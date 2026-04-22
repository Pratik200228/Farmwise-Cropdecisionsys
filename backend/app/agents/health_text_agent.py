"""
Crop Health (text-only) agent.

This module intentionally avoids importing TensorFlow / PIL / numpy so it can be
deployed in a lightweight "core API" environment (e.g. Vercel).
"""

import re
import time


# Disease Knowledge Base (Fallback for text & Treatment Mappings)
HEALTH_RULES = [
    {
        "keywords": re.compile(r"yellow(ing)?|chloros|pale\s*lea", re.IGNORECASE),
        "name": "Nitrogen Deficiency",
        "kind": "nutrient",
        "severity": "watch",
        "symptoms": ["Uniform yellowing starting on older/lower leaves", "Stunted new growth"],
        "treatment": ["Side-dress with urea (46-0-0) at 30–40 kg/ha", "Apply compost tea as a foliar spray"],
        "preventive": ["Include legumes in crop rotation", "Conduct soil nitrogen test every 2 seasons"],
    },
    {
        "keywords": re.compile(r"brown\s*spot|blight|lesion|dark\s*spot|necrosi", re.IGNORECASE),
        "name": "Early Blight / Late Blight",
        "kind": "disease",
        "severity": "moderate",
        "symptoms": ["Dark brown concentric rings on leaves", "Yellow halo surrounding lesions"],
        "treatment": ["Remove and destroy all infected lower leaves", "Apply copper-based fungicide at label rate"],
        "preventive": ["Mulch soil surface to prevent rain splash", "Water at soil level — avoid wetting foliage"],
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
        "preventive": [
            "Ensure adequate soil moisture during early tuber/fruit formation",
            "Apply compost to increase beneficial microbes",
        ],
    },
    {
        "keywords": re.compile(r"mosaic", re.IGNORECASE),
        "name": "Mosaic Virus",
        "kind": "disease",
        "severity": "severe",
        "symptoms": ["Mottled green/yellow leaves", "Curling or crinkling of leaves"],
        "treatment": ["No cure; remove and destroy infected plants immediately", "Control aphids/whiteflies that spread the virus"],
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


def _severity_to_score(severity: str) -> int:
    return {"healthy": 90, "watch": 72, "moderate": 55, "severe": 35}.get(severity, 70)


def generate_health_report(crop: str, growth_stage: str, symptoms_note: str) -> dict:
    """Text-based diagnosis logic (no ML)."""
    note = (symptoms_note or "").strip()
    matched = []
    seen_names = set()
    for rule in HEALTH_RULES:
        if rule["keywords"].search(note):
            name = rule["name"]
            if name not in seen_names:
                seen_names.add(name)
                prob_map = {"watch": 0.65, "moderate": 0.75, "severe": 0.85, "healthy": 0.9}
                matched.append(
                    {
                        "name": name,
                        "kind": rule["kind"],
                        "severity": rule["severity"],
                        "probability": prob_map.get(rule["severity"], 0.7),
                        "symptoms": rule["symptoms"],
                        "treatment": rule["treatment"],
                        "preventive": rule["preventive"],
                    }
                )

    final_issues = matched if matched else [HEALTHY_RESPONSE]
    overall = "healthy"
    for s in ["severe", "moderate", "watch", "healthy"]:
        if any(i["severity"] == s for i in final_issues):
            overall = s
            break

    health_score = _severity_to_score(overall)
    if len(matched) > 1:
        health_score = max(30, health_score - (len(matched) - 1) * 8)

    scouting_plan = [f"Walk {crop} rows every 3 days; photograph both leaf surfaces.", "Focus on border rows and humid spots."]
    if growth_stage in ("flowering", "fruiting", "grain fill"):
        scouting_plan.append("Peak-risk stage — increase scouting to every 2 days.")

    return {
        "crop": crop,
        "growthStage": growth_stage,
        "healthScore": health_score,
        "overallSeverity": overall,
        "issues": final_issues,
        "scoutingPlan": scouting_plan,
        "source": "Rule-based expert system (Text)",
        "generatedAt": int(time.time() * 1000),
    }

