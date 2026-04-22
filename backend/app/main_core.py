from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import suitability, market, health


app = FastAPI(title="FarmWise Core API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(suitability.router, prefix="/api/v1/agents/suitability", tags=["Agent 1 · Crop Suitability"])
app.include_router(market.router, prefix="/api/v1/market", tags=["Agent 2 · Market Intelligence"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Agent 3 · Crop Health (Text)"])


@app.get("/")
def read_root():
    return {"status": "Online", "role": "FarmWise Core API (no TensorFlow)", "routes": ["suitability", "market", "health text"]}

