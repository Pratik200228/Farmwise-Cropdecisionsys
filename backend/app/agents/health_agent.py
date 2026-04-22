"""
Crop Health Monitoring Agent
Uses MobileNetV2 CNN trained on PlantVillage dataset for disease detection,
with a fallback to a rule-based expert system for text-based symptoms.
"""

import re
import time
import os
import io
import logging
from typing import List
from PIL import Image
import numpy as np

# Load ML models
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
try:
    import tensorflow as tf
    import joblib

    MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
    CNN_MODEL_PATH = os.path.join(MODEL_DIR, "plant_disease_model.h5")
    CNN_CLASSES_PATH = os.path.join(MODEL_DIR, "disease_class_names.pkl")

    if os.path.exists(CNN_MODEL_PATH) and os.path.exists(CNN_CLASSES_PATH):
        CNN_MODEL = tf.keras.models.load_model(CNN_MODEL_PATH)
        CNN_CLASSES = joblib.load(CNN_CLASSES_PATH)
    else:
        CNN_MODEL = None
        CNN_CLASSES = []
except Exception as e:
    logging.warning(f"Could not load Health CNN model: {e}")
    CNN_MODEL = None
    CNN_CLASSES = []

# Disease Knowledge Base (Fallback for text & Treatment Mappings)
HEALTH_RULES = [
    {
        "keywords": re.compile(r"yellow(ing)?|chloros|pale\s*lea", re.IGNORECASE),
        "name": "Nitrogen Deficiency",
        "kind": "nutrient",
        "severity": "watch",
        "symptoms": ["Uniform yellowing starting on older/lower leaves", "Stunted new growth"],
        "treatment": ["Side-dress with urea (46-0-0) at 30–40 kg/ha", "Apply compost tea as a foliar spray"],
        "preventive": ["Include legumes in crop rotation", "Conduct soil nitrogen test every 2 seasons"]
    },
    {
        "keywords": re.compile(r"brown\s*spot|blight|lesion|dark\s*spot|necrosi", re.IGNORECASE),
        "name": "Early Blight / Late Blight",
        "kind": "disease",
        "severity": "moderate",
        "symptoms": ["Dark brown concentric rings on leaves", "Yellow halo surrounding lesions"],
        "treatment": ["Remove and destroy all infected lower leaves", "Apply copper-based fungicide at label rate"],
        "preventive": ["Mulch soil surface to prevent rain splash", "Water at soil level — avoid wetting foliage"]
    },
    {
        "keywords": re.compile(r"pwdery|mildew|white\s*film|dusty\s*lea", re.IGNORECASE),
        "name": "Powdery Mildew",
        "kind": "disease",
        "severity": "moderate",
        "symptoms": ["White powdery coating on upper leaf surfaces", "Leaf curling"],
        "treatment": ["Apply sulfur dust or wettable sulfur", "Potassium bicarbonate spray"],
        "preventive": ["Water at the base of the plant", "Space plants adequately for ventilation"]
    },
    {
        "keywords": re.compile(r"rust|common\s*rust", re.IGNORECASE),
        "name": "Common Rust / Cedar Apple Rust",
        "kind": "disease",
        "severity": "moderate",
        "symptoms": ["Orange, reddish-brown pustules on leaves", "Yellowing around pustules"],
        "treatment": ["Apply triazole-based fungicide at first sign", "Remove heavily infected leaves"],
        "preventive": ["Use rust-resistant crop varieties", "Destroy crop debris after harvest"]
    },
    {
        "keywords": re.compile(r"bacc?terial\s*spot", re.IGNORECASE),
        "name": "Bacterial Spot",
        "kind": "disease",
        "severity": "severe",
        "symptoms": ["Small, water-soaked, greasy-looking spots", "Lesions turning brown/black"],
        "treatment": ["Apply copper bactericide mixed with mancozeb", "Prune infected branches immediately"],
        "preventive": ["Use certified disease-free seeds", "Avoid working in fields when foliage is wet"]
    },
    {
        "keywords": re.compile(r"scab", re.IGNORECASE),
        "name": "Common Scab",
        "kind": "disease",
        "severity": "moderate",
        "symptoms": ["Rough, corky spots on fruit/tubers", "Olive-green spots on leaves"],
        "treatment": ["Apply captan or myclobutanil fungicide", "Adjust soil pH to be less favorable for scab"],
        "preventive": ["Ensure adequate soil moisture during early tuber/fruit formation", "Apply compost to increase beneficial microbes"]
    },
    {
        "keywords": re.compile(r"mosaic", re.IGNORECASE),
        "name": "Mosaic Virus",
        "kind": "disease",
        "severity": "severe",
        "symptoms": ["Mottled green/yellow leaves", "Curling or crinkling of leaves"],
        "treatment": ["No cure; remove and destroy infected plants immediately", "Control aphids/whiteflies that spread the virus"],
        "preventive": ["Use resistant varieties", "Sanitize tools with rubbing alcohol between plants"]
    }
]

