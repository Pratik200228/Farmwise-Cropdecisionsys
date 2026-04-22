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
import type { HealthReport, MarketReport, SuitabilityReport } from "../types/insights";
import {
  fetchMarketForecast,
  runCropSuitabilityAgent,
  runHealthMonitoring,
} from "./insightsApi";

function inferGrowthStage(context: FarmContext): string {
  const raw = `${context.season} ${context.notes}`.toLowerCase();
  if (raw.includes("seed")) return "seedling";
  if (raw.includes("flower")) return "flowering";
  if (raw.includes("fruit")) return "fruiting";
  if (raw.includes("matur")) return "maturity";
  return "vegetative";
}

function mapSuitability(report: SuitabilityReport): SuitabilityAgentResult {
  return {
    agent: "suitability",
    environmentalSummary: report.summary,
    rankedCrops: report.crops.slice(0, 3).map((crop) => ({
      name: crop.name,
      score: crop.score,
      rationale: crop.rationale,
    })),
  };
}

function mapMarket(report: MarketReport): MarketAgentResult {
  const riskNotes =
    report.currentPrice >= report.seasonalMedian
      ? "Current price is above the seasonal median; protect margin if transport and storage costs are rising."
      : "Current price is below the seasonal median; avoid forced sales unless storage, cash flow, or spoilage risk is high.";

  return {
    agent: "market",
    cropFocus: report.crop,
    outlook: report.summary,
    suggestedWindows: report.windows.map(
      (window) =>
        `${window.label} (${window.window}) - ${window.reason} [${window.confidence} confidence]`,
    ),
    riskNotes,
  };
}

function mapHealth(report: HealthReport, symptomsNote?: string): HealthAgentResult {
  const priorityRisks = report.issues.map((issue) =>
    issue.name === "No significant issue detected"
      ? issue.name
      : `${issue.name} (${Math.round(issue.probability * 100)}% likely)`,
  );

  const scoutingPlan = symptomsNote?.trim()
    ? [
        `Reported symptoms: ${symptomsNote.trim()}. Validate this against field photos before treatment.`,
        ...report.scoutingPlan,
      ]
    : report.scoutingPlan;

  return {
    agent: "health",
    cropFocus: report.crop,
    scoutingPlan,
    priorityRisks,
    whenToEscalate:
      report.scoutingPlan[report.scoutingPlan.length - 1] ??
      "Escalate if symptoms spread quickly or affect yield-bearing tissue.",
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
  const report = await runCropSuitabilityAgent(body.context);
  return mapSuitability(report);
}

export async function callMarketAgent(body: MarketRequestBody): Promise<MarketAgentResult> {
  const report = await fetchMarketForecast(body.cropFocus);
  return mapMarket(report);
}

export async function callHealthAgent(body: HealthRequestBody): Promise<HealthAgentResult> {
  const report = await runHealthMonitoring(
    body.cropFocus,
    inferGrowthStage(body.context),
    body.symptomsNote ?? "",
  );
  return mapHealth(report, body.symptomsNote);
}

const STEP_LABELS: Record<string, string> = {
  suitability: "Crop Suitability AI Agent",
  market: "Market Price Service",
  health: "Crop Health Service",
};

function initSteps(): OrchestrationStep[] {
  return (["suitability", "market", "health"] as const).map((kind) => ({
    kind,
    label: STEP_LABELS[kind],
    status: "idle" as const,
  }));
}

/**
 * Build an integrated season plan from the Crop Suitability AI agent plus the
 * market and crop-health service layers described in the project proposal.
 */
export async function runMultiAgentSeasonPlan(
  context: FarmContext,
  onStepUpdate?: (steps: OrchestrationStep[]) => void,
  symptomsNote?: string,
): Promise<MultiAgentSeasonPlan> {
  let steps = initSteps();

  const update = (
    kind: OrchestrationStep["kind"],
    status: OrchestrationStep["status"],
    err?: string,
  ) => {
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
    const msg = e instanceof Error ? e.message : "Suitability analysis failed";
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
        : "Market service failed";
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
        : "Health service failed";
    errs.push(msg);
    update("health", "error", msg);
  }

  if (!market || !health) {
    throw new Error(errs.join(" · ") || "Market or health service failed");
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
