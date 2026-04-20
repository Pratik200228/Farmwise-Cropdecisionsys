from __future__ import annotations

from dataclasses import dataclass
from time import time

from app.models import CropSuitability, FarmContext, SuitabilityReport


@dataclass(frozen=True)
class CropProfile:
    name: str
    tempC: tuple[int, int]
    humidityPct: tuple[int, int]
    rainMm: tuple[int, int]
    windKph: tuple[int, int]
    phRange: tuple[float, float]
    soilFit: dict[str, int]
    plantingHints: dict[str, str]


CROP_CATALOG: tuple[CropProfile, ...] = (
    CropProfile(
        name="Maize",
        tempC=(18, 32),
        humidityPct=(40, 80),
        rainMm=(120, 400),
        windKph=(0, 25),
        phRange=(5.5, 7.5),
        soilFit={"loam": 95, "silt": 85, "clay": 70, "sandy": 60, "black": 88},
        plantingHints={
            "kharif": "Late May - Mid June",
            "rabi": "Late October - Mid November",
            "default": "At the start of the rainy season",
        },
    ),
    CropProfile(
        name="Rice",
        tempC=(20, 35),
        humidityPct=(60, 95),
        rainMm=(200, 600),
        windKph=(0, 20),
        phRange=(5.0, 7.5),
        soilFit={"loam": 85, "silt": 80, "clay": 95, "sandy": 40, "black": 80},
        plantingHints={
            "kharif": "Mid June - Mid July",
            "default": "Once monsoon rains are reliable",
        },
    ),
    CropProfile(
        name="Wheat",
        tempC=(10, 25),
        humidityPct=(40, 70),
        rainMm=(80, 250),
        windKph=(0, 30),
        phRange=(6.0, 7.5),
        soilFit={"loam": 92, "silt": 85, "clay": 80, "sandy": 55, "black": 88},
        plantingHints={
            "rabi": "Early - Mid November",
            "default": "Cool weather sowing window",
        },
    ),
    CropProfile(
        name="Lentil",
        tempC=(15, 28),
        humidityPct=(35, 65),
        rainMm=(60, 180),
        windKph=(0, 30),
        phRange=(6.0, 7.8),
        soilFit={"loam": 90, "silt": 80, "clay": 60, "sandy": 70, "black": 85},
        plantingHints={
            "rabi": "October - November",
            "default": "After main cereal harvest",
        },
    ),
    CropProfile(
        name="Tomato",
        tempC=(18, 30),
        humidityPct=(55, 80),
        rainMm=(100, 250),
        windKph=(0, 20),
        phRange=(6.0, 7.0),
        soilFit={"loam": 92, "silt": 85, "clay": 65, "sandy": 60, "black": 75},
        plantingHints={
            "kharif": "June - July (with drainage)",
            "rabi": "September - October",
            "default": "Transplant 4-6 weeks after sowing",
        },
    ),
    CropProfile(
        name="Potato",
        tempC=(12, 24),
        humidityPct=(50, 80),
        rainMm=(100, 300),
        windKph=(0, 25),
        phRange=(5.5, 6.8),
        soilFit={"loam": 90, "silt": 80, "clay": 60, "sandy": 80, "black": 70},
        plantingHints={
            "rabi": "Mid October - November",
            "default": "Cool nights with moist soil",
        },
    ),
    CropProfile(
        name="Mustard",
        tempC=(10, 25),
        humidityPct=(40, 70),
        rainMm=(60, 200),
        windKph=(0, 30),
        phRange=(6.0, 7.5),
        soilFit={"loam": 88, "silt": 85, "clay": 78, "sandy": 65, "black": 82},
        plantingHints={
            "rabi": "October - November",
            "default": "After monsoon, before frost",
        },
    ),
    CropProfile(
        name="Soybean",
        tempC=(20, 32),
        humidityPct=(50, 80),
        rainMm=(150, 400),
        windKph=(0, 25),
        phRange=(6.0, 7.5),
        soilFit={"loam": 90, "silt": 85, "clay": 72, "sandy": 65, "black": 92},
        plantingHints={
            "kharif": "Mid June - Early July",
            "default": "Early rainy season",
        },
    ),
)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _range_fit(value: float, bounds: tuple[float, float]) -> int:
    lower, upper = bounds
    if lower <= value <= upper:
        return 100
    span = max(1.0, upper - lower)
    outside = lower - value if value < lower else value - upper
    return round(_clamp(100 - (outside / span) * 120, 0, 100))