HEALTHY_RESPONSE = {
    "name": "Healthy",
    "kind": "disease",
    "severity": "healthy",
    "probability": 1.0,
    "symptoms": ["Canopy color uniform", "No visible lesions or pests"],
    "treatment": ["Continue weekly scouting"],
    "preventive": ["Maintain current watering and nutrient schedules", "Log photos weekly for trend tracking"]
}

def analyze_plant_image(image_bytes: bytes) -> dict:
    """Run the MobileNetV2 CNN on an uploaded leaf image."""
    if CNN_MODEL is None or not CNN_CLASSES:
        return {"error": "Machine learning model not loaded on backend."}
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize((128, 128))
        img_array = np.array(image) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        predictions = CNN_MODEL.predict(img_array, verbose=0)[0]
        max_idx = np.argmax(predictions)
        confidence = float(predictions[max_idx])
        predicted_class = CNN_CLASSES[max_idx]
        
        # Parse class: e.g. "Tomato___Early_blight" -> crop: "Tomato", issue: "Early_blight"
        parts = predicted_class.split("___")
        crop = parts[0].replace("_", " ") if len(parts) > 1 else "Unknown"
        issue_raw = parts[1] if len(parts) > 1 else predicted_class
        issue_clean = issue_raw.replace("_", " ")
        
        if issue_clean.lower() == "healthy":
            return {
                "crop": crop,
                "growthStage": "Observed via image scan",
                "healthScore": 90,
                "overallSeverity": "healthy",
                "issues": [HEALTHY_RESPONSE],
                "scoutingPlan": ["Continue weekly visual scouting.", "Photograph canopy regularly."],
                "source": "Image Diagnosis Scanner",
                "generatedAt": int(time.time() * 1000)
            }

        mapped_issue = None
        for rule in HEALTH_RULES:
            if rule["keywords"].search(issue_clean) or issue_clean.lower() in rule["name"].lower():
                mapped_issue = rule
                break
        
        if mapped_issue:
            response_issue = {
                "name": issue_clean.title(),
                "kind": mapped_issue["kind"],
                "severity": mapped_issue["severity"],
                "probability": confidence,
                "symptoms": [f"Visual evidence indicates matching characteristics of {issue_clean}"],
                "treatment": mapped_issue["treatment"],
                "preventive": mapped_issue["preventive"]
            }
        else:
            response_issue = {
                "name": issue_clean.title(),
                "kind": "disease",
                "severity": "moderate",
                "probability": confidence,
                "symptoms": [f"Visual indicators match {issue_clean}"],
                "treatment": ["Monitor spread over next 48h.", "Isolate/prune degraded leaves.", f"Consult local agronomist regarding {issue_clean}."],
                "preventive": ["Improve airflow", "Avoid overhead watering"]
            }

        overall = response_issue["severity"]
        health_score = _severity_to_score(overall)
        
        return {
            "crop": crop,
            "growthStage": "Observed via image scan",
            "healthScore": health_score,
            "overallSeverity": overall,
            "issues": [response_issue],
            "scoutingPlan": [f"Isolate spread of {issue_clean}.", "Re-scan leaves every 3 days."],
            "source": "Image Diagnosis Scanner",
            "generatedAt": int(time.time() * 1000)
        }
    except Exception as e:
        return {"error": f"Failed to process image: {str(e)}"}

def _severity_to_score(severity: str) -> int:
    return {"healthy": 90, "watch": 72, "moderate": 55, "severe": 35}.get(severity, 70)

def generate_health_report(crop: str, growth_stage: str, symptoms_note: str) -> dict:
    """Text-based diagnosis logic (fallback if no image uploaded)."""
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
        "Focus on border rows and humid spots."
    ]
    if growth_stage in ("flowering", "fruiting", "grain fill"):
        scouting_plan.append("Peak-risk stage — increase scouting to every 2 days.")

    return {
        "crop": crop,
        "growthStage": growth_stage,
        "healthScore": health_score,
        "overallSeverity": overall,
        "issues": final_issues,
        "scoutingPlan": scouting_plan,
        "source": "Rule-based expert system (Text fall-back)",
        "generatedAt": int(time.time() * 1000),
    }
