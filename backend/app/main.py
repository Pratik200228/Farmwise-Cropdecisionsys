from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import suitability, market, health, advisor

app = FastAPI(title="FarmWise AI Custom Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    suitability.router, 
    prefix="/api/v1/agents/suitability", 
    tags=["Agent 1 · Crop Suitability"]
)

app.include_router(
    market.router,
    prefix="/api/v1/market",
    tags=["Agent 2 · Market Intelligence"]
)

app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["Agent 3 · Crop Health"]
)

app.include_router(
    advisor.router,
    prefix="/api/v1/farm-advisor",
    tags=["Farm Advisor Chat"]
)

@app.get("/")
def read_root():
    return {
        "status": "Online",
        "agents": ["Crop Suitability", "Market Intelligence", "Crop Health"],
        "role": "FarmWise Custom Agent Engine — All 3 Agents Active"
    }