def _pick_planting_window(profile: CropProfile, season: str) -> str:
    return profile.plantingHints.get(season.strip().lower(), profile.plantingHints["default"])


def _score_crop(profile: CropProfile, context: FarmContext) -> CropSuitability:
    env = context.env
    temperature = _range_fit(env.temperatureC, profile.tempC)
    humidity = _range_fit(env.humidityPct, profile.humidityPct)
    rainfall = _range_fit(env.rainfallMm, profile.rainMm)
    wind = _range_fit(env.windKph, profile.windKph)
    soil_type_fit = profile.soilFit.get(context.soilType, 60)
    ph_fit = _range_fit(env.soilPh, profile.phRange)
    soil = round(soil_type_fit * 0.6 + ph_fit * 0.4)

    score = round(
        temperature * 0.28
        + rainfall * 0.25
        + soil * 0.22
        + humidity * 0.15
        + wind * 0.10
    )
    confidence = _clamp(
        0.55 + (min(temperature, rainfall, soil) / 100) * 0.4 - (0.05 if env.soilMoisturePct < 20 else 0),
        0.40,
        0.98,
    )

    warnings: list[str] = []
    if temperature < 55:
        warnings.append("Temperature is outside the preferred band.")
    if rainfall < 55:
        warnings.append("Rainfall support looks marginal; plan irrigation.")
    if humidity < 55:
        warnings.append("Humidity is off; monitor transpiration stress.")
    if soil < 55:
        warnings.append("Soil type or pH fit is weak; consider amendments.")
    if wind < 55:
        warnings.append("Wind exposure is high; stake tall crops.")

    rationale_bits = [
        f"Temperature fit {temperature}/100, rainfall fit {rainfall}/100, soil fit {soil}/100."
    ]
    if not warnings:
        rationale_bits.append("All key environmental factors sit inside the crop comfort band.")

    return CropSuitability(
        name=profile.name,
        score=score,
        confidence=round(confidence, 2),
        fit={
            "temperature": temperature,
            "humidity": humidity,
            "wind": wind,
            "rainfall": rainfall,
            "soil": soil,
        },
        rationale=" ".join(rationale_bits),
        plantingWindow=_pick_planting_window(profile, context.season),
        warnings=warnings,
    )


def _rotation_suggestion(top_crop: str) -> str:
    if top_crop in {"Maize", "Rice"}:
        return f"Follow {top_crop} with a legume (lentil or soybean) next cycle to restore nitrogen."
    if top_crop == "Wheat":
        return "Follow wheat with maize or soybean next cycle to break disease chains."
    if top_crop in {"Tomato", "Potato"}:
        return "Rotate out of solanaceae next season; mustard or lentil can break disease pressure."
    return "Rotate with a cereal next cycle to balance soil nutrition."


def analyze_crop_suitability(
    context: FarmContext, candidate_crops: list[str] | None = None
) -> SuitabilityReport:
    allowed = {name.lower() for name in candidate_crops or []}
    profiles = [
        profile for profile in CROP_CATALOG if not allowed or profile.name.lower() in allowed
    ]
    if not profiles:
        profiles = list(CROP_CATALOG)

    crops = sorted((_score_crop(profile, context) for profile in profiles), key=lambda item: item.score, reverse=True)
    top = crops[0]
    second = crops[1] if len(crops) > 1 else crops[0]

    goal_label = {
        "profit": "profit and margin",
        "yield": "yield maximization",
        "sustainability": "soil health and lower inputs",
        "mixed": "balanced yield and resilience",
    }[context.primaryGoal]

    summary = " ".join(
        [
            f"For {context.region.strip() or 'your region'} this {context.season} on {context.soilType} soil, the best fit is {top.name} at {top.score}/100.",
            f"{second.name} is the strongest backup option at {second.score}/100.",
            (
                f"Environmental read: {context.env.temperatureC} C average temperature, "
                f"{context.env.humidityPct}% humidity, {context.env.rainfallMm} mm expected rainfall, "
                f"soil pH {context.env.soilPh}."
            ),
            f"Decision priority: {goal_label}.",
        ]
    )

    return SuitabilityReport(
        context=context,
        env=context.env,
        summary=summary,
        crops=crops[:6],
        rotationSuggestion=_rotation_suggestion(top.name),
        generatedAt=round(time() * 1000),
    )
