"""
Crop Health Monitoring Agent.

Image classification uses a known-good public PlantVillage MobileNetV2
checkpoint (Daksh159/plant-disease-mobilenetv2 on Hugging Face), trained
on the New Plant Diseases Dataset (Augmented) - 38 classes, 95% val acc.
Text-symptom diagnosis uses a curated rule-based expert system.
"""

import io
import logging
import os
import re
import time
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


_TORCH_OK = True
try:
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    # Limit to 1 CPU thread — reduces per-thread memory buffers significantly.
    # On Render free tier (512MB RAM) multi-threading causes OOM crashes.
    torch.set_num_threads(1)
except Exception as exc:
    logger.warning("PyTorch unavailable, image scan disabled: %s", exc)
    _TORCH_OK = False


MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
TORCH_MODEL_PATH = os.path.join(MODEL_DIR, "mobilenetv2_plant.pth")
CLASSES_PATH = os.path.join(MODEL_DIR, "disease_class_names.pkl")
CEREAL_VIT_DIR = os.path.join(MODEL_DIR, "crop_leaf_vit")

HF_PLANT_REPO = os.getenv("HF_PLANT_REPO", "Daksh159/plant-disease-mobilenetv2").strip()
HF_PLANT_FILENAME = os.getenv("HF_PLANT_FILENAME", "mobilenetv2_plant.pth").strip()


def _load_class_names() -> List[str]:
    try:
        import joblib
        if os.path.exists(CLASSES_PATH):
            classes = joblib.load(CLASSES_PATH)
            if isinstance(classes, (list, tuple)) and len(classes) == 38:
                return list(classes)
    except Exception as exc:
        logger.warning("Failed to load class names pkl: %s", exc)
    # Standard alphabetical PlantVillage 38-class order
    return [
        "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust", "Apple___healthy",
        "Blueberry___healthy",
        "Cherry_(including_sour)___Powdery_mildew", "Cherry_(including_sour)___healthy",
        "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
        "Corn_(maize)___Common_rust_", "Corn_(maize)___Northern_Leaf_Blight", "Corn_(maize)___healthy",
        "Grape___Black_rot", "Grape___Esca_(Black_Measles)",
        "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape___healthy",
        "Orange___Haunglongbing_(Citrus_greening)",
        "Peach___Bacterial_spot", "Peach___healthy",
        "Pepper,_bell___Bacterial_spot", "Pepper,_bell___healthy",
        "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
        "Raspberry___healthy", "Soybean___healthy",
        "Squash___Powdery_mildew",
        "Strawberry___Leaf_scorch", "Strawberry___healthy",
        "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight",
        "Tomato___Leaf_Mold", "Tomato___Septoria_leaf_spot",
        "Tomato___Spider_mites Two-spotted_spider_mite",
        "Tomato___Target_Spot", "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
        "Tomato___Tomato_mosaic_virus", "Tomato___healthy",
    ]


CLASS_NAMES: List[str] = _load_class_names()


# --- Crop coverage gate -----------------------------------------------------
# These are the crops the public PlantVillage MobileNetV2 model can actually
# diagnose diseases for. If a farmer picks anything outside this set, image
# scan is gated off and we ask them to use the text path or contact an expert.

DISEASE_CAPABLE_CROPS = {
    "apple", "cherry", "corn", "grape", "orange",
    "peach", "pepper", "potato", "squash", "strawberry", "tomato",
}

# Crops served by the secondary cereal ViT (Layer 2):
# wambugu71/crop_leaf_diseases_vit covers rice + wheat (and also corn/potato,
# but PlantVillage handles those better, so we only route rice/wheat here).
CEREAL_VIT_CROPS = {"rice", "wheat"}

# Model has only "healthy" class for these - it can confirm a healthy leaf
# but cannot reliably detect any disease. Treat as gated for image scan.
HEALTH_ONLY_CROPS = {"blueberry", "raspberry", "soybean"}

