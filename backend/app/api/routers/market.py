from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.market_agent import generate_market_forecast

router = APIRouter()

class MarketRequest(BaseModel):
    crop: str

@router.post("/forecast")
def market_forecast(req: MarketRequest):
    return generate_market_forecast(req.crop)
