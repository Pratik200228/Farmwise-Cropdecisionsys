import type { Environment, FarmContext } from "./farm";

/* -------------------------------------------------------------------------- */
/*  Crop Suitability AI agent (the single AI agent in FarmWise)               */
/* -------------------------------------------------------------------------- */

export type CropSuitability = {
  name: string;
  /** 0–100 suitability score */
  score: number;
  /** model confidence 0–1 */
  confidence: number;
  /** per-parameter fit, each 0–100 */
  fit: {
    temperature: number;
    humidity: number;
    wind: number;
    rainfall: number;
    soil: number;
  };
  rationale: string;
  /** suggested planting window, e.g. "Late May – Mid June" */
  plantingWindow: string;
  /** warnings / watch-outs for this crop under these conditions */
  warnings: string[];
};

export type SuitabilityReport = {
  context: FarmContext;
  env: Environment;
  /** overall narrative summary from the AI agent */
  summary: string;
  /** ranked (best-first) crop recommendations */
  crops: CropSuitability[];
  /** suggested next-season rotation given the focus crop */
  rotationSuggestion: string;
  generatedAt: number;
};

/* -------------------------------------------------------------------------- */
/*  Market Price Prediction API                                               */
/* -------------------------------------------------------------------------- */

export type PricePoint = {
  /** week label, e.g. "W-3" or "W+2" (negative = past, positive = forecast) */
  label: string;
  /** price per unit (USD/quintal) */
  price: number;
  /** true if this point is the model's forecast (vs historical) */
  forecast: boolean;
};

export type SellingWindow = {
  label: string;
  window: string;
  reason: string;
  confidence: "low" | "medium" | "high";
};

export type MarketReport = {
  crop: string;
  currency: string;
  unit: string;
  /** latest observed price */
  currentPrice: number;
  /** seasonal median for reference */
  seasonalMedian: number;
  /** 8-week trend, historical + forecast */
  trend: PricePoint[];
  /** sell-window recommendations */
  windows: SellingWindow[];
  summary: string;
  source: string;
  generatedAt: number;
};

/* -------------------------------------------------------------------------- */
/*  Crop Health Monitoring API                                                */
/* -------------------------------------------------------------------------- */

export type HealthSeverity = "healthy" | "watch" | "moderate" | "severe";

export type HealthIssue = {
  name: string;
  kind: "disease" | "pest" | "nutrient" | "water";
  severity: HealthSeverity;
  /** probability the model assigns, 0–1 */
  probability: number;
  symptoms: string[];
  treatment: string[];
  preventive: string[];
};

export type HealthReport = {
  crop: string;
  growthStage: string;
  /** overall plant health score 0–100 */
  healthScore: number;
  overallSeverity: HealthSeverity;
  /** ranked issues (most likely first) */
  issues: HealthIssue[];
  /** scouting plan for the next 7 days */
  scoutingPlan: string[];
  source: string;
  generatedAt: number;
};