# Common aliases / vernacular names farmers may pick from the UI.
CROP_ALIASES = {
    "maize": "corn",
    "bell pepper": "pepper",
    "bell_pepper": "pepper",
    "capsicum": "pepper",
    "chilli": "pepper",
    "chili": "pepper",
    "paddy": "rice",
    "brinjal": "eggplant",
}


def _normalize_crop(crop: Optional[str]) -> str:
    if not crop:
        return ""
    key = crop.strip().lower().replace("(", "").replace(")", "").strip()
    return CROP_ALIASES.get(key, key)


def _build_unsupported_response(crop_label: str, stage_hint: Optional[str], reason: str) -> dict:
    return {
        "crop": crop_label,
        "growthStage": stage_hint or "Observed via image scan",
        "healthScore": 70,
        "overallSeverity": "watch",
        "issues": [{
            "name": f"Image scan not available for {crop_label}",
            "kind": "disease",
            "severity": "watch",
            "probability": 0.0,
            "symptoms": [
                reason,
                "Running the model anyway would force a wrong label from a different crop family.",
            ],
            "treatment": [
                f"Switch to the text-symptom flow and describe what you see on your {crop_label}.",
                "Capture clear photos of affected and healthy leaves for an agronomist visit.",
            ],
            "preventive": [
                "Consult a local extension officer or plant pathologist for confirmation.",
                "Track symptom spread daily until you get expert diagnosis.",
            ],
        }],
        "scoutingPlan": [
            f"Image-based diagnosis for {crop_label} is not supported by the current model.",
            "Use the text-symptom path, or contact a local agronomist within 24-48 hours.",
        ],
        "source": "Crop-coverage gate (model not trained on this crop)",
        "generatedAt": int(time.time() * 1000),
    }


_MODEL = None
_TRANSFORM = None
_CEREAL_MODEL = None
_CEREAL_PROCESSOR = None
_CEREAL_ID2LABEL: dict = {}

_MODEL_DOWNLOAD_ATTEMPTED = False


def _ensure_plant_weights_present() -> bool:
    """Ensure MobileNetV2 weights exist locally; download if missing."""
    global _MODEL_DOWNLOAD_ATTEMPTED
    if os.path.exists(TORCH_MODEL_PATH):
        return True
    if _MODEL_DOWNLOAD_ATTEMPTED:
        return False
    _MODEL_DOWNLOAD_ATTEMPTED = True

    try:
        os.makedirs(MODEL_DIR, exist_ok=True)
        from huggingface_hub import hf_hub_download

        logger.info(
            "Plant weights missing; downloading from Hugging Face repo=%s file=%s",
            HF_PLANT_REPO,
            HF_PLANT_FILENAME,
        )
        downloaded = hf_hub_download(
            repo_id=HF_PLANT_REPO,
            filename=HF_PLANT_FILENAME,
            local_dir=MODEL_DIR,
            local_dir_use_symlinks=False,
        )

        # Ensure the expected filename exists for torch.load
        if os.path.abspath(downloaded) != os.path.abspath(TORCH_MODEL_PATH):
            try:
                if os.path.exists(TORCH_MODEL_PATH):
                    os.remove(TORCH_MODEL_PATH)
                os.replace(downloaded, TORCH_MODEL_PATH)
            except Exception:
                pass

        return os.path.exists(TORCH_MODEL_PATH)
    except Exception as exc:
        logger.exception("Failed downloading plant model weights: %s", exc)
        return False


