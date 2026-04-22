import re
from fastapi import APIRouter
from app.api.schemas import AdvisorRequest, AdvisorResponse

router = APIRouter()

@router.post("/chat", response_model=AdvisorResponse)
def farm_advisor_chat(body: AdvisorRequest):
    messages = body.messages
    context = body.context

    # Get last user message
    user_msgs = [m.content for m in messages if m.role == "user"]
    q = user_msgs[-1].lower() if user_msgs else ""
    print(f"DEBUG ADVISOR: q='{q}'")
    
    region = context.region.strip() if context.region else "your area"
    
    goal = "balanced yield and resilience"
    if context.primaryGoal == "profit":
        goal = "margin and market timing"
    elif context.primaryGoal == "yield":
        goal = "maximizing yield"
    elif context.primaryGoal == "sustainability":
        goal = "soil health and lower inputs"

    # Rule-based routing
    if any(kw in q for kw in ["price", "market", "sell", "commodity", "timing"]):
        reply = f"For **{region}**, market-linked decisions work best when you combine USDA/commodity trend data with your harvest window.\n\n- Track basis and local elevator bids vs. futures.\n- If your goal is {goal}, stress-test a \"sell-by\" date against storage cost."
    elif any(kw in q for kw in ["disease", "pest", "leaf", "spot", "yellow", "health"]):
        reply = f"Crop health checks should pair **clear photos** (canopy + affected leaves) with **growth stage** and recent weather.\n\n- Rule out nutrition issues before assuming disease.\n- For {region}, align scouting with humid/warm periods when fungal pressure rises."
    elif any(kw in q for kw in ["what", "grow", "crop", "rotate", "suitability", "plant"]):
        notes_str = f"Notes you added: _{context.notes.strip()}_" if context.notes.strip() else "Add notes in Farm context for more specific rotation ideas."
        reply = f"Here is a **structured starting point** for {region} ({context.season}, {context.soilType}).\n\n1. **Shortlist** 3–5 crops that match season length and water budget.\n2. **Score** them on heat/cold risk, soil fit, and market outlet.\n\nYour stated goal centers on **{goal}**. {notes_str}"
    elif any(kw in q for kw in ["soil", "moisture", "irrigation", "water", "nasa"]):
        reply = f"With **{context.soilType}** soil on ~**{context.farmSizeAcres}** acres, water management should follow soil moisture trends and rooting depth.\n\n- Use NASA SMAP/IMERG-style signals as a regional guide, then ground-truth with field probes.\n- Match irrigation to crop stage; peak need often tracks flowering/grain fill.\n- Goal focus: {goal}."
    else:
        reply = f"I am ready to assist. I see you farm in **{region}** with **{context.soilType}** soil, ~**{context.farmSizeAcres}** acres, **{context.season}** season, optimizing for **{goal}**.\n\nTry asking about:\n- **Crop suitability** and rotation\n- **Market timing** and selling windows\n- **Crop health** scouting\n- **Soil moisture** and irrigation"

    return AdvisorResponse(reply=reply)
