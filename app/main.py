from fastapi import FastAPI
from app.services.ingestion import fetch_environmental_data

app = FastAPI(title="FarmWise AI Backend")

@app.get("/")
def read_root():
    return {"status": "Online"}

@app.post("/sync-environment")
def sync_data():
    # This calls the script we just wrote
    result = fetch_environmental_data()
    return resultfrom fastapi import FastAPI

app = FastAPI(title="FarmWise AI Backend")

@app.get("/")
def read_root():
    return {"status": "FarmWise AI System Online", "role": "Data Integration Layer"}

@app.get("/weather-sync")
def sync_weather():
    # This is where you will eventually call OpenWeatherMap
    return {"message": "Ready to ingest weather data"}
