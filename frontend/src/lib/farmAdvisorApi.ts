import type { ChatMessage, FarmContext } from "../types/farm";
import { buildApiUrl, isMockAiEnabled } from "./runtimeConfig";

const ADVISOR_PATH = "/api/v1/farm-advisor/chat";

export type AdvisorRequestBody = {
  messages: { role: "user" | "assistant" | "system"; content: string }[];
  context: FarmContext;
};

export type AdvisorResponseBody = {
  reply?: string;
  message?: string;
};

function lastUserText(messages: ChatMessage[]): string {
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === "user") return messages[i].content;
  }
  return "";
}

const SOWING_WINDOWS: Record<string, string> = {
  cotton: "Cotton: late spring to early monsoon (April-July). Needs warm soil >18C and stable rainfall onset.",
  rice: "Rice / paddy: with monsoon onset (June-July) for kharif; Nov-Dec for boro/rabi rice.",
  wheat: "Wheat: cool-season sowing (Oct 25 - Nov 30). Late sowing past mid-Dec drops yield ~1%/day.",
  barley: "Barley: same as wheat (Oct-Dec) but tolerates colder, drier soils.",
  maize: "Maize: kharif sowing late June - early July; rabi maize Oct-Nov in irrigated belts.",
  mustard: "Mustard / sarson: Oct 15 - Nov 10. Needs cool, dry winter for siliqua fill.",
  lentil: "Lentil / masoor: Oct 25 - Nov 15. Sow on residual moisture after rice/maize harvest.",
  chickpea: "Chickpea / chana: Oct 20 - Nov 15. Skip irrigation 7-10 days before sowing.",
  soybean: "Soybean: with monsoon onset (June 20 - July 15). Avoid waterlogged plots.",
  sugarcane: "Sugarcane: Feb-March (spring) or Oct-Nov (autumn) depending on belt.",
  tomato: "Tomato: nursery in June or Nov-Dec; transplant 25-30 days later. Avoid frost.",
  potato: "Potato: Oct 1 - Oct 25 in north plains; Aug-Sept in hills. Soil temp <22C is ideal.",
  onion: "Onion: nursery in Sept-Oct (rabi) or May-June (kharif); transplant 6-8 weeks later.",
  chili: "Chili: nursery May-June (kharif) or Sept-Oct (rabi). Transplant 35-40 days later.",
  groundnut: "Groundnut: with monsoon (June 15 - July 15). Likes well-drained sandy loam.",
  jowar: "Jowar / sorghum: kharif June-July; rabi Sept-Oct in receding-moisture areas.",
  bajra: "Bajra / pearl millet: June-July. Tolerates poor soils + low rainfall.",
  ragi: "Ragi / finger millet: June-July (kharif). Direct-seeded or transplanted 4-week nursery.",
  turmeric: "Turmeric: April-June planting, ~9 month crop. Needs warm, well-drained loam.",
};

const HARVEST_WINDOWS: Record<string, string> = {
  wheat: "Wheat: 120-150 days. Harvest when ears turn golden and grain hardens (Apr in N. India).",
  rice: "Rice: 110-140 days. Harvest at 80-85% golden grains, before lodging.",
  maize: "Maize: 90-110 days. Husk dry, kernel hard with black layer at base.",
  cotton: "Cotton: 150-180 days. Pick bolls in 3 flushes after they open white and dry.",
  mustard: "Mustard: 120-140 days. Harvest when 75% siliqua turn yellow.",
  lentil: "Lentil: 110-130 days. Harvest when pods turn brown, before shattering.",
  chickpea: "Chickpea: 100-120 days. Lower leaves yellow, pods rattle when shaken.",
  potato: "Potato: 90-110 days. Cut haulms 7-10 days before digging to set skin.",
  tomato: "Tomato: 60-90 days from transplant. Pick at breaker stage for distant markets.",
  soybean: "Soybean: 95-110 days. Pods turn brown, leaves drop, moisture drops below 14%.",
  groundnut: "Groundnut: 105-125 days. Pods rattle when shaken; check 10 random plants.",
  sugarcane: "Sugarcane: 12 months. Brix >18%, leaves yellowing, internodes hard.",
};

