import os
import logging
from typing import List, Dict

import requests
from fastapi import APIRouter
from app.api.schemas import AdvisorRequest, AdvisorResponse

router = APIRouter()

logger = logging.getLogger(__name__)


# --- Per-crop sowing windows (used by sowing-timing intent) -----------------

_SOWING_WINDOWS = {
    "cotton":      "Cotton: late spring to early monsoon (April-July). Needs warm soil >18C and stable rainfall onset.",
    "rice":        "Rice / paddy: with monsoon onset (June-July) for kharif; Nov-Dec for boro/rabi rice.",
    "wheat":       "Wheat: cool-season sowing (Oct 25 - Nov 30). Late sowing past mid-Dec drops yield ~1%/day.",
    "barley":      "Barley: same as wheat (Oct-Dec) but tolerates colder, drier soils.",
    "maize":       "Maize: kharif sowing late June - early July; rabi maize Oct-Nov in irrigated belts.",
    "mustard":     "Mustard / sarson: Oct 15 - Nov 10. Needs cool, dry winter for siliqua fill.",
    "lentil":      "Lentil / masoor: Oct 25 - Nov 15. Sow on residual moisture after rice/maize harvest.",
    "chickpea":    "Chickpea / chana: Oct 20 - Nov 15. Skip irrigation 7-10 days before sowing.",
    "soybean":     "Soybean: with monsoon onset (June 20 - July 15). Avoid waterlogged plots.",
    "sugarcane":   "Sugarcane: Feb-March (spring) or Oct-Nov (autumn) depending on belt.",
    "tomato":      "Tomato: nursery in June or Nov-Dec; transplant 25-30 days later. Avoid frost.",
    "potato":      "Potato: Oct 1 - Oct 25 in north plains; Aug-Sept in hills. Soil temp <22C is ideal.",
    "onion":       "Onion: nursery in Sept-Oct (rabi) or May-June (kharif); transplant 6-8 weeks later.",
    "chili":       "Chili: nursery May-June (kharif) or Sept-Oct (rabi). Transplant 35-40 days later.",
    "groundnut":   "Groundnut: with monsoon (June 15 - July 15). Likes well-drained sandy loam.",
    "jowar":       "Jowar / sorghum: kharif June-July; rabi Sept-Oct in receding-moisture areas.",
    "bajra":       "Bajra / pearl millet: June-July. Tolerates poor soils + low rainfall.",
    "ragi":        "Ragi / finger millet: June-July (kharif). Direct-seeded or transplanted 4-week nursery.",
    "turmeric":    "Turmeric: April-June planting, ~9 month crop. Needs warm, well-drained loam.",
}

_HARVEST_WINDOWS = {
    "wheat":     "Wheat: 120-150 days. Harvest when ears turn golden and grain hardens (Apr in N. India).",
    "rice":      "Rice: 110-140 days. Harvest at 80-85% golden grains, before lodging.",
    "maize":     "Maize: 90-110 days. Husk dry, kernel hard with black layer at base.",
    "cotton":    "Cotton: 150-180 days. Pick bolls in 3 flushes after they open white and dry.",
    "mustard":   "Mustard: 120-140 days. Harvest when 75% siliqua turn yellow.",
    "lentil":    "Lentil: 110-130 days. Harvest when pods turn brown, before shattering.",
    "chickpea":  "Chickpea: 100-120 days. Lower leaves yellow, pods rattle when shaken.",
    "potato":    "Potato: 90-110 days. Cut haulms 7-10 days before digging to set skin.",
    "tomato":    "Tomato: 60-90 days from transplant. Pick at breaker stage for distant markets.",
    "soybean":   "Soybean: 95-110 days. Pods turn brown, leaves drop, moisture drops below 14%.",
    "groundnut": "Groundnut: 105-125 days. Pods rattle when shaken; check 10 random plants.",
    "sugarcane": "Sugarcane: 12 months. Brix >18%, leaves yellowing, internodes hard.",
}


