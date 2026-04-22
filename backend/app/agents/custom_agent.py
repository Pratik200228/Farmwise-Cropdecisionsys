from typing import Dict, List, Any
import os
import joblib
import logging

from app.api.schemas import FarmContext, CropSuitability, FitScores, SuitabilityResponse, SuitabilityRankedCrop

# Load ML models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
try:
    RF_MODEL = joblib.load(os.path.join(MODEL_DIR, "crop_recommendation_model.pkl"))
    LE_MODEL = joblib.load(os.path.join(MODEL_DIR, "crop_label_encoder.pkl"))
except Exception as e:
    logging.warning(f"Could not load ML models: {e}. Falling back to rule-based.")
    RF_MODEL = None
    LE_MODEL = None


# Reference catalog adapted from the original Typescript logic to ensure feature parity
CROP_CATALOG = [
    {
        "name": "Maize",
        "tempC": (18, 32),
        "humidityPct": (40, 80),
        "rainMm": (120, 400),
        "windKph": (0, 25),
        "phRange": (5.5, 7.5),
        "soilFit": {"loam": 95, "silt": 85, "clay": 70, "sandy": 60, "black": 88},
        "plantingHints": {"kharif": "Late May - Mid June", "rabi": "Late October - Mid November", "default": "At the start of the rainy season"}
    },
    {
        "name": "Rice",
        "tempC": (20, 35),
        "humidityPct": (60, 95),
        "rainMm": (200, 600),
        "windKph": (0, 20),
        "phRange": (5.0, 7.5),
        "soilFit": {"loam": 85, "silt": 80, "clay": 95, "sandy": 40, "black": 80},
        "plantingHints": {"kharif": "Mid June - Mid July", "default": "Once monsoon rains are reliable"}
    },
    {
        "name": "Wheat",
        "tempC": (10, 25),
        "humidityPct": (40, 70),
        "rainMm": (80, 250),
        "windKph": (0, 30),
        "phRange": (6.0, 7.5),
        "soilFit": {"loam": 92, "silt": 85, "clay": 80, "sandy": 55, "black": 88},
        "plantingHints": {"rabi": "Early - Mid November", "default": "Cool weather sowing window"}
    },
    {
        "name": "Lentil",
        "tempC": (15, 28),
        "humidityPct": (35, 65),
        "rainMm": (60, 180),
        "windKph": (0, 30),
        "phRange": (6.0, 7.8),
        "soilFit": {"loam": 90, "silt": 80, "clay": 60, "sandy": 70, "black": 85},
        "plantingHints": {"rabi": "October - November", "default": "After main cereal harvest"}
    },
    {
        "name": "Tomato",
        "tempC": (18, 30),
        "humidityPct": (55, 80),
        "rainMm": (100, 250),
        "windKph": (0, 20),
        "phRange": (6.0, 7.0),
        "soilFit": {"loam": 92, "silt": 85, "clay": 65, "sandy": 60, "black": 75},
        "plantingHints": {"kharif": "June - July (with drainage)", "rabi": "September - October", "default": "Transplant 4-6 wks after sowing"}
    },
    {
        "name": "Potato",
        "tempC": (12, 24),
        "humidityPct": (50, 80),
        "rainMm": (100, 300),
        "windKph": (0, 25),
        "phRange": (5.5, 6.8),
        "soilFit": {"loam": 90, "silt": 80, "clay": 60, "sandy": 80, "black": 70},
        "plantingHints": {"rabi": "Mid October - November", "default": "Cool nights with moist soil"}
    },
    {
        "name": "Mustard",
        "tempC": (10, 25),
        "humidityPct": (40, 70),
        "rainMm": (60, 200),
        "windKph": (0, 30),
        "phRange": (6.0, 7.5),
        "soilFit": {"loam": 88, "silt": 85, "clay": 78, "sandy": 65, "black": 82},
        "plantingHints": {"rabi": "October - November", "default": "After monsoon, before frost"}
    },
    {
        "name": "Soybean",
        "tempC": (20, 32),
        "humidityPct": (50, 80),
        "rainMm": (150, 400),
        "windKph": (0, 25),
        "phRange": (6.0, 7.5),
        "soilFit": {"loam": 90, "silt": 85, "clay": 72, "sandy": 65, "black": 92},
        "plantingHints": {"kharif": "Mid June - Early July", "default": "Early rainy season"}
    }
]

def clamp(n: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(n, maximum))

def range_fit(value: float, limits: tuple) -> float:
    lo, hi = limits
    if lo <= value <= hi:
        return 100.0
    span = hi - lo
    out = (lo - value) if value < lo else (value - hi)
    return clamp(100.0 - (out / max(1.0, span)) * 120.0, 0, 100)

