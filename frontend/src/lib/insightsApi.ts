import type { Environment, FarmContext } from "../types/farm";
import type {
  CropSuitability,
  HealthIssue,
  HealthReport,
  HealthSeverity,
  MarketReport,
  PricePoint,
  SellingWindow,
  SuitabilityReport,
} from "../types/insights";
import { buildApiUrl, isMockAiEnabled } from "./runtimeConfig";

/* -------------------------------------------------------------------------- */
/*  Shared helpers                                                            */
/* -------------------------------------------------------------------------- */

export const PATHS = {
  suitability: "/api/v1/agents/suitability/analyze",
  market: "/api/v1/market/forecast",
  health: "/api/v1/health/monitoring",
} as const;

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(buildApiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

function delay(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

function clamp(n: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, n));
}

/* -------------------------------------------------------------------------- */
/*  Crop catalog used by the mock suitability engine                          */
/* -------------------------------------------------------------------------- */

type CropProfile = {
  name: string;
  tempC: [number, number];
  humidityPct: [number, number];
  rainMm: [number, number];
  windKph: [number, number];
  phRange: [number, number];
  soilFit: Record<string, number>; // soilType → fit 0–100
  plantingHints: Record<string, string>;
};

const CROP_CATALOG: CropProfile[] = [
  {
    name: "Maize",
    tempC: [18, 32],
    humidityPct: [40, 80],
    rainMm: [120, 400],
    windKph: [0, 25],
    phRange: [5.5, 7.5],
    soilFit: { loam: 95, silt: 85, clay: 70, sandy: 60, black: 88 },
    plantingHints: {
      kharif: "Late May – Mid June",
      rabi: "Late October – Mid November",
      default: "At the start of the rainy season",
    },
  },
  {
    name: "Rice",
    tempC: [20, 35],
    humidityPct: [60, 95],
    rainMm: [200, 600],
    windKph: [0, 20],
    phRange: [5.0, 7.5],
    soilFit: { loam: 85, silt: 80, clay: 95, sandy: 40, black: 80 },
    plantingHints: {
      kharif: "Mid June – Mid July",
      default: "Once monsoon rains are reliable",
    },
  },
  {
    name: "Wheat",
    tempC: [10, 25],
    humidityPct: [40, 70],
    rainMm: [80, 250],
    windKph: [0, 30],
    phRange: [6.0, 7.5],
    soilFit: { loam: 92, silt: 85, clay: 80, sandy: 55, black: 88 },
    plantingHints: {
      rabi: "Early – Mid November",
      default: "Cool weather sowing window",
    },
  },
  {
    name: "Lentil",
    tempC: [15, 28],
    humidityPct: [35, 65],
    rainMm: [60, 180],
    windKph: [0, 30],
    phRange: [6.0, 7.8],
    soilFit: { loam: 90, silt: 80, clay: 60, sandy: 70, black: 85 },
    plantingHints: {
      rabi: "October – November",
      default: "After main cereal harvest",
    },
  },
  {
    name: "Tomato",
    tempC: [18, 30],
    humidityPct: [55, 80],
    rainMm: [100, 250],
    windKph: [0, 20],
    phRange: [6.0, 7.0],
    soilFit: { loam: 92, silt: 85, clay: 65, sandy: 60, black: 75 },
    plantingHints: {
      kharif: "June – July (with drainage)",
      rabi: "September – October",
      default: "Transplant 4–6 wks after sowing",
    },
  },
  {
    name: "Potato",
    tempC: [12, 24],
    humidityPct: [50, 80],
    rainMm: [100, 300],
    windKph: [0, 25],
    phRange: [5.5, 6.8],
    soilFit: { loam: 90, silt: 80, clay: 60, sandy: 80, black: 70 },
    plantingHints: {
      rabi: "Mid October – November",
      default: "Cool nights with moist soil",
    },
  },
  {
    name: "Mustard",
    tempC: [10, 25],
    humidityPct: [40, 70],
    rainMm: [60, 200],
    windKph: [0, 30],
    phRange: [6.0, 7.5],
    soilFit: { loam: 88, silt: 85, clay: 78, sandy: 65, black: 82 },
    plantingHints: {
      rabi: "October – November",
      default: "After monsoon, before frost",
    },
  },
  {
    name: "Soybean",
    tempC: [20, 32],
    humidityPct: [50, 80],
    rainMm: [150, 400],
    windKph: [0, 25],
    phRange: [6.0, 7.5],
    soilFit: { loam: 90, silt: 85, clay: 72, sandy: 65, black: 92 },
    plantingHints: {
      kharif: "Mid June – Early July",
      default: "Early rainy season",
    },
  },
];

