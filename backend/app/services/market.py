from __future__ import annotations

import hashlib
import random
from time import time

from app.models import MarketReport, PricePoint, SellingWindow


MARKET_SEEDS: dict[str, dict[str, float | str]] = {
    "Maize": {"base": 42.0, "unit": "USD/quintal", "noise": 2.4, "drift": 0.8},
    "Rice": {"base": 68.0, "unit": "USD/quintal", "noise": 3.0, "drift": 0.6},
    "Wheat": {"base": 55.0, "unit": "USD/quintal", "noise": 2.0, "drift": 0.4},
    "Lentil": {"base": 98.0, "unit": "USD/quintal", "noise": 4.5, "drift": 1.2},
    "Tomato": {"base": 22.0, "unit": "USD/quintal", "noise": 3.8, "drift": -0.3},
    "Potato": {"base": 28.0, "unit": "USD/quintal", "noise": 2.2, "drift": 0.5},
    "Mustard": {"base": 72.0, "unit": "USD/quintal", "noise": 2.6, "drift": 0.7},
    "Soybean": {"base": 61.0, "unit": "USD/quintal", "noise": 2.8, "drift": 0.9},
}


def supported_crops() -> list[str]:
    return list(MARKET_SEEDS.keys())


def _randomizer(seed: str) -> random.Random:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def build_market_report(crop: str) -> MarketReport:
    seed = MARKET_SEEDS.get(crop, MARKET_SEEDS["Maize"])
    rnd = _randomizer(f"{crop}:farmwise")

    base = float(seed["base"])
    unit = str(seed["unit"])
    noise = float(seed["noise"])
    drift = float(seed["drift"])

    price = base
    trend: list[PricePoint] = []
    for week in range(-4, 4):
        shock = (rnd.random() - 0.5) * noise
        price = price + drift * (0.6 if week < 0 else 1.0) + shock
        label = f"W{week}" if week < 0 else ("Now" if week == 0 else f"W+{week}")
        trend.append(PricePoint(label=label, price=round(price, 1), forecast=week >= 1))

    current_price = next(point.price for point in trend if point.label == "Now")
    forecast_points = [point for point in trend if point.forecast]
    peak_point = max(forecast_points, key=lambda point: point.price)

    windows = [
        SellingWindow(
            label="Forward sale",
            window="This week",
            reason=(
                f"Spot is above the seasonal median ({base}). Hedge 20-30%."
                if current_price > base
                else "Spot is below the seasonal median; avoid heavy forward selling right now."
            ),
            confidence="medium" if current_price > base else "low",
        ),
        SellingWindow(
            label="Main harvest window",
            window=peak_point.label,
            reason=f"Forecast peak around {peak_point.label} at {peak_point.price} {unit.split('/')[0]}.",
            confidence="high" if peak_point.price > base * 1.05 else "medium",
        ),
        SellingWindow(
            label="Hold and store",
            window="Post-harvest",
            reason=(
                "Prices are drifting up; storage may pay off if drying and pest costs stay low."
                if drift > 0
                else "Downward drift is visible; do not hold unless storage cost is near zero."
            ),
            confidence="medium" if drift > 0 else "low",
        ),
    ]

    summary = " ".join(
        [
            f"{crop} spot is {current_price} {unit} versus a seasonal median of {base}.",
            f"The 8-week forecast peaks near {peak_point.label} at {peak_point.price}.",
            (
                "Short-term drift is positive; watch for demand-side surprises."
                if drift > 0
                else "Short-term drift is flat to down; prioritize earlier selling windows."
            ),
        ]
    )

    return MarketReport(
        crop=crop,
        currency="USD",
        unit=unit,
        currentPrice=current_price,
        seasonalMedian=base,
        trend=trend,
        windows=windows,
        summary=summary,
        source="Fallback market forecaster (replace with USDA AMS or regional market APIs)",
        generatedAt=round(time() * 1000),
    )
