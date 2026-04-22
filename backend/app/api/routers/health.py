from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.agents.health_agent import generate_health_report, analyze_plant_image

router = APIRouter()

class HealthRequest(BaseModel):
    crop: str
    growthStage: str
    symptomsNote: str

@router.post("/monitoring")
def health_monitoring(req: HealthRequest):
    return generate_health_report(req.crop, req.growthStage, req.symptomsNote)

from fastapi import APIRouter, File, UploadFile, HTTPException, Form

@router.post("/scan")
async def health_scan(
    file: UploadFile = File(...),
    crop: Optional[str] = Form(None),
    stage: Optional[str] = Form(None)
):
    """Accepts an image file, runs it through CNN, and returns diagnosis."""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    
    contents = await file.read()
    result = analyze_plant_image(contents, crop_hint=crop, stage_hint=stage)
    if "error" in result:
        # Missing TF / model weights is a deployment/setup issue, not a random server bug
        raise HTTPException(status_code=503, detail=result["error"])
    
    return result