def _detect_crop(q: str) -> str:
    """Map any vernacular crop name in q to a normalized key."""
    aliases = {
        "cotton": "cotton", "kapas": "cotton",
        "rice": "rice", "paddy": "rice", "dhan": "rice", "chawal": "rice",
        "wheat": "wheat", "gehu": "wheat", "gehoon": "wheat", "kanak": "wheat",
        "barley": "barley", "jau": "barley",
        "maize": "maize", "corn": "maize", "makka": "maize", "bhutta": "maize",
        "mustard": "mustard", "sarson": "mustard", "rai": "mustard",
        "lentil": "lentil", "masoor": "lentil", "masur": "lentil",
        "chickpea": "chickpea", "chana": "chickpea", "gram": "chickpea",
        "soybean": "soybean", "soya": "soybean",
        "sugarcane": "sugarcane", "ganna": "sugarcane",
        "tomato": "tomato", "tamatar": "tomato",
        "potato": "potato", "aloo": "potato",
        "onion": "onion", "pyaaz": "onion", "pyaz": "onion",
        "chili": "chili", "chilli": "chili", "mirch": "chili",
        "groundnut": "groundnut", "peanut": "groundnut", "moongphali": "groundnut",
        "jowar": "jowar", "sorghum": "jowar",
        "bajra": "bajra", "pearl millet": "bajra",
        "ragi": "ragi", "finger millet": "ragi", "mandua": "ragi",
        "turmeric": "turmeric", "haldi": "turmeric",
    }
    for alias, key in aliases.items():
        if alias in q:
            return key
    return ""


def _season_window_for_crop(crop: str, season: str) -> str:
    return _SOWING_WINDOWS.get(crop, "")


