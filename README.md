# 🌾 FarmWise AI

**An AI-Powered Crop Decision Support System for Small-Scale Farmers**

## Overview

FarmWise AI helps small and family farmers make better crop selection decisions using one AI-driven crop suitability workflow plus market price and crop-health services, all through a simple visual dashboard.

## Architecture

- **Crop Suitability AI Agent** - Analyzes temperature, wind speed, humidity, rainfall, and soil conditions to rank crops by suitability score.
- **Market Price Service** - Exposes price forecasts and selling-window guidance through the FastAPI backend.
- **Crop Health Monitoring Service** - Returns health status, likely issues, and scouting guidance through the FastAPI backend.

## Tech Stack

| Layer        | Technology                        |
|--------------|-----------------------------------|
| Frontend     | React.js + Recharts               |
| Backend      | Python + FastAPI                  |
| AI Agent     | LLM API (OpenAI/Anthropic)        |
| Weather Data | OpenWeatherMap API                 |
| Soil Data    | NASA Soil Moisture                 |
| Market Data  | USDA Agricultural Marketing API   |
| Health Data  | PlantVillage / Plantix APIs       |

## Quick Start

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Available API Routes

- `POST /api/v1/agents/suitability/analyze`
- `POST /api/v1/market/forecast`
- `POST /api/v1/health/monitoring`
- `POST /api/v1/farm-advisor/chat`

## Team

| Member            | Role                                  |
|-------------------|---------------------------------------|
| Swabhiman Paudel  | Project Lead & AI Agent Developer     |
| Prabin B.K.       | Integration Lead & Data Engineer      |
| Pratik Pokharel   | UI/UX Designer & Front-End Developer  |
| Sujal Thapa       | System Architect & Documentation Lead |
