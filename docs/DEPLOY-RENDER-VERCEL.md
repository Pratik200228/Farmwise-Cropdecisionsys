# Deploy FarmWise: Render (API) + Vercel (UI)

Do **Render first**, then Vercel (the UI needs the API’s public URL).

## 1. Push this repo to GitHub

Ensure `prabin-branch` (or `main` with the same tree) includes `backend/app/models/` (`.h5` / `.pkl` files).

## 2. Render — FastAPI backend

**Option A — Blueprint**

1. [render.com](https://render.com) → **New** → **Blueprint**.
2. Connect the repository; pick the branch you use.
3. Render reads `render.yaml` and creates **farmwise-api**.

**Option B — Web Service (manual)**

1. **New** → **Web Service** → connect repo.
2. **Root Directory:** `backend`
3. **Runtime:** Python 3.12
4. **Build command:** `pip install -r requirements.txt`
5. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **Health check path:** `/`

**After deploy**

- Copy the URL, e.g. `https://farmwise-api-xxxx.onrender.com` (HTTPS, no trailing slash).

**Check logs**

- On boot you should see: `Crop health CNN: Plant disease CNN ready (38 classes).`  
  If TensorFlow OOMs on **free** tier, open the service → **Upgrade** or try a paid instance with more RAM.

## 3. Vercel — React frontend

1. [vercel.com](https://vercel.com) → **Add New** → **Project** → import the same GitHub repo.
2. **Root Directory:** `frontend`
3. **Framework Preset:** Vite (or leave auto-detect).
4. **Build command:** `npm run build`  
   **Output directory:** `dist`

**Environment variables (Production)**

| Name | Value |
|------|--------|
| `VITE_USE_MOCK_AI` | `false` |
| `VITE_API_BASE_URL` | `https://YOUR-RENDER-SUBDOMAIN.onrender.com` |

Use the **exact** Render URL (no `/` at the end). Redeploy after saving env vars so Vite picks them up at build time.

## 4. Smoke test

- Open the Vercel URL; run crop suitability / market from the UI.
- Upload a leaf image: first request after idle can be slow on Render **free** (cold start).

## 5. Troubleshooting

| Symptom | What to check |
|--------|----------------|
| UI calls wrong host | `VITE_API_BASE_URL` in Vercel **Production** + **redeploy** |
| CORS errors | Backend already allows `*`; confirm API URL is correct |
| CNN 503 on scan | Render logs: TensorFlow install and `app/models` present in deploy |
| Build fails on Render | Logs: Python version, `pip` errors, out of memory |
