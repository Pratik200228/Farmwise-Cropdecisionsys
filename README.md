# 🌾 FarmWise AI

> An AI-Powered Crop Decision Support System for Small-Scale Farmers

Small and family farmers make high-stakes decisions every day — which crops to plant, when to sell, whether that yellowing leaf is a disease or just stress. FarmWise AI brings intelligent, affordable decision support directly to the farmers who need it most, no outside consultant required.

---

## What It Does

FarmWise AI combines three tightly integrated capabilities into a single visual dashboard:

**Crop Suitability Analysis** — A goal-based AI agent analyzes real-time environmental parameters (temperature, wind speed, humidity, rainfall, and soil conditions) and ranks crops by suitability score, complete with confidence levels and seasonal rotation suggestions.

**Market Price Prediction** — Live integrations with USDA Agricultural Marketing Service and commodity market APIs surface price forecasts, historical comparisons, and optimal selling windows so farmers stop guessing and start planning.

**Crop Health Monitoring** — PlantVillage and Plantix APIs power early-warning disease detection, pest identification, and growth-stage tracking before problems become losses.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  React.js Dashboard                 │
│          (Chart.js / Recharts Visualizations)       │
└───────────────────────┬─────────────────────────────┘
                        │
              Python + FastAPI Backend
                        │
        ┌───────────────┼──────────────────┐
        ▼               ▼                  ▼
  Crop Suitability   Market Price      Crop Health
    AI Agent         Prediction        Monitoring
  (LLM API +        (USDA / AMS       (PlantVillage /
  OpenWeatherMap +   Commodity APIs)   Plantix APIs)
  NASA Soil Data)
```

The AI agent handles complex environmental reasoning. External APIs handle market and health data. Clear separation, reliable results.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React.js + Recharts / Chart.js |
| Backend | Python + FastAPI |
| AI Agent | LLM API (OpenAI / Anthropic) |
| Weather Data | OpenWeatherMap API |
| Soil Data | NASA Soil Moisture API |
| Market Data | USDA Agricultural Marketing Service API |
| Crop Health | PlantVillage API, Plantix API |
| Version Control | GitHub |

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- API keys for OpenWeatherMap, USDA AMS, and your chosen LLM provider

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env        # optional: set VITE_USE_MOCK_AI=false to use the backend above
npm run dev
```

Opens at `http://localhost:5173` (Vite dev server; `/api` is proxied to `http://localhost:8000`).

---

## Key Features

- **Ranked crop recommendations** with suitability scores based on live environmental data
- **Planting confidence levels** and seasonal rotation suggestions
- **Price forecasts** with optimal selling-window alerts
- **Disease and pest detection** with treatment recommendations
- **Early warning system** for emerging crop health issues
- **Simple visual dashboard** designed for farmers, not data scientists

---

## Project Structure

```
farmwise-ai/
├── backend/
│   ├── agents/
│   │   └── crop_suitability_agent.py   # Core AI agent logic
│   ├── integrations/
│   │   ├── market_api.py               # USDA / commodity price APIs
│   │   ├── health_api.py               # PlantVillage / Plantix APIs
│   │   └── weather_api.py              # OpenWeatherMap + NASA soil
│   ├── main.py                         # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CropRecommendations.jsx
│   │   │   ├── MarketPriceForecast.jsx
│   │   │   └── CropHealthMonitor.jsx
│   │   └── App.jsx
│   └── package.json
└── README.md
```

---

## Evaluation

The system is tested against simulated farm scenarios covering a range of environmental conditions and crop types. Evaluation criteria include:

- Accuracy of crop suitability rankings vs. agronomic ground truth
- Price forecast precision against actual market outcomes
- Disease detection recall rate in health monitoring scenarios
- Dashboard usability with non-technical users

Results are documented in the final project report.

---

## Team

| Member | Role |
|---|---|
| Swabhiman Paudel | Project Lead & AI Agent Developer |
| Prabin B.K. | Integration Lead & Data Engineer |
| Pratik Pokharel | UI/UX Designer & Front-End Developer |
| Sujal Thapa | System Architect & Documentation Lead |

---

## Course Context

This project was developed as part of a course project exploring applied AI agent design. The full proposal, architecture documentation, and evaluation report are available in the `/docs` folder.

---

*FarmWise AI — making agricultural intelligence accessible to every farmer, not just the largest ones.*