function rangeFit(value: number, [lo, hi]: [number, number]): number {
  if (value >= lo && value <= hi) return 100;
  const span = hi - lo;
  const out = value < lo ? lo - value : value - hi;
  return clamp(100 - (out / Math.max(1, span)) * 120, 0, 100);
}

function scoreCrop(profile: CropProfile, env: Environment, soilType: string): CropSuitability {
  const temperature = rangeFit(env.temperatureC, profile.tempC);
  const humidity = rangeFit(env.humidityPct, profile.humidityPct);
  const rainfall = rangeFit(env.rainfallMm, profile.rainMm);
  const wind = rangeFit(env.windKph, profile.windKph);
  const soilTypeFit = profile.soilFit[soilType] ?? 60;
  const phFit = rangeFit(env.soilPh, profile.phRange);
  const soil = Math.round(soilTypeFit * 0.6 + phFit * 0.4);

  // weighted score — temperature + rainfall matter most for kharif-style logic
  const score = Math.round(
    temperature * 0.28 +
      rainfall * 0.25 +
      soil * 0.22 +
      humidity * 0.15 +
      wind * 0.1,
  );

  const confidence = clamp(
    0.55 +
      (Math.min(temperature, rainfall, soil) / 100) * 0.4 -
      (env.soilMoisturePct < 20 ? 0.05 : 0),
    0.4,
    0.98,
  );

  const warnings: string[] = [];
  if (temperature < 55) warnings.push("Temperature is outside the preferred band.");
  if (rainfall < 55) warnings.push("Rainfall support looks marginal — plan irrigation.");
  if (humidity < 55) warnings.push("Humidity is off — monitor transpiration stress.");
  if (soil < 55) warnings.push("Soil type / pH fit is weak — consider amendments.");
  if (wind < 55) warnings.push("Wind exposure is high — stake tall crops.");

  const bits: string[] = [];
  bits.push(
    `Temperature fit ${temperature}/100, rainfall fit ${rainfall}/100, soil fit ${soil}/100.`,
  );
  if (warnings.length === 0)
    bits.push("All key environmental factors sit inside the crop's comfort band.");

  return {
    name: profile.name,
    score,
    confidence,
    fit: { temperature, humidity, wind, rainfall, soil },
    rationale: bits.join(" "),
    plantingWindow:
      profile.plantingHints[
        (profile.plantingHints as Record<string, string>)[
          // pick by season if available
          ""
        ] ?? ""
      ] ??
      profile.plantingHints.default,
    warnings,
  };
}

function pickPlantingWindow(profile: CropProfile, season: string): string {
  return (
    profile.plantingHints[season.trim().toLowerCase()] ??
    profile.plantingHints.default
  );
}