def _build_cereal_model():
    """Lazy-load the rice/wheat ViT (Layer 2 specialist)."""
    global _CEREAL_MODEL, _CEREAL_PROCESSOR, _CEREAL_ID2LABEL
    if _CEREAL_MODEL is not None:
        return _CEREAL_MODEL
    if not _TORCH_OK:
        return None
    if not os.path.isdir(CEREAL_VIT_DIR):
        logger.warning("Cereal ViT directory not found at %s", CEREAL_VIT_DIR)
        return None
    try:
        from transformers import AutoImageProcessor, AutoModelForImageClassification
        proc = AutoImageProcessor.from_pretrained(CEREAL_VIT_DIR)
        net = AutoModelForImageClassification.from_pretrained(CEREAL_VIT_DIR)
        net.eval()
        _CEREAL_MODEL = net
        _CEREAL_PROCESSOR = proc
        _CEREAL_ID2LABEL = {int(k): v for k, v in net.config.id2label.items()}
        logger.info(
            "Loaded cereal ViT (rice/wheat specialist) - %d classes", len(_CEREAL_ID2LABEL)
        )
        return _CEREAL_MODEL
    except Exception as exc:
        logger.exception("Failed to load cereal ViT: %s", exc)
        return None


def _build_model():
    global _MODEL, _TRANSFORM
    if not _TORCH_OK:
        return None
    if _MODEL is not None:
        return _MODEL
    if not _ensure_plant_weights_present():
        logger.warning(
            "MobileNetV2 plant model not available at %s (HF_PLANT_REPO=%s HF_PLANT_FILENAME=%s)",
            TORCH_MODEL_PATH,
            HF_PLANT_REPO,
            HF_PLANT_FILENAME,
        )
        return None
    try:
        net = models.mobilenet_v2(weights=None)
        in_features = net.classifier[1].in_features
        net.classifier[1] = nn.Sequential(
            nn.Dropout(0.2),
            nn.Linear(in_features, len(CLASS_NAMES)),
        )
        state = torch.load(TORCH_MODEL_PATH, map_location="cpu")
        net.load_state_dict(state)
        net.eval()
        _MODEL = net
        _TRANSFORM = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        logger.info("Loaded plant disease MobileNetV2 (%d classes)", len(CLASS_NAMES))
        return _MODEL
    except Exception as exc:
        logger.exception("Failed to load MobileNetV2 plant model: %s", exc)
        return None


HEALTH_RULES = [
    {
        "keywords": re.compile(r"yellow(ing)?|chloros|pale\s*lea", re.IGNORECASE),
        "name": "Nitrogen Deficiency",
        "kind": "nutrient",
        "severity": "watch",
        "symptoms": ["Uniform yellowing starting on older/lower leaves", "Stunted new growth"],
        "treatment": ["Side-dress with urea (46-0-0) at 30-40 kg/ha", "Apply compost tea as a foliar spray"],
        "preventive": ["Include legumes in crop rotation", "Conduct soil nitrogen test every 2 seasons"],
    },
    {
        "keywords": re.compile(r"brown\s*spot|blight|lesion|dark\s*spot|necrosi", re.IGNORECASE),
        "name": "Early Blight / Late Blight",
        "kind": "disease",
        "severity": "moderate",
        "symptoms": ["Dark brown concentric rings on leaves", "Yellow halo surrounding lesions"],
        "treatment": ["Remove and destroy all infected lower leaves", "Apply copper-based fungicide at label rate"],
        "preventive": ["Mulch soil surface to prevent rain splash", "Water at soil level - avoid wetting foliage"],
    },
    {
        "keywords": re.compile(r"pwdery|mildew|white\s*film|dusty\s*lea", re.IGNORECASE),
        "name": "Powdery Mildew",
        "kind": "disease",
        "severity": "moderate",
        "symptoms": ["White powdery coating on upper leaf surfaces", "Leaf curling"],
        "treatment": ["Apply sulfur dust or wettable sulfur", "Potassium bicarbonate spray"],
        "preventive": ["Water at the base of the plant", "Space plants adequately for ventilation"],
    },
    {
        "keywords": re.compile(r"rust|common\s*rust", re.IGNORECASE),
        "name": "Common Rust / Cedar Apple Rust",
        "kind": "disease",
        "severity": "moderate",
        "symptoms": ["Orange, reddish-brown pustules on leaves", "Yellowing around pustules"],
        "treatment": ["Apply triazole-based fungicide at first sign", "Remove heavily infected leaves"],
        "preventive": ["Use rust-resistant crop varieties", "Destroy crop debris after harvest"],
    },
    {
        "keywords": re.compile(r"bacc?terial\s*spot", re.IGNORECASE),
        "name": "Bacterial Spot",
        "kind": "disease",
        "severity": "severe",
        "symptoms": ["Small, water-soaked, greasy-looking spots", "Lesions turning brown/black"],
        "treatment": ["Apply copper bactericide mixed with mancozeb", "Prune infected branches immediately"],
        "preventive": ["Use certified disease-free seeds", "Avoid working in fields when foliage is wet"],
    },
    {
        "keywords": re.compile(r"scab", re.IGNORECASE),
        "name": "Common Scab",
        "kind": "disease",
        "severity": "moderate",
        "symptoms": ["Rough, corky spots on fruit/tubers", "Olive-green spots on leaves"],
        "treatment": ["Apply captan or myclobutanil fungicide", "Adjust soil pH to be less favorable for scab"],
        "preventive": ["Ensure adequate soil moisture during early tuber/fruit formation", "Apply compost"],
    },
    {
        "keywords": re.compile(r"mosaic", re.IGNORECASE),
        "name": "Mosaic Virus",
        "kind": "disease",
        "severity": "severe",
        "symptoms": ["Mottled green/yellow leaves", "Curling or crinkling of leaves"],
        "treatment": ["No cure; remove and destroy infected plants immediately", "Control aphids/whiteflies"],
        "preventive": ["Use resistant varieties", "Sanitize tools with rubbing alcohol between plants"],
    },
]

