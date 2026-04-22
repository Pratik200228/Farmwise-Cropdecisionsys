from fastapi import FastAPI

from app.services.ingestion import fetch_environmental_data

app = FastAPI(title="FarmWise AI Backend")


@app.get("/")
def read_root():
    return {
        "status": "FarmWise AI System Online",
        "role": "Data Integration Layer",
    }


@app.get("/weather-sync")
def sync_weather():
    return {"message": "Ready to ingest weather data"}


@app.post("/sync-environment")
def sync_data():
    return fetch_environmental_data()