def _simple_question_reply(q: str, body: AdvisorRequest) -> str:
    """Comprehensive intent dispatcher for common farmer queries.

    Order matters: more specific patterns must be checked first so they
    are not swallowed by a generic match.
    """
    ctx = body.context
    region = ctx.region.strip() if ctx.region else "your area"
    soil = ctx.soilType.strip() if ctx.soilType else "your"
    season = ctx.season.strip() if ctx.season else "this season"
    env = ctx.env

    # --- A. Greeting ----------------------------------------------------
    greetings = ["hi", "hello", "hey", "good morning", "good evening",
                 "good night", "good afternoon", "namaste", "namaskar",
                 "ram ram", "vanakkam", "salaam", "pranam"]
    if any(g == q.strip() or q.strip().startswith(g + " ") or q.strip() == g for g in greetings):
        return (
            f"Hello! I am the **FarmWise assistant** for **{region}**.\n\n"
            "Try one of these:\n"
            f"- What should I grow this {season}?\n"
            "- Best time to plant rice / wheat / mustard in my area?\n"
            "- My tomato leaves have yellow spots — what should I check?\n"
            "- When should I sell my wheat?"
        )

    # --- B. Thanks / bye ------------------------------------------------
    if any(t in q for t in ["thank you", "thanks", "thank u", "thx", "appreciate", "dhanyavad", "shukriya"]):
        return "You are welcome. If anything else comes up — pests, prices, planting timing, soil — just ask."
    if any(b in q for b in ["bye", "goodbye", "see you", "see ya", "tata", "alvida"]):
        return "Take care. Come back anytime — I am always here for crop, soil, market, and pest questions."

    # --- C. Identity / capabilities ------------------------------------
    if any(p in q for p in ["who are you", "what is farmwise", "what can you do",
                            "are you ai", "are you human", "are you real",
                            "capabilities", "what do you do", "how can you help"]):
        return (
            "I am the **FarmWise assistant**. I can help with:\n"
            "- **Crop suitability** — what to grow given your soil, season, and region\n"
            "- **Sowing & harvest timing** — for major crops\n"
            "- **Soil & irrigation** — pH, moisture, fertilizer, water schedule\n"
            "- **Pest & disease checks** — describe the symptom or upload a leaf photo\n"
            "- **Market timing** — when to sell, mandi rates, price awareness\n"
            "- **Government schemes** — basics on PM-KISAN, KCC, crop insurance"
        )

    # --- D. Quick yes/no warm-ups --------------------------------------
    if any(p in q for p in ["are you free", "is this free", "can you help me",
                            "can you talk", "are you working", "are you online"]):
        return "Yes — I am here, working, and free to use. What is your question?"

    # --- E. Encouragement / worried ------------------------------------
    if any(p in q for p in ["losing", "in debt", "broke", "bad yield", "nothing works",
                            "frustrated", "tired", "give up", "depressed", "suicide",
                            "cant continue", "cannot continue"]):
        return (
            "That sounds really hard — many farmers feel the same. A few practical next steps:\n\n"
            "1. **Talk to your local KVK (Krishi Vigyan Kendra)** — free agronomist advice + subsidized inputs.\n"
            "2. **Restructure debt** via KCC; ask your bank manager about extending tenure.\n"
            "3. **Diversify next season** — adding one short-duration crop (60-90 days) cuts risk.\n"
            "4. **Enroll in PMFBY (crop insurance)** for next sowing — premium is small (1.5-5%).\n\n"
            "If it ever feels overwhelming, please call **Kisan Call Centre 1800-180-1551** (free) "
            "or **iCall 9152987821** for emotional support."
        )

    # --- F. Weather queries --------------------------------------------
    if any(p in q for p in ["weather", "will it rain", "going to rain", "monsoon",
                            "forecast", "temperature today", "is it hot", "is it cold",
                            "kab barish", "barish hogi"]):
        return (
            f"I do not have live weather access. For **{region}**, check the **IMD app** or AccuWeather "
            "for a rolling 7-day view.\n\n"
            f"Your current Farm context shows: temp **{env.temperatureC}C**, humidity "
            f"**{env.humidityPct}%**, wind **{env.windKph} kph**, rainfall **{env.rainfallMm} mm**. "
            "Update those in the right panel and I will use them in my answers."
        )

    # --- G. Soil pH / soil basics --------------------------------------
    if any(p in q for p in ["soil ph", "ph of soil", "what is ph", "my soil is", "soil acidic",
                            "soil alkaline", "soil type", "what is loam", "what is clay",
                            "what is sandy", "improve soil", "test soil", "soil test"]):
        return (
            f"Soil pH tells you how acidic or alkaline the soil is. Your context says **pH {env.soilPh}**.\n\n"
            "- **5.5-6.5** — slightly acidic, good for most crops (rice, maize, potato, tomato).\n"
            "- **6.5-7.5** — neutral, suits wheat, mustard, lentil, chickpea.\n"
            "- **>7.8** — alkaline; add gypsum + organic matter to bring it down.\n"
            "- **<5.5** — too acidic; add lime + compost.\n\n"
            "Free soil test: request a **Soil Health Card** at your block agriculture office."
        )

    # --- H. Fertilizer / manure ----------------------------------------
    if any(p in q for p in ["fertilizer", "fertiliser", "urea", "dap", "npk", "manure",
                            "compost", "vermicompost", "khaad", "gobar"]):
        return (
            "Safe per-acre rule of thumb (verify with soil test):\n\n"
            "- **At sowing (basal)**: 20-40 kg DAP **or** 8-10 t farmyard manure / compost.\n"
            "- **Top-dress nitrogen**: 30-50 kg urea split in 2 doses (tillering + flowering).\n"
            "- **Cereals** (wheat, rice, maize) need more N; **pulses** (lentil, gram) fix their own N — skip N.\n"
            "- Avoid blanket spraying. Apply when soil is moist; never on dry soil.\n\n"
            f"For **{soil}** soil, organic matter (compost/FYM) is the single highest-ROI input."
        )

    # --- I. Irrigation -------------------------------------------------
    if any(p in q for p in ["irrigation", "water schedule", "how often", "kab paani",
                            "paani dena", "drip", "flood irrigation", "sprinkler",
                            "watering", "how much water", "should i water",
                            "water my crop", "water my plant", "water this week"]):
        return (
            f"For **{soil}** soil, water guidance:\n"
            "- **Sandy** — frequent + light (every 3-5 days, smaller volume).\n"
            "- **Loam** — moderate (every 6-8 days).\n"
            "- **Clay** — slow + deep (every 8-12 days).\n\n"
            "**Critical irrigation stages**: tillering, flowering, grain fill. Skip during heavy rain.\n"
            f"Your soil moisture reading is **{env.soilMoisturePct}%** — below 30% is dry, above 60% is saturated.\n"
            "Drip saves 50%+ water vs flood; sprinkler is good for cereals on sandy land."
        )

    # --- J. Sowing timing per crop -------------------------------------
    crop = _detect_crop(q)
    asks_sow = any(kw in q for kw in ["best time", "when to plant", "when to sow",
                                      "sowing time", "planting time", "kab boyein",
                                      "kab lagayein", "when should i plant"])
    if asks_sow and crop:
        window = _SOWING_WINDOWS.get(crop, "")
        if window:
            return (
                f"{window}\n\n"
                f"For **{region}** in **{season}**, confirm with local rainfall start and soil moisture "
                "before sowing. If you share district-level climate, I can narrow this to a sowing week."
            )

    # --- K. Storage / post-harvest (must precede harvest timing,
    #        otherwise "store wheat after harvest" matches harvest first) -
    if any(p in q for p in ["storage", "store grain", "store wheat", "store rice",
                            "post harvest", "post-harvest", "drying grain", "godown",
                            "weevil", "stored grain", "ghun", "sundi",
                            "how to store", "store after harvest"]):
        return (
            "Storage basics:\n\n"
            "- **Dry grain to <12% moisture** before storing (sun-dry 2-3 days; bite test - clean snap = ready).\n"
            "- **Clean dry godown**, raise sacks off floor with pallets, ensure ventilation.\n"
            "- **Aluminium phosphide tablet** or neem leaves keeps weevils out of stored wheat/rice.\n"
            "- Inspect every 15 days for hot spots; re-bag if you find clumping or live insects.\n"
            "- For onions/potato - cool, dark, well-aired storage; never stack >2 ft deep."
        )

    # --- L. Harvest timing per crop -----------------------------------
    asks_harvest = any(kw in q for kw in ["harvest", "when to cut", "when to harvest",
                                          "ready to cut", "kab katega", "pakna",
                                          "days to maturity"])
    if asks_harvest and crop:
        window = _HARVEST_WINDOWS.get(crop, "")
        if window:
            return f"{window}\n\nVerify with 10-plant random sampling before full-field harvest."

    # --- L. Pest indicators --------------------------------------------
    if any(p in q for p in ["bug", "insect", "worm", "caterpillar", "holes in leaf",
                            "leaves chewed", "sticky", "aphid", "whitefly", "hopper",
                            "kira", "kit", "kaira", "termite", "deemak"]):
        return (
            "Quick pest scout:\n\n"
            "1. **Holes / chewed edges** → caterpillars, beetles. Hand-pick early; spray "
            "neem oil (5 ml/L) or *Bacillus thuringiensis* if heavy.\n"
            "2. **Sticky leaves + black sooty mould** → aphids/whiteflies sucking sap. "
            "Spray neem oil or imidacloprid (read the label).\n"
            "3. **Hoppers (jumping insects)** → clear weeds; spray thiamethoxam.\n"
            "4. **Termites at root** → drench chlorpyrifos around base.\n\n"
            "Always **scout before spraying** and avoid spraying during flowering hours so pollinators stay safe."
        )

    # --- M. Disease indicators (non-technical) ------------------------
    if any(p in q for p in ["yellow leaf", "yellow leaves", "yellow spot", "brown spot",
                            "white spot", "powdery", "wilting", "wilt", "rotting", "rot",
                            "drying up", "leaves falling", "leaves curling", "halo"]):
        return (
            "Symptom interpreter:\n\n"
            "- **Lower-leaf yellowing** → likely **nitrogen deficiency**, not disease. Top-dress with urea.\n"
            "- **Brown rings + yellow halo** → **early/late blight** (fungal). Remove leaves, spray copper.\n"
            "- **White powder on top of leaf** → **powdery mildew**. Spray sulfur or potassium bicarbonate.\n"
            "- **Wilting only in afternoon** → **water stress**, not disease. Irrigate deeper.\n"
            "- **Leaves curling + sticky** → **virus** spread by whiteflies/aphids. Control the vector first.\n\n"
            "For a confirmed diagnosis, open the **Crop Health** tab and upload a clear leaf photo."
        )

    # --- N. Market / pricing ------------------------------------------
    if any(p in q for p in ["price", "mandi rate", "kya rate", "market rate", "mandi",
                            "when to sell", "kab bechu", "best price", "msp"]):
        return (
            f"For **{region}**, three rules to time selling:\n\n"
            "1. **Track 4-week price trend** in your local mandi — falling trend means sell sooner; "
            "rising trend means hold (if storable).\n"
            "2. **Cost of storage** — if it costs ~Rs.20/quintal/month and price is not rising at "
            "least that fast, sell now.\n"
            "3. **Demand windows** — wheat/rice prices often firm up post-festival; vegetables crash "
            "within 7-10 days of peak harvest.\n\n"
            "Open the **Market** tab to see commodity trends from the API. For MSP info, check eNAM or "
            "your state agriculture portal."
        )

    # --- P. Government schemes ----------------------------------------
    if any(p in q for p in ["pm kisan", "pmkisan", "kisan samman", "kcc", "kisan credit",
                            "fasal bima", "pmfby", "crop insurance", "subsidy", "yojana",
                            "scheme", "loan", "sarkari"]):
        return (
            "Major support schemes:\n\n"
            "- **PM-KISAN** — Rs.6,000/year direct transfer to small/marginal farmers. "
            "Apply at **pmkisan.gov.in** or your CSC.\n"
            "- **KCC (Kisan Credit Card)** — short-term crop loan up to Rs.3 lakh at 4% effective rate "
            "(timely repayment). Apply at any nationalized bank.\n"
            "- **PMFBY (Fasal Bima)** — crop insurance, premium 1.5-5% of sum insured. "
            "Enroll within 7 days of sowing via your bank or CSC.\n"
            "- **Soil Health Card** — free soil test at your block agriculture office.\n"
            "- **PM Kusum** — solar pump subsidy for irrigation, up to 60% support."
        )

    # --- Q. Cost / profit ---------------------------------------------
    if any(p in q for p in ["cost", "profit", "budget", "kharcha", "kamana", "kitna",
                            "expense", "income", "earn", "loss"]):
        return (
            f"Rough per-acre numbers for **{region}** (verify locally):\n\n"
            "- **Wheat / rice / maize** — Rs.20,000-30,000 input cost; profit depends on MSP + yield.\n"
            "- **Pulses (lentil, gram)** — Rs.10,000-15,000, lower water need, often higher margin.\n"
            "- **Vegetables (tomato, onion)** — Rs.40,000-80,000 but volatile prices.\n\n"
            "Always tally: seed + fertilizer + labour + water + harvest + transport.\n"
            "Profit = (yield x price) - total cost. If margin <15%, rethink the crop or price plan."
        )

    # --- R. Equipment / seeds -----------------------------------------
    if any(p in q for p in ["tractor", "machine", "equipment", "seed", "beej", "where to buy",
                            "kahaan se", "accha seed", "good seed", "sprayer", "thresher"]):
        return (
            "Inputs guidance:\n\n"
            "- **Seeds** — buy certified seed from your block-level **KVK** or registered seed dealer. "
            "Reject loose / unmarked bags. Save 20% from this season for next? Only if you know the variety.\n"
            "- **Tools** — sub-divisional agri office offers subsidies on sprayers, drip kits, "
            "threshers (often 40-50% subsidized).\n"
            "- **Tractor rental** — apps like **CHC Farm Machinery** (govt) or HelloTractor offer "
            "hourly rentals if buying is not viable."
        )

    # --- S. Crop choice / what to grow --------------------------------
    if any(p in q for p in ["what should i grow", "what to grow", "should i grow",
                            "what crop", "which crop", "what to plant", "what should i plant",
                            "best crop", "good crop", "crop suggestion", "crop suitability",
                            "rotate", "crop rotation", "intercrop", "grow this season",
                            "grow next season", "konsi fasal", "kya bouun"]):
        notes_str = (
            f"Notes you added: _{ctx.notes.strip()}_"
            if ctx.notes and ctx.notes.strip()
            else "Add notes in **Farm context** (right panel) for more specific rotation ideas."
        )
        goal_label = _build_goal_label(ctx.primaryGoal)
        return (
            f"Here is a **structured starting point** for **{region}** "
            f"({season}, {soil} soil, ~{ctx.farmSizeAcres} acres):\n\n"
            "1. **Shortlist** 3-5 crops that match your season length and water budget.\n"
            "2. **Score** them on heat/cold risk, soil fit, and local market outlet.\n"
            "3. **Validate** the top 1-2 in the **Crop Suitability** tab once you have weather + soil readings.\n\n"
            f"Quick suggestions by season:\n"
            "- **Kharif / monsoon** — rice, maize, soybean, cotton, groundnut, jowar, bajra\n"
            "- **Rabi / winter** — wheat, mustard, chickpea, lentil, barley, potato, onion\n"
            "- **Zaid / summer** — moong, watermelon, fodder maize, vegetables (with irrigation)\n\n"
            f"Your stated goal centers on **{goal_label}**. {notes_str}"
        )

    return ""


