from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import suitability

app = FastAPI(title="FarmWise AI Custom Backend")

# Configure CORS so the Vite frontend (usually on port 5173/3000) can talk to us (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect the custom python agent router
app.include_router(
    suitability.router, 
    prefix="/api/v1/agents/suitability", 
    tags=["Suitability Agent"]
)

@app.get("/")
def read_root():
    return {
        "status": "Online",
        "role": "FarmWise Custom Agent Engine"
    }