HEALTHY_RESPONSE = {
    "name": "Healthy",
    "kind": "disease",
    "severity": "healthy",
    "probability": 1.0,
    "symptoms": ["Canopy color uniform", "No visible lesions or pests"],
    "treatment": ["Continue weekly scouting"],
    "preventive": ["Maintain current watering and nutrient schedules", "Log photos weekly for trend tracking"],
}


def _severity_from_label(label: str) -> str:
    lower = label.lower()
    if "healthy" in lower:
        return "healthy"
    if any(k in lower for k in ["mosaic", "bacterial", "huanglongbing", "haunglongbing", "citrus_greening", "late_blight"]):
        return "severe"
    if any(k in lower for k in ["scab", "rust", "blight", "rot", "spot", "mildew", "leaf_mold", "scorch", "esca", "spider_mites", "target_spot", "yellow_leaf_curl"]):
        return "moderate"
    return "watch"


def _severity_to_score(severity: str) -> int:
    return {"healthy": 90, "watch": 72, "moderate": 55, "severe": 35}.get(severity, 70)


def _humanize(label: str) -> Tuple[str, str]:
    if "___" in label:
        crop_part, disease_part = label.split("___", 1)
    else:
        crop_part, disease_part = "Unknown", label
    crop = crop_part.replace("_", " ").replace("(", "(").strip()
    disease = disease_part.replace("_", " ").strip().rstrip("_").strip()
    return crop, disease or "Healthy"


def _treatment_for(label: str) -> dict:
    _, disease = _humanize(label)
    for rule in HEALTH_RULES:
        if rule["keywords"].search(disease):
            return {
                "name": disease.title(),
                "kind": rule["kind"],
                "treatment": rule["treatment"],
                "preventive": rule["preventive"],
            }
    return {
        "name": disease.title(),
        "kind": "disease",
        "treatment": [
            "Isolate affected plants and remove diseased tissue.",
            "Improve airflow and avoid overhead watering.",
            "Confirm with a local agronomist before targeted chemical control.",
        ],
        "preventive": ["Rotate crops next cycle", "Use certified disease-free seed/seedlings"],
    }