function mockSuitability(context: FarmContext): SuitabilityReport {
  const env = context.env;
  const scored = CROP_CATALOG.map((profile) => {
    const s = scoreCrop(profile, env, context.soilType);
    s.plantingWindow = pickPlantingWindow(profile, context.season);
    return s;
  }).sort((a, b) => b.score - a.score);

  const top = scored[0];
  const secondary = scored[1];
  const region = context.region.trim() || "your region";
  const goalLabel =
    context.primaryGoal === "profit"
      ? "profit / margin"
      : context.primaryGoal === "yield"
        ? "yield maximization"
        : context.primaryGoal === "sustainability"
          ? "soil health and lower inputs"
          : "balanced yield and resilience";

  const summary = [
    `For **${region}** this **${context.season}** with **${context.soilType}** soil, the best fit is **${top.name}** at **${top.score}/100**.`,
    `**${secondary.name}** is a strong backup at ${secondary.score}/100.`,
    `Environmental read: ${env.temperatureC}°C avg, ${env.humidityPct}% humidity, ${env.rainfallMm} mm expected rainfall, soil pH ${env.soilPh}.`,
    `Goal priority: **${goalLabel}**.`,
  ].join(" ");

  const rotationSuggestion =
    top.name === "Maize" || top.name === "Rice"
      ? `Follow ${top.name} with a legume (lentil, soybean) next cycle to restore nitrogen.`
      : top.name === "Wheat"
        ? `Follow wheat with maize or soybean in the next cycle to break disease chains.`
        : top.name === "Tomato" || top.name === "Potato"
          ? `Rotate out of solanaceae next season — mustard or lentil breaks disease pressure.`
          : `Rotate with a cereal next cycle to balance soil nutrition.`;

  return {
    context,
    env,
    summary,
    crops: scored.slice(0, 6),
    rotationSuggestion,
    generatedAt: Date.now(),
  };
}

export async function runCropSuitabilityAgent(
  context: FarmContext,
): Promise<SuitabilityReport> {
  if (isMockAiEnabled()) {
    await delay(650);
    return mockSuitability(context);
  }
  return postJson<SuitabilityReport>(PATHS.suitability, { context });
}

/* -------------------------------------------------------------------------- */
/*  Market Price Prediction — mock                                            */
/* -------------------------------------------------------------------------- */

type MarketSeed = {
  base: number;
  unit: string;
  noise: number;
  drift: number;
};

const MARKET_SEEDS: Record<string, MarketSeed> = {
  Maize: { base: 42, unit: "USD/quintal", noise: 2.4, drift: 0.8 },
  Rice: { base: 68, unit: "USD/quintal", noise: 3.0, drift: 0.6 },
  Wheat: { base: 55, unit: "USD/quintal", noise: 2.0, drift: 0.4 },
  Lentil: { base: 98, unit: "USD/quintal", noise: 4.5, drift: 1.2 },
  Tomato: { base: 22, unit: "USD/quintal", noise: 3.8, drift: -0.3 },
  Potato: { base: 28, unit: "USD/quintal", noise: 2.2, drift: 0.5 },
  Mustard: { base: 72, unit: "USD/quintal", noise: 2.6, drift: 0.7 },
  Soybean: { base: 61, unit: "USD/quintal", noise: 2.8, drift: 0.9 },
};

function pseudoRandom(seedStr: string): () => number {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < seedStr.length; i++) {
    h = Math.imul(h ^ seedStr.charCodeAt(i), 16777619);
  }
  return () => {
    h ^= h << 13;
    h ^= h >>> 17;
    h ^= h << 5;
    return ((h >>> 0) % 10000) / 10000;
  };
}