const CROP_ALIASES: Array<[RegExp, string]> = [
  [/\b(cotton|kapas)\b/, "cotton"],
  [/\b(rice|paddy|dhan|chawal)\b/, "rice"],
  [/\b(wheat|gehu|gehoon|kanak)\b/, "wheat"],
  [/\b(barley|jau)\b/, "barley"],
  [/\b(maize|corn|makka|bhutta)\b/, "maize"],
  [/\b(mustard|sarson|rai)\b/, "mustard"],
  [/\b(lentil|masoor|masur)\b/, "lentil"],
  [/\b(chickpea|chana|gram)\b/, "chickpea"],
  [/\b(soybean|soya)\b/, "soybean"],
  [/\b(sugarcane|ganna)\b/, "sugarcane"],
  [/\b(tomato|tamatar)\b/, "tomato"],
  [/\b(potato|aloo)\b/, "potato"],
  [/\b(onion|pyaaz|pyaz)\b/, "onion"],
  [/\b(chili|chilli|mirch)\b/, "chili"],
  [/\b(groundnut|peanut|moongphali)\b/, "groundnut"],
  [/\b(jowar|sorghum)\b/, "jowar"],
  [/\b(bajra|pearl millet)\b/, "bajra"],
  [/\b(ragi|finger millet|mandua)\b/, "ragi"],
  [/\b(turmeric|haldi)\b/, "turmeric"],
];

function detectCrop(q: string): string {
  for (const [re, key] of CROP_ALIASES) {
    if (re.test(q)) return key;
  }
  return "";
}

