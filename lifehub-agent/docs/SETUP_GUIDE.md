# LifeHub Agent - Installation & Setup Guide

Complete step-by-step guide to install and run LifeHub Agent on **macOS** and **Windows**.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Clone the Repository](#clone-the-repository)
3. [Backend Setup](#backend-setup)
4. [Frontend Setup](#frontend-setup)
5. [Running the Application](#running-the-application)
6. [Optional: Ollama Setup (Fully Local)](#optional-ollama-setup-fully-local)
7. [Optional: MCP Integration (Web Search)](#optional-mcp-integration-web-search)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 18+ | Frontend runtime |
| **uv** | Latest | Python package manager |
| **Git** | Latest | Clone repository |

### API Keys (Choose One)

| Option | What You Need |
|--------|---------------|
| **OpenAI (Recommended)** | OpenAI API key from [platform.openai.com](https://platform.openai.com/api-keys) |
| **Fully Local** | Ollama installed (no API key needed) |

---

## Installation by Platform

### macOS

#### 1. Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Install Python 3.11+
```bash
brew install python@3.11
```

Verify installation:
```bash
python3 --version
# Should show Python 3.11.x or higher
```

#### 3. Install Node.js 18+
```bash
brew install node@18
```

Verify installation:
```bash
node --version
# Should show v18.x.x or higher

npm --version
# Should show 9.x.x or higher
```

#### 4. Install uv (Python package manager)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal or run:
```bash
source ~/.zshrc
```

Verify installation:
```bash
uv --version
```

---

### Windows

#### 1. Install Python 3.11+

**Option A: Microsoft Store (Easiest)**
- Open Microsoft Store
- Search for "Python 3.11"
- Click "Get" to install

**Option B: Official Installer**
- Download from [python.org/downloads](https://www.python.org/downloads/)
- **Important**: Check "Add Python to PATH" during installation

Verify installation (open PowerShell or Command Prompt):
```powershell
python --version
# Should show Python 3.11.x or higher
```

#### 2. Install Node.js 18+

- Download LTS version from [nodejs.org](https://nodejs.org/)
- Run the installer (use default settings)

Verify installation:
```powershell
node --version
# Should show v18.x.x or higher

npm --version
# Should show 9.x.x or higher
```

#### 3. Install uv (Python package manager)

**PowerShell (Run as Administrator):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart PowerShell, then verify:
```powershell
uv --version
```

#### 4. Install Git (if not installed)

- Download from [git-scm.com](https://git-scm.com/download/win)
- Run installer with default settings

---

## Clone the Repository

### macOS
```bash
cd ~/projects  # or your preferred directory
git clone git@github.com:rpulijala/learning.git
cd lifehub-agent
```

### Windows (PowerShell)
```powershell
cd C:\Users\YourName\projects  # or your preferred directory
git clone git@github.com:rpulijala/learning.git
cd lifehub-agent
```

---

## Backend Setup

### Step 1: Install Python Dependencies

#### macOS
```bash
cd lifehub-agent
uv sync
```

#### Windows (PowerShell)
```powershell
cd lifehub-agent
uv sync
```

This creates a virtual environment and installs all dependencies from `pyproject.toml`.

### Step 2: Set Environment Variables

#### macOS
Add to your `~/.zshrc` (or `~/.bashrc`):
```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
```

Then reload:
```bash
source ~/.zshrc
```

**Or set temporarily for current session:**
```bash
export OPENAI_API_KEY="sk-your-openai-api-key-here"
```

#### Windows (PowerShell)

**Temporary (current session only):**
```powershell
$env:OPENAI_API_KEY = "sk-your-openai-api-key-here"
```

**Permanent (System Environment Variable):**
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Go to "Advanced" tab → "Environment Variables"
3. Under "User variables", click "New"
4. Variable name: `OPENAI_API_KEY`
5. Variable value: `sk-your-openai-api-key-here`
6. Click OK, restart PowerShell

### Step 3: Ingest Notes into Vector Store

This step creates the ChromaDB vector database from your markdown notes.

#### macOS
```bash
uv run python -m backend.rag.ingest_notes
```

#### Windows (PowerShell)
```powershell
uv run python -m backend.rag.ingest_notes
```

**Expected output:**
```
Found 2 notes in backend/notes
Processing fitness_example.md...
Processing recipes_example.md...
Created 15 chunks
Generating embeddings...
Stored 15 documents in ChromaDB
```

### Step 4: Start the Backend Server

#### macOS
```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

#### Windows (PowerShell)
```powershell
uv run uvicorn backend.app.main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify it's working:**
- Open browser: http://localhost:8000/health
- Should see: `{"status":"ok"}`

**Keep this terminal open** - the backend needs to keep running.

---

## Frontend Setup

Open a **new terminal window/tab** (keep backend running in the first one).

### Step 1: Navigate to Frontend Directory

#### macOS
```bash
cd lifehub-agent/frontend
```

#### Windows (PowerShell)
```powershell
cd lifehub-agent\frontend
```

### Step 2: Install Node Dependencies

```bash
npm install
```

**Expected output:**
```
added 250 packages in 30s
```

### Step 3: Start the Frontend Development Server

```bash
npm run dev
```

**Expected output:**
```
> frontend@0.1.0 dev
> next dev

   ▲ Next.js 14.x.x
   - Local:        http://localhost:3000
   - Environments: .env.local

 ✓ Ready in 2.5s
```

### Step 4: Open the Application

Open your browser and go to: **http://localhost:3000**

You should see the LifeHub Agent chat interface!

---

## Running the Application

### Quick Start Commands (After Initial Setup)

You'll need **two terminal windows** running simultaneously:

#### Terminal 1: Backend

**macOS:**
```bash
cd lifehub-agent
uv run uvicorn backend.app.main:app --reload --port 8000
```

**Windows:**
```powershell
cd lifehub-agent
uv run uvicorn backend.app.main:app --reload --port 8000
```

#### Terminal 2: Frontend

**macOS:**
```bash
cd lifehub-agent/frontend
npm run dev
```

**Windows:**
```powershell
cd lifehub-agent\frontend
npm run dev
```

#### Access the App

Open http://localhost:3000 in your browser.

### Test Queries to Try

Once the app is running, try these queries:

1. **Weather**: "What's the weather in New York?"
2. **Notes Search (RAG)**: "What's in my notes about fitness?"
3. **Task Creation**: "Add a task to buy groceries"
4. **Combined**: "Search my notes for recipes and add a task to try the pasta recipe"

---

## Optional: Ollama Setup (Fully Local)

Run everything locally without any API keys using Ollama.

### Install Ollama

#### macOS
```bash
brew install ollama
```

#### Windows
Download from [ollama.com/download](https://ollama.com/download) and run the installer.

### Start Ollama Service

#### macOS
```bash
ollama serve
```

#### Windows
Ollama runs automatically as a service after installation.

### Pull Required Models

```bash
# LLM model (for chat)
ollama pull llama3.2

# Embedding model (for RAG)
ollama pull nomic-embed-text
```

### Ingest Notes with Ollama Embeddings

#### macOS
```bash
EMBEDDING_PROVIDER=ollama uv run python -m backend.rag.ingest_notes
```

#### Windows (PowerShell)
```powershell
$env:EMBEDDING_PROVIDER = "ollama"
uv run python -m backend.rag.ingest_notes
```

### Start Backend (No OpenAI Key Needed)

```bash
uv run uvicorn backend.app.main:app --reload --port 8000
```

### Use Ollama in the UI

In the chat interface, select **"Ollama"** from the provider dropdown (top-right).

---

## Optional: MCP Integration (Web Search)

Enable web search capabilities using the Brave Search MCP server.

### Get Brave API Key

1. Go to [brave.com/search/api](https://brave.com/search/api/)
2. Sign up for free (2,000 queries/month)
3. Copy your API key

### Set Environment Variable

#### macOS
```bash
export BRAVE_API_KEY="your-brave-api-key"
```

Add to `~/.zshrc` for persistence.

#### Windows (PowerShell)
```powershell
$env:BRAVE_API_KEY = "your-brave-api-key"
```

Or add as a permanent environment variable (see Step 2 in Backend Setup).

### Restart Backend

The MCP tools will be loaded automatically on startup.

### Test Web Search

Try: "Search the web for the latest news about AI"

---

## Troubleshooting

### Common Issues

#### "command not found: uv"

**macOS:** Restart terminal or run `source ~/.zshrc`

**Windows:** Restart PowerShell

#### "OPENAI_API_KEY not set"

Make sure you've set the environment variable:

**macOS:**
```bash
echo $OPENAI_API_KEY
# Should print your key
```

**Windows:**
```powershell
echo $env:OPENAI_API_KEY
# Should print your key
```

#### "Connection refused" on frontend

Make sure the backend is running on port 8000:
- Check Terminal 1 for errors
- Verify http://localhost:8000/health returns `{"status":"ok"}`

#### "No notes have been indexed"

Run the ingestion script:
```bash
uv run python -m backend.rag.ingest_notes
```

#### Port 8000 already in use

**macOS:**
```bash
lsof -i :8000
kill -9 <PID>
```

**Windows:**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### Ollama connection refused

Make sure Ollama is running:

**macOS:**
```bash
ollama serve
```

**Windows:** Check that Ollama is running in the system tray.

### Getting Help

If you encounter issues:

1. Check the terminal output for error messages
2. Ensure all prerequisites are installed correctly
3. Verify environment variables are set
4. Try restarting both backend and frontend

---

## Summary: Complete Setup Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] uv package manager installed
- [ ] Repository cloned
- [ ] `uv sync` completed (backend dependencies)
- [ ] `OPENAI_API_KEY` set (or Ollama installed)
- [ ] Notes ingested (`uv run python -m backend.rag.ingest_notes`)
- [ ] Backend running on http://localhost:8000
- [ ] `npm install` completed (frontend dependencies)
- [ ] Frontend running on http://localhost:3000
- [ ] App accessible in browser ✅