def _build_goal_label(primary_goal: str) -> str:
    if primary_goal == "profit":
        return "margin and market timing"
    if primary_goal == "yield":
        return "maximizing yield"
    if primary_goal == "sustainability":
        return "soil health and lower inputs"
    return "balanced yield and resilience"


def _rule_based_reply(body: AdvisorRequest) -> str:
    messages = body.messages
    context = body.context

    user_msgs = [m.content for m in messages if m.role == "user"]
    q = user_msgs[-1].lower() if user_msgs else ""
    region = context.region.strip() if context.region else "your area"
    goal = _build_goal_label(context.primaryGoal)
    simple_reply = _simple_question_reply(q, body)
    if simple_reply:
        return simple_reply

    if any(kw in q for kw in ["price", "market", "sell", "commodity", "timing", "time", "when"]):
        return (
            f"For **{region}**, market-linked decisions work best when you combine USDA/commodity trend data "
            f"with your harvest window.\n\n- Track basis and local elevator bids vs. futures.\n- If your goal "
            f'is {goal}, stress-test a "sell-by" date against storage cost.'
        )
    elif any(kw in q for kw in ["disease", "pest", "leaf", "spot", "yellow", "health"]):
        return (
            "Crop health checks should pair **clear photos** (canopy + affected leaves) with **growth stage** "
            "and recent weather.\n\n- Rule out nutrition issues before assuming disease.\n"
            f"- For {region}, align scouting with humid/warm periods when fungal pressure rises."
        )
    elif any(kw in q for kw in ["what grow", "which crop", "crop", "rotate", "suitability", "plant"]):
        notes_str = f"Notes you added: _{context.notes.strip()}_" if context.notes.strip() else "Add notes in Farm context for more specific rotation ideas."
        return (
            f"Here is a **structured starting point** for {region} ({context.season}, {context.soilType}).\n\n"
            "1. **Shortlist** 3–5 crops that match season length and water budget.\n"
            "2. **Score** them on heat/cold risk, soil fit, and market outlet.\n\n"
            f"Your stated goal centers on **{goal}**. {notes_str}"
        )
    elif any(kw in q for kw in ["soil", "moisture", "irrigation", "water", "nasa"]):
        return (
            f"With **{context.soilType}** soil on ~**{context.farmSizeAcres}** acres, water management should "
            "follow soil moisture trends and rooting depth.\n\n"
            "- Use NASA SMAP/IMERG-style signals as a regional guide, then ground-truth with field probes.\n"
            "- Match irrigation to crop stage; peak need often tracks flowering/grain fill.\n"
            f"- Goal focus: {goal}."
        )
    return (
        f"I am ready to assist. I see you farm in **{region}** with **{context.soilType}** soil, "
        f"~**{context.farmSizeAcres}** acres, **{context.season}** season, optimizing for **{goal}**.\n\n"
        "Try asking about:\n- **Crop suitability** and rotation\n- **Market timing** and selling windows\n"
        "- **Crop health** scouting\n- **Soil moisture** and irrigation"
    )


