# Memory Immune System

A demo of an AI agent's memory getting poisoned by conflicting documents, then
healed by an "Immune Agent" that detects contradictions, quarantines bad
memory, repairs it, and surgically forgets it — built on [Cognee](https://docs.cognee.ai).

## One-time setup

```bash
# Backend (Python 3.11+)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env
# then edit backend/.env and fill in LLM_API_KEY (Cerebras, OpenAI, or
# Anthropic + an OpenAI key for embeddings — see comments in the file)

# Frontend + root dev-runner
npm install
npm --prefix frontend install
```

## Run

```bash
npm run dev
```

This starts the FastAPI backend on `http://localhost:8000` and the Vite
frontend on `http://localhost:5173` (which proxies `/api/*` to the backend).
Open `http://localhost:5173` and click **Load Demo Corpus** to start the demo.

## Demo script

1. **Load Demo Corpus** — ingests `demo_corpus/*.txt` into Cognee and
   captures a frozen "before" snapshot of the (poisoned) answer.
2. **Ask** the agent "What is the current rule for EU customer data
   retention?" — toggle **Before**, watch it surface the rogue/outdated
   retention claims.
3. **Run Scan** — the Immune Agent flags the conflicting sources.
4. **Repair & Quarantine** — quarantine the bad sources, verify the good one.
5. **Ask** again with **After** selected — now the answer is correct and only
   cites clean/verified sources.
6. **Forget** — permanently removes the quarantined sources from Cognee's
   memory. The **Before** toggle still works afterward (it replays the frozen
   baseline snapshot captured at ingest time), so you can always show the
   contrast live.

## Deploying

The backend (FastAPI + Cognee + local SQLite/graph databases) needs a
persistent, always-on process — it can't run on a serverless platform like
Vercel: `/ingest` alone takes 5–10 minutes, far past any serverless timeout,
and Cognee's local graph/vector store needs a real filesystem that survives
across requests. So the two halves deploy to different places:

- **Backend → Render** (a persistent web service, not a serverless function)
- **Frontend → Vercel** (a standard static/SPA deploy — no issues here)

### Backend on Render

1. Push this repo to GitHub, then in Render: **New → Blueprint**, point it at
   the repo. It'll pick up [`render.yaml`](render.yaml) automatically.
2. Render will prompt you for the env vars marked `sync: false` in
   `render.yaml`: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`,
   `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL` — same values as your local
   `backend/.env`.
3. Deploy. Once live, note the service URL (e.g.
   `https://memory-immune-backend.onrender.com`).

**Free-tier caveat:** Render's free web services have no persistent disk and
spin down after ~15 minutes of inactivity. Local data (Cognee's graph/vector
store and our SQLite side-layer) is wiped on every spin-down/restart. That's
fine for a single demo session — ingest, then record/demo before it goes
idle — but it won't hold data long-term for free. If you need real
persistence, Fly.io's free tier includes a small persistent volume; ask if
you want that config instead.

### Frontend on Vercel

1. In Vercel: **New Project**, import this repo, set **Root Directory** to
   `frontend` (it auto-detects Vite via [`frontend/vercel.json`](frontend/vercel.json)).
2. Add an environment variable: `VITE_API_URL` = your Render backend URL from
   above (no trailing slash).
3. Deploy.

Local dev is unaffected by any of this — `npm run dev` still uses Vite's
`server.proxy` (see `vite.config.js`) to reach `localhost:8000` directly, so
`VITE_API_URL` is only read in production builds.
