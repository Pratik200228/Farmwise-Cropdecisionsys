# 🌾 FarmWise AI

> An AI-Powered Crop Decision Support System for Small-Scale Farmers

Small and family farmers make high-stakes decisions every day — which crops to plant, when to sell, and how to treat a sick leaf. **FarmWise AI** brings professional-grade agricultural intelligence directly to the farmers who need it most, combining expert knowledge with state-of-the-art machine learning.

---

## 🚀 What It Does

FarmWise AI combines three tightly integrated capabilities into a single visual dashboard:

**1. Crop Suitability Analysis**  
A hybrid AI agent analyzes 8 environmental parameters (N, P, K, Temp, Humidity, pH, Rainfall, Wind) and ranks crops by suitability score. We use a **Random Forest Classifier** blended with **Agronomic Expert Rules** to ensure grounded, realistic recommendations.

**2. Market Intelligence**  
A forensic pricing agent that uses a **Random Forest Regressor** (for primary grains) and **Seasonal Heuristic Modeling** (for other crops). It identifies optimal "Peak Selling Windows" to help farmers maximize their profit margins.

**3. Crop Health Monitor**  
A computer vision engine powered by **MobileNetV2 (CNN)**. Farmers take a photo of a leaf, and the AI identifies the disease and provides an immediate, professional treatment plan.

---

## 🏗️ Technical Architecture

We use a **Decoupled SaaS Architecture** to balance performance with AI compute requirements:

- **Frontend**: React + TypeScript (Vite) hosted on **Vercel**.
- **Backend**: FastAPI (Python) hosted on **Render.com**.
- **Specialized AI**: Local ML models (Scikit-Learn, TensorFlow/MobileNetV2) run on the backend to avoid the latency and cost of external LLM APIs.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React, TypeScript, Tailwind CSS, Recharts |
| **Backend** | Python, FastAPI, Uvicorn |
| **AI (Suitability)** | Scikit-learn (Random Forest Classifier) |
| **AI (Health)** | TensorFlow (MobileNetV2 CNN) |
| **AI (Market)** | Scikit-learn (Random Forest Regressor + Seasonal Heuristics) |
| **Deployment** | Vercel (Frontend), Render (Backend) |

---

## 🏁 Getting Started

### 1. Backend Setup (AI Brain)
Ensure you have Python 3.10+ installed.
```bash
cd backend
python -m venv .venv
source .env/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### 2. Frontend Setup (Dashboard)
Ensure you have Node.js 18+ installed.
```bash
cd frontend
npm install
npm run dev
```

### 3. Environment Configuration
Create a `.env` in the `frontend/` folder:
```env
VITE_API_BASE_URL=https://your-backend-on-render.com
VITE_USE_MOCK_AI=false
```

---

## 📁 Project Structure

```
farmwise-ai/
├── backend/
│   ├── app/
│   │   ├── agents/      # The AI logic (Suitability, Market, Health)
│   │   ├── models/      # Trained .pkl and .h5 files
│   │   └── api/         # FastAPI Routers
│   └── main.py          # Entry point
├── frontend/
│   ├── src/
│   │   ├── components/  # Dashboard UI Components
│   │   └── lib/         # API connection logic (insightsApi.ts)
│   └── vercel.json      # Proxy configuration
└── README.md
```

---

## 👥 Team

- **Swabhiman Paudel**: Project Lead & AI Agent Developer
- **Prabin B.K.**: Integration Lead & Data Engineer
- **Pratik Pokharel**: UI/UX Designer & Front-End Developer
- **Sujal Thapa**: System Architect & Documentation Lead

---

*FarmWise AI — making agricultural intelligence accessible to every farmer, not just the largest ones.*
