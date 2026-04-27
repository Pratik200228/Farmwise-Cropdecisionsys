import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from backend/.env on startup so LLM keys
# (ANTHROPIC_API_KEY / OPENAI_API_KEY) and other secrets are available
# to all routers via os.getenv(...). Falls back silently if .env is missing.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)

from app.api.routers import suitability, market, health, advisor  # noqa: E402

app = FastAPI(title="FarmWise AI Custom Backend")


@app.on_event("startup")
def _log_env_status() -> None:
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    has_openai = bool(os.getenv("OPENAI_API_KEY", "").strip())
    has_groq = bool(os.getenv("GROQ_API_KEY", "").strip())
    provider = os.getenv("LLM_PROVIDER", "anthropic").strip().lower()
    if has_anthropic or has_openai or has_groq:
        print(
            f"[env] LLM keys loaded -> anthropic={has_anthropic} openai={has_openai} "
            f"groq={has_groq} (LLM_PROVIDER={provider}). "
            "Chat will use the LLM with rule-based fallback."
        )
    else:
        print(
            "[env] No LLM keys found in environment / backend/.env. "
            "Chat will use the rule-based dispatcher only."
        )


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
