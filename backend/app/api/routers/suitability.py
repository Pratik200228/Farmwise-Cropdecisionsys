from fastapi import APIRouter
from app.api.schemas import SuitabilityRequest, SuitabilityResponse
from app.agents.custom_agent import generate_suitability_report

router = APIRouter()

@router.post("/analyze", response_model=SuitabilityResponse)
def analyze_suitability(body: SuitabilityRequest):
    # This calls our custom Python mathematical engine instead of a third-party LLM
    result = generate_suitability_report(body.context)
    return result
