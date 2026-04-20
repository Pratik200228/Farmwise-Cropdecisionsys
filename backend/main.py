from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    AdvisorRequest,
    AdvisorResponse,
    HealthMonitoringRequest,
    HealthReport,
    MarketForecastRequest,
    MarketReport,
    SuitabilityAnalysisRequest,
    SuitabilityReport,
)
from app.services.advisor import build_advisor_reply
from app.services.health import build_health_report
from app.services.market import build_market_report
from app.services.suitability import analyze_crop_suitability


app = FastAPI(
    title="FarmWise AI API",
    version="0.1.0",
    description=(
        "Backend for the FarmWise AI crop decision support system. "
        "Implements one crop suitability AI workflow plus market and crop health service integrations."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/status")
def status() -> dict[str, str]:
    return {"status": "ok", "service": "farmwise-ai-api"}


@app.post("/api/v1/agents/suitability/analyze", response_model=SuitabilityReport)
def suitability_analyze(payload: SuitabilityAnalysisRequest) -> SuitabilityReport:
    return analyze_crop_suitability(payload.context, payload.candidateCrops)


@app.post("/api/v1/market/forecast", response_model=MarketReport)
def market_forecast(payload: MarketForecastRequest) -> MarketReport:
    return build_market_report(payload.crop)


@app.post("/api/v1/health/monitoring", response_model=HealthReport)
def health_monitoring(payload: HealthMonitoringRequest) -> HealthReport:
    return build_health_report(payload.crop, payload.growthStage, payload.symptomsNote)


@app.post("/api/v1/farm-advisor/chat", response_model=AdvisorResponse)
def farm_advisor_chat(payload: AdvisorRequest) -> AdvisorResponse:
    reply = build_advisor_reply(payload.messages, payload.context)
    return AdvisorResponse(reply=reply)
