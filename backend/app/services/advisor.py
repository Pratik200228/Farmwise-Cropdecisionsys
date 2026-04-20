from __future__ import annotations

from app.models import ChatMessage, FarmContext


def _last_user_text(messages: list[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content.lower()
    return ""


def build_advisor_reply(messages: list[ChatMessage], context: FarmContext) -> str:
    question = _last_user_text(messages)
    region = context.region.strip() or "your area"
    goal = {
        "profit": "margin and market timing",
        "yield": "maximizing yield",
        "sustainability": "soil health and lower inputs",
        "mixed": "balanced yield and resilience",
    }[context.primaryGoal]

    if any(token in question for token in ("price", "market", "sell", "commodity")):
        return (
            f"For {region}, market-linked decisions work best when you compare local bids against the seasonal baseline. "
            f"Track basis, storage cost, and transport margin. With your current goal of {goal}, sell in stages instead of in one lot."
        )

    if any(token in question for token in ("disease", "pest", "leaf", "spot", "yellow", "health")):
        return (
            f"Crop health checks should pair symptom notes with growth stage and recent weather for {region}. "
            "Rule out water and nutrition stress before assuming disease. If symptoms spread quickly, escalate with photos and lab support."
        )

    if any(token in question for token in ("soil", "moisture", "irrigation", "water")):
        return (
            f"With {context.soilType} soil on about {context.farmSizeAcres} acres, irrigation planning should follow root depth and soil moisture trends. "
            "Use regional moisture signals as guidance, then ground-truth in the field before changing irrigation frequency."
        )

    if any(token in question for token in ("grow", "crop", "rotate", "suitability", "plant")):
        return (
            f"Start with a shortlist of crops that fit {context.season}, your water budget, and {context.soilType} soil in {region}. "
            f"Then rank them by suitability score, market outlet, and how well they support your goal of {goal}. "
            "Rotate with legumes or cereals to manage fertility and disease pressure."
        )

    return (
        f"I am the FarmWise decision-support assistant for {region}. "
        f"I can help interpret crop suitability, market timing, crop health, and irrigation decisions with your goal focused on {goal}."
    )