def generate_suitability_report(context: FarmContext) -> SuitabilityResponse:
    target_soil = context.soilType.lower()
    season = context.season.lower()
    env = context.env

    # -----------------------------
    # Evaluate using Rules or ML
    # -----------------------------
    evaluated_crops = []
    
    if RF_MODEL is not None and LE_MODEL is not None:
        # Estimate N, P, K from soil type since frontend doesn't provide them
        npk_estimates = {
            "loam": (90, 42, 43),
            "silt": (70, 50, 40),
            "clay": (50, 60, 50),
            "sandy": (30, 20, 20),
            "black": (80, 60, 50)
        }
        n, p, k = npk_estimates.get(target_soil, (60, 40, 40))

        # Model expects: ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
        features = [[n, p, k, env.temperatureC, env.humidityPct, env.soilPh, env.rainfallMm]]
        try:
            probas = RF_MODEL.predict_proba(features)[0]
            ml_scores = {LE_MODEL.inverse_transform([i])[0].capitalize(): prob for i, prob in enumerate(probas)}
        except Exception:
            ml_scores = {}
    else:
        ml_scores = {}

    for profile in CROP_CATALOG:
        t_fit = range_fit(env.temperatureC, profile["tempC"])
        h_fit = range_fit(env.humidityPct, profile["humidityPct"])
        r_fit = range_fit(env.rainfallMm, profile["rainMm"])
        w_fit = range_fit(env.windKph, profile["windKph"])
        
        soil_type_fit = profile["soilFit"].get(target_soil, 60)
        ph_fit = range_fit(env.soilPh, profile["phRange"])
        s_fit = round(soil_type_fit * 0.6 + ph_fit * 0.4)

        base_score = round(t_fit * 0.28 + r_fit * 0.25 + s_fit * 0.22 + h_fit * 0.15 + w_fit * 0.1)
        confidence = clamp(0.55 + (min(t_fit, r_fit, s_fit) / 100) * 0.4 - (0.05 if env.soilMoisturePct < 20 else 0), 0.4, 0.98)

        # Apply ML Probabilities if available
        if ml_scores and profile["name"] in ml_scores:
            ml_prob = ml_scores[profile["name"]]
            # ML output strongly dictates base_score
            base_score = max(5, int(ml_prob * 100) + int(base_score * 0.2)) # Blend ML with rules fallback
            base_score = min(base_score, 100)
            confidence = max(0.6, confidence + (ml_prob * 0.2))

        warnings = []
        if t_fit < 55: warnings.append("Temperature is outside the preferred band.")
        if r_fit < 55: warnings.append("Rainfall support looks marginal - plan irrigation.")
        if h_fit < 55: warnings.append("Humidity is off - monitor transpiration stress.")
        if s_fit < 55: warnings.append("Soil type / pH fit is weak - consider amendments.")
        if w_fit < 55: warnings.append("Wind exposure is high - stake tall crops.")

        rationale_bits = [f"Temperature fit {int(t_fit)}/100, rainfall fit {int(r_fit)}/100, soil fit {int(s_fit)}/100."]
        if ml_scores:
            rationale_bits.append("ML Model prediction factored into final score.")
        if not warnings:
            rationale_bits.append("All key environmental factors sit inside the crop's comfort band.")
            
        planting_window = profile["plantingHints"].get(season, profile["plantingHints"]["default"])

        crop = CropSuitability(
            name=profile["name"],
            score=int(base_score),
            confidence=confidence,
            fit=FitScores(temperature=int(t_fit), humidity=int(h_fit), wind=int(w_fit), rainfall=int(r_fit), soil=int(s_fit)),
            rationale=" ".join(rationale_bits),
            plantingWindow=planting_window,
            warnings=warnings
        )
        evaluated_crops.append(crop)

    # Sort descending by score
    evaluated_crops.sort(key=lambda c: c.score, reverse=True)
    top_crops = evaluated_crops[:6]
    
    top = top_crops[0]
    secondary = top_crops[1]
    
    region = context.region.strip() or "your region"
    goal_label = {
        "profit": "profit / margin",
        "yield": "yield maximization",
        "sustainability": "soil health and lower inputs",
        "mixed": "balanced yield and resilience"
    }.get(context.primaryGoal, "balanced results")
    
    summary = f"For **{region}** this **{context.season}** with **{context.soilType}** soil, the best fit is **{top.name}** at **{top.score}/100**. "
    summary += f"**{secondary.name}** is a strong backup at {secondary.score}/100. "
    summary += f"Environmental read: {env.temperatureC}°C avg, {env.humidityPct}% humidity, {env.rainfallMm} mm expected rainfall, soil pH {env.soilPh}. "
    summary += f"Goal priority: **{goal_label}**."

    # Generate rotation suggestion dynamically
    r_sug = "Rotate with a cereal next cycle to balance soil nutrition."
    if top.name in ["Maize", "Rice"]:
        r_sug = f"Follow {top.name} with a legume (lentil, soybean) next cycle to restore nitrogen."
    elif top.name == "Wheat":
        r_sug = f"Follow wheat with maize or soybean in the next cycle to break disease chains."
    elif top.name in ["Tomato", "Potato"]:
        r_sug = "Rotate out of solanaceae next season - mustard or lentil breaks disease pressure."

    env_sum = f"For **{region}**, **{context.season}** on **{context.soilType}** soil, the agent weights temperature stress, rainfall reliability, and soil water holding capacity. Goal: **{context.primaryGoal}**."

    return SuitabilityResponse(
        agent="suitability",
        environmentalSummary=env_sum,
        rankedCrops=[SuitabilityRankedCrop(name=c.name, score=c.score, rationale=c.rationale) for c in top_crops],
        context=context,
        env=env,
        summary=summary,
        crops=top_crops,
        rotationSuggestion=r_sug
    )
