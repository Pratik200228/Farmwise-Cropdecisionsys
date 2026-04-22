from fastapi import APIRouter, File, UploadFile, HTTPException

from app.agents.health_agent import analyze_plant_image

router = APIRouter()


@router.post("/scan")
async def health_scan(file: UploadFile = File(...)):
    """Accepts an image file, runs it through CNN, and returns diagnosis."""
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    contents = await file.read()
    result = analyze_plant_image(contents)
    if "error" in result:
        # Missing TF / model weights is a deployment/setup issue, not a random server bug
        raise HTTPException(status_code=503, detail=result["error"])

    return result

