# 🌾 FarmWise AI

> An AI-Powered Crop Decision Support System for Small-Scale Farmers

Small and family farmers make high-stakes decisions every day — which crops to plant, when to sell, and how to treat a sick leaf. **FarmWise AI** brings professional-grade agricultural intelligence directly to the farmers who need it most, combining expert knowledge with state-of-the-art machine learning.

---

## 🚀 What It Does

FarmWise AI combines four tightly integrated capabilities into a single visual dashboard:

**1. Crop Suitability Analysis**  
A hybrid AI agent analyzes 8 environmental parameters (N, P, K, Temp, Humidity, pH, Rainfall, Wind) and ranks crops by suitability score. We use a **Random Forest Classifier** blended with **Agronomic Expert Rules** to ensure grounded, realistic recommendations.

**2. Market Intelligence**  
A forensic pricing agent that uses a **Random Forest Regressor** (for primary grains) and **Seasonal Heuristic Modeling** (for other crops). It identifies optimal "Peak Selling Windows" to help farmers maximize their profit margins.

**3. Crop Health Monitor**  
A computer vision engine powered by **MobileNetV2 (PyTorch)** trained on the PlantVillage dataset (38 classes, ~95% val accuracy). Farmers take a photo of a leaf and the AI identifies the disease with an immediate treatment plan. Model weights are auto-downloaded from HuggingFace on first boot.

**4. Ask FarmWise (AI Chat)**  
A conversational advisor powered by **Groq (llama-3.3-70b)** with a 19-intent rule-based fallback. Answers questions about crop rotation, soil health, market timing, government schemes and more.

---

## 🏗️ Technical Architecture

- **Frontend**: React + TypeScript (Vite) hosted on **Vercel**
- **Backend**: FastAPI (Python) hosted on **Render.com**
- **Disease Model**: PyTorch MobileNetV2 — auto-downloaded from HuggingFace Hub on startup
- **LLM**: Groq API (llama-3.3-70b) with automatic rule-based fallback

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React, TypeScript, Vite, Recharts |
| **Backend** | Python, FastAPI, Uvicorn |
| **AI (Suitability)** | Scikit-learn (Random Forest Classifier) |
| **AI (Health)** | PyTorch + MobileNetV2 (PlantVillage, 38 classes) |
| **AI (Market)** | Scikit-learn (Random Forest Regressor + Seasonal Heuristics) |
| **AI (Chat)** | Groq API — llama-3.3-70b-versatile |
| **Deployment** | Vercel (Frontend), Render (Backend) |

---

## 🏁 Getting Started

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Environment Variables
Create `backend/.env`:
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key_here   # free at console.groq.com/keys
```
> The app works without any API keys — it falls back to the built-in rule-based advisor automatically.

---

## 📁 Project Structure

```
farmwise-ai/
├── backend/
│   ├── app/
│   │   ├── agents/      # AI logic (Suitability, Market, Health, Advisor)
│   │   ├── models/      # Trained .pkl and .pth model weights
│   │   └── api/         # FastAPI routers
│   ├── scripts/         # Model training scripts
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # React UI components
│   │   └── lib/         # API client (insightsApi.ts)
│   └── index.html
└── README.md
```

---

## 👥 Team

- **Swabhiman Paudel** — Project Lead & AI Agent Developer
- **Prabin B.K.** — Integration Lead & Data Engineer
- **Pratik Pokharel** — UI/UX Designer & Front-End Developer
- **Sujal Thapa** — System Architect & Documentation Lead

---

*FarmWise AI — making agricultural intelligence accessible to every farmer, not just the largest ones.*
