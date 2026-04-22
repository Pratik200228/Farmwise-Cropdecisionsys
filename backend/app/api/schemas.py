import time
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

# --- Inputs --- #
class Environment(BaseModel):
    temperatureC: float
    humidityPct: float
    windKph: float
    rainfallMm: float
    soilPh: float
    soilMoisturePct: float

class FarmContext(BaseModel):
    region: str
    soilType: str
    farmSizeAcres: float
    primaryGoal: Literal["yield", "profit", "sustainability", "mixed"]
    season: str
    notes: str
    env: Environment

class SuitabilityRequest(BaseModel):
    context: FarmContext
    candidateCrops: Optional[List[str]] = None

# --- Outputs --- #
class FitScores(BaseModel):
    temperature: int
    humidity: int
    wind: int
    rainfall: int
    soil: int

class CropSuitability(BaseModel):
    name: str
    score: int
    confidence: float
    fit: FitScores
    rationale: str
    plantingWindow: str
    warnings: List[str]

class SuitabilityRankedCrop(BaseModel):
    name: str
    score: int
    rationale: str

class SuitabilityResponse(BaseModel):
    # Field mapping for multiAgentApi.ts expectations
    agent: str = "suitability"
    environmentalSummary: str
    rankedCrops: List[SuitabilityRankedCrop]

    # Field mapping for insightsApi.ts expectations
    context: FarmContext
    env: Environment
    summary: str
    crops: List[CropSuitability]
    rotationSuggestion: str
    generatedAt: int = Field(default_factory=lambda: int(time.time() * 1000))
