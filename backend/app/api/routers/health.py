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

@router.post("/scan")
async def health_scan(file: UploadFile = File(...)):
    """Accepts an image file, runs it through CNN, and returns diagnosis."""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File provided is not an image.")
    
    contents = await file.read()
    result = analyze_plant_image(contents)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result
