# 🌾 FarmWise AI

**An AI-Powered Crop Decision Support System for Small-Scale Farmers**

## Overview

FarmWise AI helps small and family farmers make better crop selection decisions using AI-driven environmental analysis, market price predictions, and crop health monitoring — all through a simple visual dashboard.

## Architecture

- **Crop Suitability AI Agent** — Analyzes temperature, wind speed, humidity, rainfall, and soil conditions to rank crops by suitability score.
- **Market Price Prediction API** — Integrates with USDA/commodity APIs for price forecasts and optimal selling windows.
- **Crop Health Monitoring API** — Uses PlantVillage/Plantix APIs for disease detection, pest identification, and growth tracking.

## Tech Stack

| Layer        | Technology                        |
|--------------|-----------------------------------|
| Frontend     | React.js + Recharts               |
| Backend      | Python + FastAPI                   |
| AI Agent     | LLM API (OpenAI/Anthropic)        |
| Weather Data | OpenWeatherMap API                 |
| Soil Data    | NASA Soil Moisture                 |
| Market Data  | USDA Agricultural Marketing API   |
| Health Data  | PlantVillage / Plantix APIs       |

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start
```

## Team

| Member            | Role                                  |
|-------------------|---------------------------------------|
| Swabhiman Paudel  | Project Lead & AI Agent Developer     |
| Prabin B.K.       | Integration Lead & Data Engineer      |
| Pratik Pokharel   | UI/UX Designer & Front-End Developer  |
| Sujal Thapa       | System Architect & Documentation Lead |