function mockMarket(crop: string): MarketReport {
  const seed = MARKET_SEEDS[crop] ?? MARKET_SEEDS.Maize;
  const rnd = pseudoRandom(crop + ":v2");

  const trend: PricePoint[] = [];
  let p = seed.base;
  for (let w = -4; w <= 3; w++) {
    const shock = (rnd() - 0.5) * seed.noise;
    p = p + seed.drift * (w < 0 ? 0.6 : 1) + shock;
    trend.push({
      label: w < 0 ? `W${w}` : w === 0 ? "Now" : `W+${w}`,
      price: Math.round(p * 10) / 10,
      forecast: w >= 1,
    });
  }

  const currentPrice = trend.find((t) => t.label === "Now")!.price;
  const seasonalMedian = seed.base;
  const forecastPeak = Math.max(...trend.filter((t) => t.forecast).map((t) => t.price));
  const peakPoint = trend.find((t) => t.forecast && t.price === forecastPeak)!;

  const windows: SellingWindow[] = [
    {
      label: "Forward sale",
      window: "This week",
      reason:
        currentPrice > seasonalMedian
          ? `Spot is above the seasonal median (${seasonalMedian}). Hedge 20–30%.`
          : `Spot is below median — avoid heavy forward selling right now.`,
      confidence: currentPrice > seasonalMedian ? "medium" : "low",
    },
    {
      label: "Main harvest window",
      window: peakPoint.label,
      reason: `Forecast peak around ${peakPoint.label} at ${peakPoint.price} ${seed.unit.split("/")[0]}.`,
      confidence: forecastPeak > seasonalMedian * 1.05 ? "high" : "medium",
    },
    {
      label: "Hold & store",
      window: "Post-harvest",
      reason:
        seed.drift > 0
          ? "Prices are drifting up — storage may pay off if drying/pest cost stays low."
          : "Downward drift — don't hold unless storage cost is near zero.",
      confidence: seed.drift > 0 ? "medium" : "low",
    },
  ];

  const summary = [
    `**${crop}** spot is **${currentPrice} ${seed.unit}** vs seasonal median **${seasonalMedian}**.`,
    `8-week forecast peaks near **${peakPoint.label}** at **${peakPoint.price}**.`,
    seed.drift > 0
      ? "Short-term drift is positive — watch for demand-side surprises."
      : "Short-term drift is flat-to-down — prioritize early sales.",
  ].join(" ");

  return {
    crop,
    currency: "USD",
    unit: seed.unit,
    currentPrice,
    seasonalMedian,
    trend,
    windows,
    summary,
    source: "Mock forecaster (replace with USDA AMS / commodity API)",
    generatedAt: Date.now(),
  };
}

export async function fetchMarketForecast(crop: string): Promise<MarketReport> {
  if (isMockAiEnabled()) {
    await delay(450);
    return mockMarket(crop);
  }
  return postJson<MarketReport>(PATHS.market, { crop });
}

export function supportedMarketCrops(): string[] {
  return Object.keys(MARKET_SEEDS);
}

/* -------------------------------------------------------------------------- */
/*  Crop Health Monitoring — mock                                             */
/* -------------------------------------------------------------------------- */

type HealthRule = {
  keywords: RegExp;
  crop?: string;
  issue: Omit<HealthIssue, "probability">;
};

const HEALTH_RULES: HealthRule[] = [
  {
    keywords: /yellow(ing)?|chloros/i,
    issue: {
      name: "Nitrogen deficiency",
      kind: "nutrient",
      severity: "watch",
      symptoms: ["Uniform yellowing on older leaves", "Stunted new growth"],
      treatment: [
        "Side-dress with urea or compost tea",
        "Split applications — avoid one heavy dose",
      ],
      preventive: [
        "Include legumes in rotation",
        "Test soil N every 2 seasons",
      ],
    },
  },
  {
    keywords: /brown\s*spot|blight|lesion/i,
    issue: {
      name: "Early blight",
      kind: "disease",
      severity: "moderate",
      symptoms: [
        "Concentric brown rings on lower leaves",
        "Yellow halo around lesions",
      ],
      treatment: [
        "Remove and destroy infected leaves",
        "Apply copper-based fungicide at label rate",
      ],
      preventive: [
        "Mulch to limit soil splash",
        "Rotate out of solanaceae for 2 seasons",
      ],
    },
  },
  {
    keywords: /powder(y)?|white\s*film/i,
    issue: {
      name: "Powdery mildew",
      kind: "disease",
      severity: "moderate",
      symptoms: [
        "White powdery film on leaf surfaces",
        "Leaf curling in late stages",
      ],
      treatment: [
        "Sulfur dust or potassium bicarbonate spray",
        "Prune dense canopy for airflow",
      ],
      preventive: [
        "Water at the base, not overhead",
        "Space plants for ventilation",
      ],
    },
  },
  {
    keywords: /aphid|curl(ing)?\s*leaf|sticky/i,
    issue: {
      name: "Aphid infestation",
      kind: "pest",
      severity: "watch",
      symptoms: ["Curling new leaves", "Sticky honeydew + sooty mold"],
      treatment: [
        "Strong water jet on undersides",
        "Neem oil at dusk, repeat after 5 days",
      ],
      preventive: [
        "Encourage ladybugs and lacewings",
        "Avoid excess nitrogen which favors aphids",
      ],
    },
  },
  {
    keywords: /wilt(ing)?|droop/i,
    issue: {
      name: "Water stress or vascular wilt",
      kind: "water",
      severity: "watch",
      symptoms: ["Midday wilting", "No recovery overnight (if vascular)"],
      treatment: [
        "Deep, infrequent irrigation",
        "Dig a test plant — check roots & stem for browning",
      ],
      preventive: [
        "Mulch to stabilize soil moisture",
        "Avoid overhead watering at midday",
      ],
    },
  },
  {
    keywords: /hole|chew(ed)?|caterpillar|worm/i,
    issue: {
      name: "Caterpillar / leaf-feeding pest",
      kind: "pest",
      severity: "moderate",
      symptoms: ["Irregular holes in leaves", "Frass (droppings) on leaves"],
      treatment: [
        "Hand-pick in the evening",
        "Bt (Bacillus thuringiensis) spray on larvae",
      ],
      preventive: [
        "Trap crops (marigold, radish)",
        "Weekly scouting during warm, humid spells",
      ],
    },
  },
];

