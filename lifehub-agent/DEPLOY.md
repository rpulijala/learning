# Deployment Guide

## Overview

- **Backend**: FastAPI on Render (Python)
- **Frontend**: Next.js on Vercel

---

## Backend Deployment (Render)

### 1. Push to GitHub
```bash
git add .
git commit -m "Add deployment configs"
git push origin main
```

### 2. Create Render Web Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New** → **Web Service**
3. Connect your GitHub repo
4. Render will auto-detect `render.yaml` and configure:
   - **Name**: lifehub-agent-backend
   - **Runtime**: Python
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

### 3. Set Environment Variables
In Render dashboard, add:
- `OPENAI_API_KEY` = your OpenAI API key

### 4. Deploy
Click **Create Web Service**. Render will build and deploy.

### 5. Verify
```bash
# Health check
curl https://your-render-url.onrender.com/health

# Test streaming
curl -N -X POST https://your-render-url.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "provider": "openai"}'
```

---

## Frontend Deployment (Vercel)

### 1. Import to Vercel
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **Add New** → **Project**
3. Import your GitHub repo
4. Set **Root Directory** to `frontend`

### 2. Set Environment Variables
In Vercel project settings → Environment Variables:
- `NEXT_PUBLIC_BACKEND_URL` = `https://your-render-url.onrender.com`

### 3. Deploy
Click **Deploy**. Vercel will build and deploy the Next.js app.

### 4. Verify
1. Open your Vercel URL
2. Send a chat message
3. Verify streaming response works

---

## Environment Variables Summary

| Service  | Variable                  | Value                              |
|----------|---------------------------|------------------------------------|
| Render   | `OPENAI_API_KEY`          | Your OpenAI API key                |
| Vercel   | `NEXT_PUBLIC_BACKEND_URL` | `https://xxx.onrender.com`         |

---

## Local Development

```bash
# Terminal 1: Backend
cd lifehub-agent
uv run uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Frontend
cd lifehub-agent/frontend
npm run dev
```

Open http://localhost:3000

---

## Notes

- **Streaming**: SSE streaming works over HTTPS on Render
- **Cold starts**: Free tier on Render may have ~30s cold start
- **CORS**: Backend allows all origins for Vercel preview URLs
- **Ollama**: Only works locally (not available on Render)