def _build_system_prompt(body: AdvisorRequest) -> str:
    ctx = body.context
    goal = _build_goal_label(ctx.primaryGoal)
    notes = ctx.notes.strip() if ctx.notes else "No extra notes provided."
    return (
        "You are FarmWise AI, an agronomy + farm economics assistant.\n"
        "Give practical, concise recommendations for farmers.\n"
        "Prioritize actionable steps, clear assumptions, and risk warnings.\n"
        "Do not claim live data access unless explicitly provided.\n\n"
        "Current farm context:\n"
        f"- Region: {ctx.region}\n"
        f"- Soil type: {ctx.soilType}\n"
        f"- Farm size (acres): {ctx.farmSizeAcres}\n"
        f"- Season: {ctx.season}\n"
        f"- Primary goal: {goal}\n"
        f"- Notes: {notes}\n"
        f"- Environment: temp {ctx.env.temperatureC}C, humidity {ctx.env.humidityPct}%, "
        f"wind {ctx.env.windKph}kph, rainfall {ctx.env.rainfallMm}mm, soil pH {ctx.env.soilPh}, "
        f"soil moisture {ctx.env.soilMoisturePct}%"
    )


def _to_llm_messages(body: AdvisorRequest) -> List[Dict[str, str]]:
    # Keep the thread small for latency/cost.
    trimmed = body.messages[-10:]
    return [{"role": m.role, "content": m.content} for m in trimmed if m.content.strip()]


