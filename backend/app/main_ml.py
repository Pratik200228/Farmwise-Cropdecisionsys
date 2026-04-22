import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import health_scan

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Importing this module loads TF + weights (see init_cnn()).
    from app.agents import health_agent

    logger.info("Crop health CNN: %s", health_agent.cnn_status_message())
    yield


app = FastAPI(title="FarmWise ML API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_scan.router, prefix="/api/v1/health", tags=["Agent 3 · Crop Health (Scan)"])


@app.get("/")
def read_root():
    return {"status": "Online", "role": "FarmWise ML API (TensorFlow)", "routes": ["health scan"]}

