import type { FarmContext } from "../types/farm";
import type {
  HealthAgentResult,
  HealthRequestBody,
  MarketAgentResult,
  MarketRequestBody,
  MultiAgentSeasonPlan,
  OrchestrationStep,
  SuitabilityAgentResult,
  SuitabilityRequestBody,
} from "../types/agents";

const PATHS = {
  suitability: "/api/v1/agents/suitability/analyze",
  market: "/api/v1/agents/market/forecast",
  health: "/api/v1/agents/health/monitoring-plan",
} as const;

function apiBase(): string {
  const raw = import.meta.env.VITE_API_BASE_URL;
  if (raw && raw.length > 0) return raw.replace(/\/$/, "");
  return "";
}

function useMock(): boolean {
  return import.meta.env.VITE_USE_MOCK_AI === "true";
}

function url(path: string): string {
  const base = apiBase();
  return base ? `${base}${path}` : path;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(url(path), {
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

function mockDelay(ms = 450): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

function mockSuitability(context: FarmContext): SuitabilityAgentResult {
  const region = context.region.trim() || "your region";
  const season = context.season || "this season";
  return {
    agent: "suitability",
    environmentalSummary: `For **${region}**, **${season}** on **${context.soilType}** soil, the agent weights temperature stress, rainfall reliability, and soil water holding capacity. Goal: **${context.primaryGoal}**.`,
    rankedCrops: [
      {
        name: "Maize",
        score: 88,
        rationale: "Strong fit for warm-season growth and local demand; matches typical kharif moisture.",
      },
      {
        name: "Lentil",
        score: 76,
        rationale: "Good rotation option if drainage is adequate; watch terminal heat at pod fill.",
      },
      {
        name: "Tomato",
        score: 69,
        rationale: "Profitable but higher disease pressure; needs tight scouting (see Health agent).",
      },
    ],
  };
}

function mockMarket(context: FarmContext, crop: string, topScore: number): MarketAgentResult {
  return {
    agent: "market",
    cropFocus: crop,
    outlook: `**${crop}** basis and wholesale trends for **${context.region.trim() || "the area"}** favor staggered sales when local supply peaks. Suitability score **${topScore}** supports committing acreage if storage/logistics match.`,
    suggestedWindows: [
      "Pre-harvest: hedge or forward-sell 20–30% if price > seasonal median.",
      "Main harvest: 2-week sell band around historical local peak (USDA series when live).",
      "Post-harvest: only if drying/storage cost < expected basis recovery.",
    ],
    riskNotes:
      "Volatile transport and fuel costs can erase margin—pair with the Health agent’s loss-prevention plan.",
  };
}

function mockHealth(
  context: FarmContext,
  crop: string,
  symptomsNote?: string,
): HealthAgentResult {
  const intro = symptomsNote?.trim()
    ? `**Reported symptoms:** _${symptomsNote.trim()}_ — prioritize ruling out nutrition/water stress before disease ID.`
    : null;
  return {
    agent: "health",
    cropFocus: crop,
    scoutingPlan: [
      ...(intro ? [intro] : []),
      `Weekly canopy walk for **${crop}**; photograph both upper and lower leaf surfaces.`,
      "Track growth stage vs. weather: humidity + warmth triggers fungal cycles.",
      "Border rows and low spots first—early infestation often starts there.",
      "If irrigation: check for root-zone saturation vs. crop water demand.",
    ],
    priorityRisks:
      context.soilType === "clay"
        ? ["Root / crown rots under wet feet", "Nutrient tie-up; verify tissue test if yellowing"]
        : ["Mite / thrips in dry spells", "Wind-driven fungal spores after storms"],
    whenToEscalate:
      "Escalate to lab or extension if >15% of plants show progressive lesions within 5 days or if yield-bearing tissue is affected.",
  };
}

function mergeSummary(
  context: FarmContext,
  crop: string,
  s: SuitabilityAgentResult,
  m: MarketAgentResult,
  h: HealthAgentResult,
  symptomsNote?: string,
): string {
  const top = s.rankedCrops[0];
  const symptomLine = symptomsNote?.trim()
    ? `\n**Symptoms noted:** _${symptomsNote.trim()}_ (folded into health agent plan).`
    : "";
  return [
    `**Integrated plan** for **${crop}** (${context.season}, ${context.soilType} soil, goal: **${context.primaryGoal}**).`,
    "",
    `1. **Suitability** — ${top?.name ?? crop} leads at **${top?.score ?? 0}/100**: _${top?.rationale ?? "See ranked list below."}_`,
    `2. **Market** — ${m.outlook.replace(/\*\*/g, "")}`,
    `3. **Health** — Lead risks: ${h.priorityRisks.join("; ")}. ${h.whenToEscalate}`,
    symptomLine,
  ].join("\n");
}

export async function callSuitabilityAgent(
  body: SuitabilityRequestBody,
): Promise<SuitabilityAgentResult> {
  if (useMock()) {
    await mockDelay();
    return mockSuitability(body.context);
  }
  return postJson<SuitabilityAgentResult>(PATHS.suitability, body);
}

export async function callMarketAgent(body: MarketRequestBody): Promise<MarketAgentResult> {
  if (useMock()) {
    await mockDelay();
    return mockMarket(body.context, body.cropFocus, body.suitabilityTopScore ?? 0);
  }
  return postJson<MarketAgentResult>(PATHS.market, body);
}

export async function callHealthAgent(body: HealthRequestBody): Promise<HealthAgentResult> {
  if (useMock()) {
    await mockDelay();
    return mockHealth(body.context, body.cropFocus, body.symptomsNote);
  }
  return postJson<HealthAgentResult>(PATHS.health, body);
}

const STEP_LABELS: Record<string, string> = {
  suitability: "Agent 1 — Crop suitability (environment & soil)",
  market: "Agent 2 — Market intelligence (price & timing)",
  health: "Agent 3 — Crop health (scouting & risk)",
};

function initSteps(): OrchestrationStep[] {
  return (["suitability", "market", "health"] as const).map((kind) => ({
    kind,
    label: STEP_LABELS[kind],
    status: "idle" as const,
  }));
}

/**
 * Complex task: produce a season plan by orchestrating **three different AI agents**.
 * Suitability runs first (picks focus crop); Market and Health run in parallel on that crop.
 */
export async function runMultiAgentSeasonPlan(
  context: FarmContext,
  onStepUpdate?: (steps: OrchestrationStep[]) => void,
  symptomsNote?: string,
): Promise<MultiAgentSeasonPlan> {
  let steps = initSteps();

  const update = (kind: keyof typeof PATHS, status: OrchestrationStep["status"], err?: string) => {
    steps = steps.map((s) =>
      s.kind === kind ? { ...s, status, error: err } : s,
    );
    onStepUpdate?.(steps);
  };

  update("suitability", "running");
  let suitability: SuitabilityAgentResult;
  try {
    suitability = await callSuitabilityAgent({ context });
    update("suitability", "done");
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Suitability agent failed";
    update("suitability", "error", msg);
    throw new Error(msg);
  }

  const focusCrop = suitability.rankedCrops[0]?.name ?? "Maize";
  const topScore = suitability.rankedCrops[0]?.score ?? 0;

  update("market", "running");
  update("health", "running");

  const marketReq = callMarketAgent({
    context,
    cropFocus: focusCrop,
    suitabilityTopScore: topScore,
  });
  const healthReq = callHealthAgent({
    context,
    cropFocus: focusCrop,
    symptomsNote: symptomsNote?.trim() || undefined,
  });

  const settled = await Promise.allSettled([marketReq, healthReq]);

  let market: MarketAgentResult | undefined;
  let health: HealthAgentResult | undefined;
  const errs: string[] = [];

  if (settled[0].status === "fulfilled") {
    market = settled[0].value;
    update("market", "done");
  } else {
    const msg =
      settled[0].reason instanceof Error
        ? settled[0].reason.message
        : "Market agent failed";
    errs.push(msg);
    update("market", "error", msg);
  }

  if (settled[1].status === "fulfilled") {
    health = settled[1].value;
    update("health", "done");
  } else {
    const msg =
      settled[1].reason instanceof Error
        ? settled[1].reason.message
        : "Health agent failed";
    errs.push(msg);
    update("health", "error", msg);
  }

  if (!market || !health) {
    throw new Error(errs.join(" · ") || "Market or health agent failed");
  }

  const integratedSummary = mergeSummary(
    context,
    focusCrop,
    suitability,
    market,
    health,
    symptomsNote,
  );

  return {
    context,
    focusCrop,
    suitability,
    market,
    health,
    integratedSummary,
    steps,
  };
}