const HEALTHY_ISSUE: HealthIssue = {
  name: "No significant issue detected",
  kind: "disease",
  severity: "healthy",
  probability: 0.82,
  symptoms: ["Canopy color uniform", "No visible lesions or pests reported"],
  treatment: ["Continue weekly scouting"],
  preventive: [
    "Maintain mulch and spacing",
    "Log photos weekly for trend tracking",
  ],
};

function severityFromScore(score: number): HealthSeverity {
  if (score >= 85) return "healthy";
  if (score >= 70) return "watch";
  if (score >= 50) return "moderate";
  return "severe";
}

function mockHealth(
  crop: string,
  growthStage: string,
  symptomsNote: string,
): HealthReport {
  const note = symptomsNote.trim();
  const matched: HealthIssue[] = [];

  for (const rule of HEALTH_RULES) {
    if (rule.keywords.test(note)) {
      matched.push({ ...rule.issue, probability: 0.6 + Math.random() * 0.3 });
    }
  }

  // dedupe by name, keep first
  const seen = new Set<string>();
  const issues = matched.filter((i) => {
    if (seen.has(i.name)) return false;
    seen.add(i.name);
    return true;
  });

  const healthScore = issues.length === 0 ? 88 : Math.max(40, 92 - issues.length * 14);
  const overallSeverity = severityFromScore(healthScore);

  const finalIssues = issues.length > 0 ? issues : [HEALTHY_ISSUE];

  const scoutingPlan = [
    `Walk ${crop} rows every 3 days; photograph both leaf surfaces.`,
    `Focus on border rows & low, humid spots where pressure starts first.`,
    growthStage === "flowering" || growthStage === "fruiting"
      ? "Flowering/fruiting is peak-risk — scout every 2 days."
      : "Log growth stage weekly so the model can tune its expectations.",
    finalIssues.some((i) => i.kind === "disease")
      ? "If lesions spread to >15% of plants in 5 days, escalate to extension service."
      : "If an unknown pattern appears, send photos through the health API before spraying.",
  ];

  return {
    crop,
    growthStage,
    healthScore,
    overallSeverity,
    issues: finalIssues,
    scoutingPlan,
    source: "Mock health engine (replace with PlantVillage / Plantix API)",
    generatedAt: Date.now(),
  };
}

export async function runHealthMonitoring(
  crop: string,
  growthStage: string,
  symptomsNote: string,
): Promise<HealthReport> {
  if (isMockAiEnabled()) {
    await delay(550);
    return mockHealth(crop, growthStage, symptomsNote);
  }
  return postJson<HealthReport>(PATHS.health, { crop, growthStage, symptomsNote });
}
