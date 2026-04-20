from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Environment(StrictModel):
    temperatureC: float
    humidityPct: float
    windKph: float
    rainfallMm: float
    soilPh: float
    soilMoisturePct: float


class FarmContext(StrictModel):
    region: str
    soilType: str
    farmSizeAcres: float
    primaryGoal: Literal["yield", "profit", "sustainability", "mixed"]
    season: str
    notes: str
    env: Environment


class CropSuitability(StrictModel):
    name: str
    score: int
    confidence: float
    fit: dict[str, int]
    rationale: str
    plantingWindow: str
    warnings: list[str]


class SuitabilityReport(StrictModel):
    context: FarmContext
    env: Environment
    summary: str
    crops: list[CropSuitability]
    rotationSuggestion: str
    generatedAt: int


class SuitabilityAnalysisRequest(StrictModel):
    context: FarmContext
    candidateCrops: list[str] | None = None


class PricePoint(StrictModel):
    label: str
    price: float
    forecast: bool


class SellingWindow(StrictModel):
    label: str
    window: str
    reason: str
    confidence: Literal["low", "medium", "high"]


class MarketReport(StrictModel):
    crop: str
    currency: str
    unit: str
    currentPrice: float
    seasonalMedian: float
    trend: list[PricePoint]
    windows: list[SellingWindow]
    summary: str
    source: str
    generatedAt: int


class MarketForecastRequest(StrictModel):
    crop: str


class HealthIssue(StrictModel):
    name: str
    kind: Literal["disease", "pest", "nutrient", "water"]
    severity: Literal["healthy", "watch", "moderate", "severe"]
    probability: float
    symptoms: list[str]
    treatment: list[str]
    preventive: list[str]


class HealthReport(StrictModel):
    crop: str
    growthStage: str
    healthScore: int
    overallSeverity: Literal["healthy", "watch", "moderate", "severe"]
    issues: list[HealthIssue]
    scoutingPlan: list[str]
    source: str
    generatedAt: int


class HealthMonitoringRequest(StrictModel):
    crop: str
    growthStage: str
    symptomsNote: str


class ChatMessage(StrictModel):
    role: Literal["user", "assistant", "system"]
    content: str


class AdvisorRequest(StrictModel):
    messages: list[ChatMessage]
    context: FarmContext


class AdvisorResponse(StrictModel):
    reply: str
