import type { FarmContext } from "./farm";

/** Three agent families required for multi-agent season planning */
export type AgentKind = "suitability" | "market" | "health" | "planner";

export type SuitabilityRankedCrop = {
  name: string;
  score: number;
  rationale: string;
};

/** Agent 1 — environmental / agronomic suitability (weather, soil, season) */
export type SuitabilityAgentResult = {
  agent: "suitability";
  environmentalSummary: string;
  rankedCrops: SuitabilityRankedCrop[];
};

/** Agent 2 — market & price intelligence (USDA / commodity context) */
export type MarketAgentResult = {
  agent: "market";
  cropFocus: string;
  outlook: string;
  suggestedWindows: string[];
  riskNotes: string;
};

/** Agent 3 — crop health & scouting (disease / pest / monitoring) */
export type HealthAgentResult = {
  agent: "health";
  cropFocus: string;
  scoutingPlan: string[];
  priorityRisks: string[];
  whenToEscalate: string;
};

export type OrchestrationStepStatus = "idle" | "running" | "done" | "error";

export type OrchestrationStep = {
  kind: AgentKind;
  label: string;
  status: OrchestrationStepStatus;
  error?: string;
};

/** Outcome of the complex task: three agent types + merged recommendation */
export type MultiAgentSeasonPlan = {
  context: FarmContext;
  focusCrop: string;
  suitability: SuitabilityAgentResult;
  market: MarketAgentResult;
  health: HealthAgentResult;
  integratedSummary: string;
  steps: OrchestrationStep[];
};

export type SuitabilityRequestBody = {
  context: FarmContext;
  candidateCrops?: string[];
};

export type MarketRequestBody = {
  context: FarmContext;
  cropFocus: string;
  suitabilityTopScore?: number;
};

export type HealthRequestBody = {
  context: FarmContext;
  cropFocus: string;
  symptomsNote?: string;
};
