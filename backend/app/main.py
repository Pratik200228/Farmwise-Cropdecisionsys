import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import suitability, market, health

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.agents import health_agent

    # CNN is initialized when this module is imported; log status at startup for deploy debugging
    logger.info("Crop health CNN: %s", health_agent.cnn_status_message())
    yield


app = FastAPI(title="FarmWise AI Custom Backend", lifespan=lifespan)

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

@app.get("/")
def read_root():
    return {
        "status": "Online",
        "agents": ["Crop Suitability", "Market Intelligence", "Crop Health"],
        "role": "FarmWise Custom Agent Engine — All 3 Agents Active"
    }