def _anthropic_reply(api_key: str, system_prompt: str, messages: List[Dict[str, str]]) -> str:
    url = "https://api.anthropic.com/v1/messages"
    payload = {
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        "max_tokens": 700,
        "temperature": 0.35,
        "system": system_prompt,
        "messages": messages,
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    res = requests.post(url, json=payload, headers=headers, timeout=30)
    res.raise_for_status()
    data = res.json()
    content = data.get("content", [])
    text_blocks = [b.get("text", "") for b in content if b.get("type") == "text"]
    return "\n".join([t for t in text_blocks if t]).strip()


def _openai_compatible_reply(
    api_key: str,
    system_prompt: str,
    messages: List[Dict[str, str]],
    base_url: str,
    model: str,
) -> str:
    """Shared helper for any OpenAI-compatible chat-completions API
    (OpenAI, Groq, Together, etc.).
    """
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.35,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    res = requests.post(url, json=payload, headers=headers, timeout=30)
    res.raise_for_status()
    data = res.json()
    choices = data.get("choices", [])
    if not choices:
        return ""
    return (choices[0].get("message", {}) or {}).get("content", "").strip()


def _openai_reply(api_key: str, system_prompt: str, messages: List[Dict[str, str]]) -> str:
    return _openai_compatible_reply(
        api_key,
        system_prompt,
        messages,
        base_url="https://api.openai.com/v1",
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )


def _groq_reply(api_key: str, system_prompt: str, messages: List[Dict[str, str]]) -> str:
    return _openai_compatible_reply(
        api_key,
        system_prompt,
        messages,
        base_url="https://api.groq.com/openai/v1",
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    )


def _llm_reply(body: AdvisorRequest) -> str:
    provider = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()
    system_prompt = _build_system_prompt(body)
    messages = _to_llm_messages(body)

    if not messages:
        return ""

    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            return ""
        return _groq_reply(api_key, system_prompt, messages)

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return ""
        return _openai_reply(api_key, system_prompt, messages)

    # Default provider: Anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return ""
    return _anthropic_reply(api_key, system_prompt, messages)


@router.post("/chat", response_model=AdvisorResponse)
def farm_advisor_chat(body: AdvisorRequest):
    try:
        llm_text = _llm_reply(body)
        if llm_text:
            return AdvisorResponse(reply=llm_text)
    except Exception as exc:
        logger.warning("Advisor LLM call failed, using fallback: %s", exc)

    return AdvisorResponse(reply=_rule_based_reply(body))