def _analyze_with_cereal_vit(
    image_bytes: bytes,
    crop_label: str,
    crop_norm: str,
    stage_hint: Optional[str],
) -> dict:
    """Layer 2 path: rice / wheat specialist (ViT).

    The ViT predicts crop+disease jointly across {corn, potato, rice, wheat}.
    We filter probabilities down to just the user-selected crop's classes so
    the answer is always coherent with the dropdown selection.
    """
    net = _build_cereal_model()
    if net is None or _CEREAL_PROCESSOR is None:
        return {"error": "Cereal disease model not loaded on backend."}
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = _CEREAL_PROCESSOR(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = net(**inputs)
            full_probs = torch.softmax(outputs.logits, dim=1)[0].cpu().numpy()
    except Exception as exc:
        return {"error": f"Failed to process image: {exc}"}

    crop_prefix = crop_norm.capitalize() + "___"  # e.g. "Rice___"
    crop_indices = [
        i for i, lbl in _CEREAL_ID2LABEL.items() if lbl.startswith(crop_prefix)
    ]
    invalid_idx = next(
        (i for i, lbl in _CEREAL_ID2LABEL.items() if lbl == "Invalid"), None
    )

    invalid_prob = float(full_probs[invalid_idx]) if invalid_idx is not None else 0.0
    crop_total = float(sum(full_probs[i] for i in crop_indices)) if crop_indices else 0.0
    other_crop_total = float(1.0 - crop_total - invalid_prob)

    if invalid_prob > 0.6 or (crop_total < 0.20 and invalid_prob > 0.3):
        return {
            "crop": crop_label,
            "growthStage": stage_hint or "Observed via image scan",
            "healthScore": 60,
            "overallSeverity": "watch",
            "issues": [{
                "name": "Image not recognized as a crop leaf",
                "kind": "disease",
                "severity": "watch",
                "probability": invalid_prob,
                "symptoms": [
                    "The model classified this image as not a crop leaf.",
                    "Common causes: blurry photo, soil/equipment in frame, wrong subject.",
                ],
                "treatment": [
                    "Recapture a close-up of one affected leaf in good daylight.",
                    "Hold the camera ~15-20 cm from the leaf, fill the frame.",
                ],
                "preventive": [
                    "Take 2-3 photos of different affected leaves for cross-check.",
                ],
            }],
            "scoutingPlan": [
                f"Re-photograph {crop_label} leaves and rerun the scan.",
            ],
            "modelConfidence": round(invalid_prob, 3),
            "topPredictions": [
                {"label": "Not a leaf", "probability": round(invalid_prob, 3)},
            ],
            "source": "Cereal ViT (rice/wheat specialist) - non-leaf detected",
            "generatedAt": int(time.time() * 1000),
        }

    if other_crop_total > 0.5 and crop_total < 0.3:
        return {
            "crop": crop_label,
            "growthStage": stage_hint or "Observed via image scan",
            "healthScore": 65,
            "overallSeverity": "watch",
            "issues": [{
                "name": f"Photo doesn't appear to be a {crop_label} leaf",
                "kind": "disease",
                "severity": "watch",
                "probability": other_crop_total,
                "symptoms": [
                    f"Visual signal is more consistent with another crop than {crop_label}.",
                    "Confirm you've selected the correct crop in the dropdown.",
                ],
                "treatment": [
                    "Switch the crop selector to match the actual leaf photographed.",
                    "Or recapture a clearer leaf image of the intended crop.",
                ],
                "preventive": [
                    "Always frame a single representative leaf per scan.",
                ],
            }],
            "scoutingPlan": [
                f"Re-confirm crop selection vs. photographed leaf.",
            ],
            "modelConfidence": round(other_crop_total, 3),
            "topPredictions": [
                {
                    "label": _humanize(_CEREAL_ID2LABEL[i])[1] + f" ({_CEREAL_ID2LABEL[i].split('___')[0]})",
                    "probability": round(float(full_probs[i]), 3),
                }
                for i in np.argsort(full_probs)[-3:][::-1]
            ],
            "source": "Cereal ViT (rice/wheat specialist) - crop mismatch",
            "generatedAt": int(time.time() * 1000),
        }

    if not crop_indices:
        return {"error": f"No {crop_label} classes registered in cereal model."}

    crop_probs = full_probs[crop_indices]
    crop_probs = crop_probs / crop_probs.sum() if crop_probs.sum() > 0 else crop_probs
    sorted_local = np.argsort(crop_probs)[::-1]
    top_k = [
        (_CEREAL_ID2LABEL[crop_indices[int(i)]], float(crop_probs[int(i)]))
        for i in sorted_local[:3]
    ]
    top_label, top_conf = top_k[0]
    second_conf = float(top_k[1][1]) if len(top_k) > 1 else 0.0
    margin = top_conf - second_conf

    if top_conf < 0.50 or margin < 0.10:
        labels_pretty = ", ".join(
            f"{_humanize(name)[1]} ({int(prob * 100)}%)" for name, prob in top_k
        )
        return {
            "crop": crop_label,
            "growthStage": stage_hint or "Observed via image scan",
            "healthScore": 65,
            "overallSeverity": "watch",
            "issues": [{
                "name": "Uncertain diagnosis",
                "kind": "disease",
                "severity": "watch",
                "probability": top_conf,
                "symptoms": [
                    "Model confidence is low for a single class.",
                    f"Top candidates: {labels_pretty}",
                ],
                "treatment": [
                    "Re-photograph in good daylight with leaf filling the frame.",
                    "Capture both upper and lower leaf surfaces.",
                ],
                "preventive": [
                    "Continue scouting every 48 hours.",
                    "Contact a local plant expert if symptoms spread quickly.",
                ],
            }],
            "scoutingPlan": [
                f"Recapture clearer images for {crop_label} within 24 hours.",
            ],
            "modelConfidence": round(top_conf, 3),
            "topPredictions": [
                {"label": _humanize(name)[1], "probability": round(prob, 3)} for name, prob in top_k
            ],
            "source": "Cereal ViT (rice/wheat specialist) - low-confidence fallback",
            "generatedAt": int(time.time() * 1000),
        }

    _, predicted_disease = _humanize(top_label)

    if "healthy" in top_label.lower():
        return {
            "crop": crop_label,
            "growthStage": stage_hint or "Observed via image scan",
            "healthScore": 95,
            "overallSeverity": "healthy",
            "issues": [{**HEALTHY_RESPONSE, "probability": top_conf}],
            "scoutingPlan": [
                f"Continue weekly scouting of {crop_label}.",
                "Photograph canopy regularly for trend tracking.",
            ],
            "modelConfidence": round(top_conf, 3),
            "topPredictions": [
                {"label": _humanize(name)[1], "probability": round(prob, 3)} for name, prob in top_k
            ],
            "source": "Cereal ViT (rice/wheat specialist)",
            "generatedAt": int(time.time() * 1000),
        }

    severity = _severity_from_label(top_label)
    treatment_info = _treatment_for(top_label)
    health_score = _severity_to_score(severity)
    scouting_plan = [
        f"Isolate spread of {predicted_disease.lower()} in {crop_label} and prune affected tillers/leaves.",
        "Re-scan every 3 days; track spread across rows.",
    ]
    if severity == "severe":
        scouting_plan.append(
            "High-severity risk detected: contact a local agronomist or plant pathologist within 24-48 hours."
        )

    return {
        "crop": crop_label,
        "growthStage": stage_hint or "Observed via image scan",
        "healthScore": health_score,
        "overallSeverity": severity,
        "issues": [{
            "name": predicted_disease.title(),
            "kind": treatment_info["kind"],
            "severity": severity,
            "probability": top_conf,
            "symptoms": [f"Visual indicators most closely match {predicted_disease.lower()}"],
            "treatment": treatment_info["treatment"],
            "preventive": treatment_info["preventive"],
        }],
        "scoutingPlan": scouting_plan,
        "modelConfidence": round(top_conf, 3),
        "topPredictions": [
            {"label": _humanize(name)[1], "probability": round(prob, 3)} for name, prob in top_k
        ],
        "source": "Cereal ViT (rice/wheat specialist)",
        "generatedAt": int(time.time() * 1000),
    }


def analyze_plant_image(image_bytes: bytes, crop_hint: Optional[str] = None, stage_hint: Optional[str] = None) -> dict:
    """Route the image to the right specialist model based on the crop hint."""
    crop_norm = _normalize_crop(crop_hint)
    crop_label = (crop_hint or crop_norm or "this crop").strip()

    if crop_norm in CEREAL_VIT_CROPS:
        return _analyze_with_cereal_vit(image_bytes, crop_label, crop_norm, stage_hint)

    if crop_norm:
        if crop_norm not in DISEASE_CAPABLE_CROPS:
            if crop_norm in HEALTH_ONLY_CROPS:
                reason = (
                    f"The plant disease model only knows healthy {crop_label} - "
                    "it cannot reliably detect diseases for this crop yet."
                )
            else:
                reason = (
                    f"This model was not trained on {crop_label}. "
                    "Supported crops: Apple, Cherry, Corn, Grape, Orange, Peach, Pepper, Potato, "
                    "Squash, Strawberry, Tomato (PlantVillage); Rice, Wheat (cereal specialist)."
                )
            return _build_unsupported_response(crop_label, stage_hint, reason)

    net = _build_model()
    if net is None:
        return {"error": "Plant disease model not loaded on backend."}
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        with torch.no_grad():
            tensor = _TRANSFORM(image).unsqueeze(0)
            logits = net(tensor)
            probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
    except Exception as exc:
        return {"error": f"Failed to process image: {exc}"}

    top_k_idx = np.argsort(probs)[-3:][::-1]
    top_k = [(CLASS_NAMES[i], float(probs[i])) for i in top_k_idx]
    top_label, top_conf = top_k[0]
    top_label_lower = top_label.lower()
    second_conf = float(top_k[1][1]) if len(top_k) > 1 else 0.0
    margin = top_conf - second_conf
    predicted_crop, predicted_disease = _humanize(top_label)

    # Use the model's predicted crop name — don't override with crop_hint.
    # crop_hint is used only for routing (cereal ViT vs MobileNetV2),
    # not for labelling the result. This way the result always reflects
    # what the model actually saw, regardless of what the UI dropdown says.

    if top_conf < 0.55 or margin < 0.10:
        labels_pretty = ", ".join(
            f"{_humanize(name)[1]} ({int(prob * 100)}%)" for name, prob in top_k
        )
        crop = predicted_crop.strip() or crop_hint or "Unknown"
        return {
            "crop": crop,
            "growthStage": stage_hint or "Observed via image scan",
            "healthScore": 65,
            "overallSeverity": "watch",
            "issues": [{
                "name": "Uncertain diagnosis",
                "kind": "disease",
                "severity": "watch",
                "probability": top_conf,
                "symptoms": [
                    "Model confidence is low for a single class.",
                    f"Top candidates: {labels_pretty}",
                ],
                "treatment": [
                    "Re-photograph in good daylight with leaf filling the frame.",
                    "Capture both upper and lower leaf surfaces.",
                    "Avoid blanket spraying until diagnosis is confirmed.",
                ],
                "preventive": [
                    "Continue scouting every 48 hours.",
                    "Contact a local plant expert if symptoms spread quickly.",
                ],
            }],
            "scoutingPlan": [
                f"Recapture clearer images for {crop} within 24 hours.",
                "Track whether spots/lesions are spreading.",
                "Contact a local agronomist if condition worsens before re-scan.",
            ],
            "modelConfidence": round(top_conf, 3),
            "topPredictions": [
                {"label": _humanize(name)[1], "probability": round(prob, 3)} for name, prob in top_k
            ],
            "source": "PyTorch MobileNetV2 (PlantVillage) - low-confidence fallback",
            "generatedAt": int(time.time() * 1000),
        }

    crop = predicted_crop.strip() or crop_hint or "Unknown"

    if "healthy" in top_label_lower:
        return {
            "crop": crop,
            "growthStage": stage_hint or "Observed via image scan",
            "healthScore": 95,
            "overallSeverity": "healthy",
            "issues": [{**HEALTHY_RESPONSE, "probability": top_conf}],
            "scoutingPlan": [
                f"Continue weekly visual scouting of {crop}.",
                "Photograph canopy regularly for trend tracking.",
            ],
            "modelConfidence": round(top_conf, 3),
            "topPredictions": [
                {"label": _humanize(name)[1], "probability": round(prob, 3)} for name, prob in top_k
            ],
            "source": "PyTorch MobileNetV2 (PlantVillage)",
            "generatedAt": int(time.time() * 1000),
        }

    severity = _severity_from_label(top_label)
    treatment_info = _treatment_for(top_label)

    response_issue = {
        "name": predicted_disease.title(),
        "kind": treatment_info["kind"],
        "severity": severity,
        "probability": top_conf,
        "symptoms": [f"Visual indicators most closely match {predicted_disease.lower()}"],
        "treatment": treatment_info["treatment"],
        "preventive": treatment_info["preventive"],
    }

    health_score = _severity_to_score(severity)

    scouting_plan = [
        f"Isolate spread of {predicted_disease.lower()} and prune affected leaves.",
        "Re-scan leaves every 3 days; track spread across rows.",
    ]
    if severity == "severe":
        scouting_plan.append(
            "High-severity risk detected: contact a local agronomist or plant pathologist within 24-48 hours."
        )

    return {
        "crop": crop,
        "growthStage": stage_hint or "Observed via image scan",
        "healthScore": health_score,
        "overallSeverity": severity,
        "issues": [response_issue],
        "scoutingPlan": scouting_plan,
        "modelConfidence": round(top_conf, 3),
        "topPredictions": [
            {"label": _humanize(name)[1], "probability": round(prob, 3)} for name, prob in top_k
        ],
        "source": "PyTorch MobileNetV2 (PlantVillage)",
        "generatedAt": int(time.time() * 1000),
    }


def generate_health_report(crop: str, growth_stage: str, symptoms_note: str) -> dict:
    """Text-based diagnosis (used when no image uploaded)."""
    note = symptoms_note.strip()
    matched = []
    seen_names = set()
    for rule in HEALTH_RULES:
        if rule["keywords"].search(note):
            name = rule["name"]
            if name not in seen_names:
                seen_names.add(name)
                prob_map = {"watch": 0.65, "moderate": 0.75, "severe": 0.85, "healthy": 0.9}
                matched.append({
                    "name": name,
                    "kind": rule["kind"],
                    "severity": rule["severity"],
                    "probability": prob_map.get(rule["severity"], 0.7),
                    "symptoms": rule["symptoms"],
                    "treatment": rule["treatment"],
                    "preventive": rule["preventive"],
                })

    final_issues = matched if matched else [HEALTHY_RESPONSE]
    overall = "healthy"
    for s in ["severe", "moderate", "watch", "healthy"]:
        if any(i["severity"] == s for i in final_issues):
            overall = s
            break

    health_score = _severity_to_score(overall)
    if len(matched) > 1:
        health_score = max(30, health_score - (len(matched) - 1) * 8)

    scouting_plan = [
        f"Walk {crop} rows every 3 days; photograph both leaf surfaces.",
        "Focus on border rows and humid spots.",
    ]
    if growth_stage in ("flowering", "fruiting", "grain fill"):
        scouting_plan.append("Peak-risk stage - increase scouting to every 2 days.")
    if overall == "severe":
        scouting_plan.append(
            "High-severity risk detected: contact a local agronomist or plant pathologist immediately."
        )

    return {
        "crop": crop,
        "growthStage": growth_stage,
        "healthScore": health_score,
        "overallSeverity": overall,
        "issues": final_issues,
        "scoutingPlan": scouting_plan,
        "source": "Rule-based expert system (text fallback)",
        "generatedAt": int(time.time() * 1000),
    }