export function mockAdvisorReply(messages: ChatMessage[], context: FarmContext): string {
  const q = lastUserText(messages).toLowerCase().trim();
  const region = context.region.trim() || "your area";
  const soil = context.soilType.trim() || "your";
  const season = context.season.trim() || "this season";
  const env = context.env;
  const goal =
    context.primaryGoal === "profit"
      ? "margin and market timing"
      : context.primaryGoal === "yield"
        ? "maximizing yield"
        : context.primaryGoal === "sustainability"
          ? "soil health and lower inputs"
          : "balanced yield and resilience";

  // A. Greeting
  if (/^(hi|hello|hey|good morning|good evening|good afternoon|good night|namaste|namaskar|ram ram|vanakkam|salaam|pranam)\b/.test(q)) {
    return `Hello! I am the **FarmWise assistant** for **${region}**.\n\nTry one of these:\n- What should I grow this ${season}?\n- Best time to plant rice / wheat / mustard in my area?\n- My tomato leaves have yellow spots — what should I check?\n- When should I sell my wheat?`;
  }

  // B. Thanks / bye
  if (/(thank you|thanks|thank u|thx|appreciate|dhanyavad|shukriya)/.test(q)) {
    return "You are welcome. If anything else comes up — pests, prices, planting timing, soil — just ask.";
  }
  if (/\b(bye|goodbye|see you|see ya|tata|alvida)\b/.test(q)) {
    return "Take care. Come back anytime — I am always here for crop, soil, market, and pest questions.";
  }

  // C. Identity / capabilities
  if (/(who are you|what is farmwise|what can you do|are you ai|are you human|are you real|capabilities|what do you do|how can you help)/.test(q)) {
    return "I am the **FarmWise assistant**. I can help with:\n- **Crop suitability** — what to grow given your soil, season, and region\n- **Sowing & harvest timing** — for major crops\n- **Soil & irrigation** — pH, moisture, fertilizer, water schedule\n- **Pest & disease checks** — describe the symptom or upload a leaf photo\n- **Market timing** — when to sell, mandi rates, price awareness\n- **Government schemes** — basics on PM-KISAN, KCC, crop insurance";
  }

  // D. Yes/no warm-ups
  if (/(are you free|is this free|can you help me|can you talk|are you working|are you online)/.test(q)) {
    return "Yes — I am here, working, and free to use. What is your question?";
  }

  // E. Encouragement / worried
  if (/(losing|in debt|broke|bad yield|nothing works|frustrated|tired|give up|depressed|suicide|cant continue|cannot continue)/.test(q)) {
    return "That sounds really hard — many farmers feel the same. A few practical next steps:\n\n1. **Talk to your local KVK (Krishi Vigyan Kendra)** — free agronomist advice + subsidized inputs.\n2. **Restructure debt** via KCC; ask your bank manager about extending tenure.\n3. **Diversify next season** — adding one short-duration crop (60-90 days) cuts risk.\n4. **Enroll in PMFBY (crop insurance)** for next sowing — premium is small (1.5-5%).\n\nIf it ever feels overwhelming, please call **Kisan Call Centre 1800-180-1551** (free) or **iCall 9152987821** for emotional support.";
  }

  // F. Weather
  if (/(weather|will it rain|going to rain|monsoon|forecast|temperature today|is it hot|is it cold|kab barish|barish hogi)/.test(q)) {
    return `I do not have live weather access. For **${region}**, check the **IMD app** or AccuWeather for a rolling 7-day view.\n\nYour current Farm context shows: temp **${env.temperatureC}C**, humidity **${env.humidityPct}%**, wind **${env.windKph} kph**, rainfall **${env.rainfallMm} mm**. Update those in the right panel and I will use them in my answers.`;
  }

  // G. Soil pH / soil basics
  if (/(soil ph|ph of soil|what is ph|my soil is|soil acidic|soil alkaline|soil type|what is loam|what is clay|what is sandy|improve soil|test soil|soil test)/.test(q)) {
    return `Soil pH tells you how acidic or alkaline the soil is. Your context says **pH ${env.soilPh}**.\n\n- **5.5-6.5** — slightly acidic, good for most crops (rice, maize, potato, tomato).\n- **6.5-7.5** — neutral, suits wheat, mustard, lentil, chickpea.\n- **>7.8** — alkaline; add gypsum + organic matter to bring it down.\n- **<5.5** — too acidic; add lime + compost.\n\nFree soil test: request a **Soil Health Card** at your block agriculture office.`;
  }

  // H. Fertilizer / manure
  if (/(fertilizer|fertiliser|urea|dap|npk|manure|compost|vermicompost|khaad|gobar)/.test(q)) {
    return `Safe per-acre rule of thumb (verify with soil test):\n\n- **At sowing (basal)**: 20-40 kg DAP **or** 8-10 t farmyard manure / compost.\n- **Top-dress nitrogen**: 30-50 kg urea split in 2 doses (tillering + flowering).\n- **Cereals** (wheat, rice, maize) need more N; **pulses** (lentil, gram) fix their own N — skip N.\n- Avoid blanket spraying. Apply when soil is moist; never on dry soil.\n\nFor **${soil}** soil, organic matter (compost/FYM) is the single highest-ROI input.`;
  }

  // I. Irrigation
  if (/(irrigation|water schedule|how often|kab paani|paani dena|drip|flood irrigation|sprinkler|watering|how much water|should i water|water my crop|water my plant|water this week)/.test(q)) {
    return `For **${soil}** soil, water guidance:\n- **Sandy** — frequent + light (every 3-5 days, smaller volume).\n- **Loam** — moderate (every 6-8 days).\n- **Clay** — slow + deep (every 8-12 days).\n\n**Critical irrigation stages**: tillering, flowering, grain fill. Skip during heavy rain.\nYour soil moisture reading is **${env.soilMoisturePct}%** — below 30% is dry, above 60% is saturated.\nDrip saves 50%+ water vs flood; sprinkler is good for cereals on sandy land.`;
  }

  // J. Sowing timing per crop
  const crop = detectCrop(q);
  if (crop && /(best time|when to plant|when to sow|sowing time|planting time|kab boyein|kab lagayein|when should i plant)/.test(q)) {
    const window = SOWING_WINDOWS[crop];
    if (window) {
      return `${window}\n\nFor **${region}** in **${season}**, confirm with local rainfall start and soil moisture before sowing. If you share district-level climate, I can narrow this to a sowing week.`;
    }
  }

  // K. Storage / post-harvest (must precede harvest timing)
  if (/(storage|store grain|store wheat|store rice|post harvest|post-harvest|drying grain|godown|weevil|stored grain|ghun|sundi|how to store|store after harvest)/.test(q)) {
    return "Storage basics:\n\n- **Dry grain to <12% moisture** before storing (sun-dry 2-3 days; bite test - clean snap = ready).\n- **Clean dry godown**, raise sacks off floor with pallets, ensure ventilation.\n- **Aluminium phosphide tablet** or neem leaves keeps weevils out of stored wheat/rice.\n- Inspect every 15 days for hot spots; re-bag if you find clumping or live insects.\n- For onions/potato - cool, dark, well-aired storage; never stack >2 ft deep.";
  }

  // L. Harvest timing
  if (crop && /(harvest|when to cut|when to harvest|ready to cut|kab katega|pakna|days to maturity)/.test(q)) {
    const window = HARVEST_WINDOWS[crop];
    if (window) {
      return `${window}\n\nVerify with 10-plant random sampling before full-field harvest.`;
    }
  }

  // L. Pest indicators
  if (/(bug|insect|worm|caterpillar|holes in leaf|leaves chewed|sticky|aphid|whitefly|hopper|kira|kit|kaira|termite|deemak)/.test(q)) {
    return "Quick pest scout:\n\n1. **Holes / chewed edges** → caterpillars, beetles. Hand-pick early; spray neem oil (5 ml/L) or *Bacillus thuringiensis* if heavy.\n2. **Sticky leaves + black sooty mould** → aphids/whiteflies sucking sap. Spray neem oil or imidacloprid (read the label).\n3. **Hoppers (jumping insects)** → clear weeds; spray thiamethoxam.\n4. **Termites at root** → drench chlorpyrifos around base.\n\nAlways **scout before spraying** and avoid spraying during flowering hours so pollinators stay safe.";
  }

  // M. Disease indicators
  if (/(yellow leaf|yellow leaves|yellow spot|brown spot|white spot|powdery|wilting|wilt|rotting|rot|drying up|leaves falling|leaves curling|halo)/.test(q)) {
    return "Symptom interpreter:\n\n- **Lower-leaf yellowing** → likely **nitrogen deficiency**, not disease. Top-dress with urea.\n- **Brown rings + yellow halo** → **early/late blight** (fungal). Remove leaves, spray copper.\n- **White powder on top of leaf** → **powdery mildew**. Spray sulfur or potassium bicarbonate.\n- **Wilting only in afternoon** → **water stress**, not disease. Irrigate deeper.\n- **Leaves curling + sticky** → **virus** spread by whiteflies/aphids. Control the vector first.\n\nFor a confirmed diagnosis, open the **Crop Health** tab and upload a clear leaf photo.";
  }

  // N. Market / pricing
  if (/(price|mandi rate|kya rate|market rate|mandi|when to sell|kab bechu|best price|msp|sell|commodity)/.test(q)) {
    return `For **${region}**, three rules to time selling:\n\n1. **Track 4-week price trend** in your local mandi — falling trend means sell sooner; rising trend means hold (if storable).\n2. **Cost of storage** — if it costs ~Rs.20/quintal/month and price is not rising at least that fast, sell now.\n3. **Demand windows** — wheat/rice prices often firm up post-festival; vegetables crash within 7-10 days of peak harvest.\n\nOpen the **Market** tab to see commodity trends. Goal focus: ${goal}.`;
  }

  // P. Government schemes
  if (/(pm kisan|pmkisan|kisan samman|kcc|kisan credit|fasal bima|pmfby|crop insurance|subsidy|yojana|scheme|loan|sarkari)/.test(q)) {
    return "Major support schemes:\n\n- **PM-KISAN** — Rs.6,000/year direct transfer to small/marginal farmers. Apply at **pmkisan.gov.in** or your CSC.\n- **KCC (Kisan Credit Card)** — short-term crop loan up to Rs.3 lakh at 4% effective rate (timely repayment). Apply at any nationalized bank.\n- **PMFBY (Fasal Bima)** — crop insurance, premium 1.5-5% of sum insured. Enroll within 7 days of sowing via your bank or CSC.\n- **Soil Health Card** — free soil test at your block agriculture office.\n- **PM Kusum** — solar pump subsidy for irrigation, up to 60% support.";
  }

  // Q. Cost / profit
  if (/(cost|profit|budget|kharcha|kamana|kitna|expense|income|earn|loss)/.test(q)) {
    return `Rough per-acre numbers for **${region}** (verify locally):\n\n- **Wheat / rice / maize** — Rs.20,000-30,000 input cost; profit depends on MSP + yield.\n- **Pulses (lentil, gram)** — Rs.10,000-15,000, lower water need, often higher margin.\n- **Vegetables (tomato, onion)** — Rs.40,000-80,000 but volatile prices.\n\nAlways tally: seed + fertilizer + labour + water + harvest + transport.\nProfit = (yield x price) - total cost. If margin <15%, rethink the crop or price plan.`;
  }

  // R. Equipment / seeds
  if (/(tractor|machine|equipment|seed|beej|where to buy|kahaan se|accha seed|good seed|sprayer|thresher)/.test(q)) {
    return "Inputs guidance:\n\n- **Seeds** — buy certified seed from your block-level **KVK** or registered seed dealer. Reject loose / unmarked bags.\n- **Tools** — sub-divisional agri office offers subsidies on sprayers, drip kits, threshers (often 40-50% subsidized).\n- **Tractor rental** — apps like **CHC Farm Machinery** (govt) or HelloTractor offer hourly rentals if buying is not viable.";
  }

  // S. Crop choice / what to grow
  if (/(what should i grow|what to grow|should i grow|what crop|which crop|what to plant|what should i plant|best crop|good crop|crop suggestion|crop suitability|rotate|crop rotation|intercrop|grow this season|grow next season|konsi fasal|kya bouun)/.test(q)) {
    const notes = context.notes.trim()
      ? `Notes you added: _${context.notes.trim()}_`
      : "Add notes in **Farm context** (right panel) for more specific rotation ideas.";
    return `Here is a **structured starting point** for **${region}** (${season}, ${soil} soil, ~${context.farmSizeAcres} acres):\n\n1. **Shortlist** 3-5 crops that match your season length and water budget.\n2. **Score** them on heat/cold risk, soil fit, and local market outlet.\n3. **Validate** the top 1-2 in the **Crop Suitability** tab once you have weather + soil readings.\n\nQuick suggestions by season:\n- **Kharif / monsoon** — rice, maize, soybean, cotton, groundnut, jowar, bajra\n- **Rabi / winter** — wheat, mustard, chickpea, lentil, barley, potato, onion\n- **Zaid / summer** — moong, watermelon, fodder maize, vegetables (with irrigation)\n\nYour stated goal centers on **${goal}**. ${notes}`;
  }

  return `I am your **FarmWise advisor** (demo mode). I see you farm in **${region}** with **${soil}** soil, ~**${context.farmSizeAcres}** acres, **${season}** season, optimizing for **${goal}**.\n\nTry asking about:\n- **Crop suitability** and rotation\n- **Sowing / harvest timing** for any major crop\n- **Soil moisture, fertilizer, irrigation**\n- **Pest / disease symptoms**\n- **Market timing** and selling windows\n- **PM-KISAN, KCC, crop insurance** basics`;
}

export async function sendFarmAdvisorMessage(
  messages: ChatMessage[],
  context: FarmContext,
): Promise<string> {
  if (isMockAiEnabled()) {
    await new Promise((r) => setTimeout(r, 600));
    return mockAdvisorReply(messages, context);
  }

  const body: AdvisorRequestBody = {
    messages: messages.map((m) => ({ role: m.role, content: m.content })),
    context,
  };

  const res = await fetch(buildApiUrl(ADVISOR_PATH), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Advisor request failed (${res.status})`);
  }

  const data = (await res.json()) as AdvisorResponseBody;
  const reply = data.reply ?? data.message;
  if (!reply) throw new Error("Advisor response missing reply");
  return reply;
}
