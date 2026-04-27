# Layer 3 — Unified Plant Disease Fine-Tune

Goal: replace the multi-model router (PlantVillage MobileNetV2 + Cereal ViT
+ crop gate) with a single MobileNetV2 fine-tuned on a unified label space
that covers every crop your farmers care about — including Rice, Wheat,
Lentil, Mustard, etc.

This document explains how to run the training script and swap the result
into the backend.

---

## 1. Pre-requisites

- A working Python 3.12 venv with `torch`, `torchvision`, and
  `huggingface_hub` already installed (the FarmWise backend venv works).
- Install the extra training-only deps:

```bash
cd backend
.\.venv\Scripts\python.exe -m pip install datasets pillow tqdm
```

- Recommended: a CUDA GPU. CPU training works but is **very slow**
  (~2-4 hours per epoch on the full PlantVillage dataset).

---

## 2. Pick your datasets

The script accepts a comma-separated list of either Hugging Face dataset
IDs **or** local ImageFolder paths. Some good starting points:

| Source | Dataset spec | Crops covered | Size |
|---|---|---|---|
| Hugging Face | `mohanty/PlantVillage` | 14 crops, 38 classes (lab) | ~54k images |
| Hugging Face | `wambugu71/CropDiseaseDetection` | corn/potato/rice/wheat | ~10k images |
| Local folder | `data/plantdoc/` | 13 crops in real fields | ~2.6k images |
| Local folder | `data/mustard_disease/` | mustard (your own collected images) | varies |

You can mix-and-match. Classes with the same name across datasets are
merged automatically; new classes get appended.

To use PlantDoc, download
[pratikkayal/PlantDoc-Dataset](https://github.com/pratikkayal/PlantDoc-Dataset)
and re-organize it as `data/plantdoc/<class_name>/*.jpg`.

---

## 3. Run training

From inside `backend/`:

```bash
# Quick smoke test on PlantVillage only (CPU friendly: 1 epoch ~ 2-4h)
.\.venv\Scripts\python.exe scripts\train_unified_disease_model.py \
    --datasets mohanty/PlantVillage \
    --epochs 1 --freeze-features

# Full run on multiple sources (GPU recommended)
.\.venv\Scripts\python.exe scripts\train_unified_disease_model.py \
    --datasets mohanty/PlantVillage,wambugu71/CropDiseaseDetection,data/plantdoc \
    --epochs 12 --batch-size 64
```

Outputs:

- `app/models/unified_plant_disease.pth` — best-validation MobileNetV2 weights
- `app/models/unified_class_names.json` — ordered list of class labels

The script prints per-epoch train/val loss and accuracy and only saves
checkpoints when validation accuracy improves.

---

## 4. Swap the model into the backend

Once `unified_plant_disease.pth` is ready, update
`backend/app/agents/health_agent.py` so the router loads it as the primary
model:

1. Add a new constant near the top:

```python
UNIFIED_MODEL_PATH = os.path.join(MODEL_DIR, "unified_plant_disease.pth")
UNIFIED_CLASSES_PATH = os.path.join(MODEL_DIR, "unified_class_names.json")
```

2. Build a loader that reads the JSON class list and constructs a
   MobileNetV2 with `len(classes)` outputs (mirror `_build_model`).

3. In `analyze_plant_image`, prefer the unified model when it's present;
   fall back to the existing PlantVillage MobileNetV2 / cereal ViT chain
   if it isn't. That way you can A/B for a few days before retiring the
   specialists.

4. Once the unified model is verified end-to-end, the cereal ViT path and
   crop-coverage gate can be removed (or kept as belts-and-braces).

---

## 5. What "good" looks like

After ~10 epochs on PlantVillage + a small rice/wheat/mustard set, expect:

- Validation accuracy 92-96% on PlantVillage (lab images)
- 60-80% on PlantDoc (real-field images) — this is the harder benchmark
- Crop-level coverage matches the union of all training datasets, so the
  UI dropdown can show whatever crops you trained on.

Track:
- Per-class precision/recall — flag classes < 80% recall for more data
- Confusion between visually similar diseases (early vs late blight, common
  rust vs northern leaf blight, etc.)
- Inference latency: keep MobileNetV2 below 50 ms / image on CPU.

---

## 6. Things to be honest about

- "Lab images" (PlantVillage) train very high accuracy on lab images and
  much lower on field photos. PlantDoc / your own field captures are what
  generalize.
- Mustard / lentil / sugarcane datasets in the public domain are small
  and noisy. Plan to collect your own labelled dataset for production.
- Always keep a held-out test set you never train on so you can detect
  regressions when you retrain.
