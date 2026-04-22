from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.health_text_agent import generate_health_report

router = APIRouter()

class HealthRequest(BaseModel):
    crop: str
    growthStage: str
    symptomsNote: str

@router.post("/monitoring")
def health_monitoring(req: HealthRequest):
    return generate_health_report(req.crop, req.growthStage, req.symptomsNote)
