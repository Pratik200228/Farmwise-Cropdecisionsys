"""
Market Intelligence Agent — Utility-Based Agent
Uses the trained RandomForest model (corn_price_model.pkl) for corn price prediction.
Uses seasonal heuristics for all other crops.
"""

import os
import time
import math
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "corn_price_model.pkl")

try:
    _CORN_MODEL = joblib.load(MODEL_PATH)
except Exception:
    _CORN_MODEL = None

CROP_MARKET_CONFIG = {
    "Corn":    {"baseline": 4.50, "unit": "USD/bu", "harvest_month": 10, "currency": "USD"},
    "Maize":   {"baseline": 4.50, "unit": "USD/bu", "harvest_month": 10, "currency": "USD"},
    "Rice":    {"baseline": 14.0, "unit": "USD/cwt", "harvest_month": 9, "currency": "USD"},
    "Wheat":   {"baseline": 5.80, "unit": "USD/bu", "harvest_month": 7, "currency": "USD"},
    "Soybean": {"baseline": 13.5, "unit": "USD/bu", "harvest_month": 10, "currency": "USD"},
    "Tomato":  {"baseline": 85.0, "unit": "USD/short ton", "harvest_month": 8, "currency": "USD"},
    "Potato":  {"baseline": 10.5, "unit": "USD/cwt", "harvest_month": 9, "currency": "USD"},
    "Lentil":  {"baseline": 0.42, "unit": "USD/lb", "harvest_month": 7, "currency": "USD"},
    "Mustard": {"baseline": 0.38, "unit": "USD/lb", "harvest_month": 5, "currency": "USD"},
}

def _seasonal_multiplier(month: int, harvest_month: int) -> float:
    months_to_harvest = (harvest_month - month) % 12
    angle = (months_to_harvest / 12.0) * 2 * math.pi
    return 0.88 + 0.24 * ((1 - math.cos(angle)) / 2)

def _predict_week_price_corn(year: int, month: int) -> float:
    if _CORN_MODEL is None:
        return 4.50
    pred = _CORN_MODEL.predict([[year, month]])[0]
    return round(float(pred), 2)

def _build_trend(crop: str, current_year: int, current_month: int) -> list:
    config = CROP_MARKET_CONFIG.get(crop, CROP_MARKET_CONFIG["Corn"])
    baseline = config["baseline"]
    harvest_month = config["harvest_month"]
    use_model = crop in ("Corn", "Maize") and _CORN_MODEL is not None
    trend = []
    for offset in range(-3, 5):
        week_month = ((current_month - 1 + (offset // 4)) % 12) + 1
        week_year = current_year + ((current_month - 1 + (offset // 4)) // 12)
        is_forecast = offset >= 0
        label = f"W{offset:+d}" if offset != 0 else "Now"
        if use_model:
            price = _predict_week_price_corn(week_year, week_month)
            price = round(price + (offset % 4) * 0.015, 2)
        else:
            mult = _seasonal_multiplier(week_month, harvest_month)
            price = round(baseline * mult, 2)
        trend.append({
            "label": label,
            "price": price,
            "forecast": is_forecast,
        })
    return trend

def _best_selling_window(trend: list, config: dict) -> list:
    forecast_points = [p for p in trend if p["forecast"]]
    if not forecast_points:
        return []

    peak = max(forecast_points, key=lambda p: p["price"])
    peak_price = peak["price"]
    current_price = next((p["price"] for p in trend if p["label"] == "Now"), peak_price)
    pct_gain = ((peak_price - current_price) / current_price * 100) if current_price > 0 else 0

    confidence = "high" if pct_gain >= 5 else "medium" if pct_gain >= 2 else "low"

    return [
        {
            "label": "Peak Window",
            "window": f"Around {peak['label']}",
            "reason": f"Forecast peaks at {config['unit'].split('/')[0]} {peak_price:.2f}/{config['unit'].split('/')[-1]}.",
            "confidence": confidence,
        },
        {
            "label": "Hold Strategy",
            "window": "Wait until peak",
            "reason": "Staggered selling over 2 weeks reduces timing risk.",
            "confidence": "medium",
        },
    ]

def generate_market_forecast(crop: str) -> dict:
    import datetime
    now = datetime.datetime.now()
    config = CROP_MARKET_CONFIG.get(crop, CROP_MARKET_CONFIG["Corn"])
    trend = _build_trend(crop, now.year, now.month)
    current_price = next((p["price"] for p in trend if p["label"] == "Now"), config["baseline"])
    seasonal_median = round(config["baseline"] * 1.0, 2)
    windows = _best_selling_window(trend, config)
    source = (
        "RandomForest ML model trained on USDA NASS corn price data (prabin-branch)"
        if crop in ("Corn", "Maize") and _CORN_MODEL is not None
        else "Seasonal heuristic model based on historical harvest cycles"
    )

    return {
        "crop": crop,
        "currency": config["currency"],
        "unit": config["unit"],
        "currentPrice": current_price,
        "seasonalMedian": seasonal_median,
        "trend": trend,
        "windows": windows,
        "summary": (
            f"Current {crop} price is {config['unit'].split('/')[0]} {current_price:.2f} per "
            f"{config['unit'].split('/')[-1]}. Seasonal median is {seasonal_median:.2f}. "
        ),
        "source": source,
        "generatedAt": int(time.time() * 1000),
    }
