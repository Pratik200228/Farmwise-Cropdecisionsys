import time
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

# --- Inputs --- #
class Environment(BaseModel):
    temperatureC: float = Field(..., ge=-10, le=55)
    humidityPct: float = Field(..., ge=0, le=100)
    windKph: float = Field(..., ge=0, le=150)
    rainfallMm: float = Field(..., ge=0, le=2000)
    soilPh: float = Field(..., ge=1.0, le=14.0)
    soilMoisturePct: float = Field(..., ge=0, le=100)

class FarmContext(BaseModel):
    region: str = Field(..., min_length=2, max_length=100)
    soilType: str
    farmSizeAcres: float = Field(..., ge=0.0)
    primaryGoal: Literal["yield", "profit", "sustainability", "mixed"]
    season: str
    notes: str
    env: Environment

class SuitabilityRequest(BaseModel):
    context: FarmContext
    candidateCrops: Optional[List[str]] = None

class AdvisorMessage(BaseModel):
    role: Literal["user", "system", "assistant"]
    content: str

class AdvisorRequest(BaseModel):
    messages: List[AdvisorMessage]
    context: FarmContext
    # Optional per-request override so different UI features can use different providers.
    # If omitted, backend uses LLM_PROVIDER.
    provider: Optional[Literal["anthropic", "openai", "groq", "gemini"]] = None

class AdvisorResponse(BaseModel):
    reply: str

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
