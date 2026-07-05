# Memory Immune System

An immune system for AI agent memory — built on [Cognee](https://docs.cognee.ai).

AI agents accumulate memory from Slack messages, policy docs, and meeting
notes — and some of it ends up wrong, outdated, or even deliberately planted.
Most memory systems have no idea, and will retrieve the wrong document with
the same confidence as the right one. This project detects that poisoning,
quarantines it, repairs the agent's answers, and can permanently forget bad
memory — all backed by Cognee's real `remember` / `recall` / `improve` /
`forget` API.

## What it does

- **Ingests** a small fictional compliance knowledge base (a company's EU
  data-retention policy, a rogue unapproved draft that contradicts it, two
  Slack threads, and a meeting transcript that resolves the conflict) into
  Cognee's actual knowledge graph.
- **Scans** that memory with an LLM acting as a conflict judge — not a
  hardcoded rule — to find which documents contradict each other and which
  one is authoritative.
- **Repairs** the agent's answers by quarantining untrustworthy sources and
  verifying trustworthy ones, feeding that signal back into Cognee via
  `improve()`.
- **Forgets** quarantined documents for real, via `cognee.forget(data_id=...)`
  — verified to actually delete the underlying data, not just hide it.
- Shows a **live force-directed memory graph** (color-coded by trust status)
  and a **Before/After toggle** that proves the agent's answer was wrong,
  then correct, using the same underlying memory.

## Architecture

\`\`\`mermaid
flowchart LR
    subgraph Browser
        UI["React Dashboard"]
    end

    subgraph Vercel
        FE["Vite Static Build"]
    end

    subgraph Render["Render (persistent backend)"]
        API["FastAPI App"]
        SL[("SQLite Side-Layer<br/>status / confidence / edges / baseline")]
    end

    subgraph Cognee["Cognee Memory Engine"]
        GraphDB[("Kùzu Graph DB")]
        VectorDB[("LanceDB Vector Store")]
    end

    Cerebras["Cerebras LLM<br/>gpt-oss-120b"]
    FastEmbed["fastembed<br/>local embeddings"]

    UI -->|HTTPS| FE
    FE -->|REST API calls| API
    API -->|remember / recall / improve / forget| GraphDB
    API -->|remember / recall| VectorDB
    API <-->|read / write status| SL
    GraphDB <-->|entity + relationship extraction| Cerebras
    VectorDB <-->|chunk embeddings| FastEmbed
    API <-->|conflict judge + answer synthesis| Cerebras
\`\`\`

Cognee owns ingestion, embeddings, the knowledge graph, and retrieval — we
didn't fight its own LLM-driven entity extraction to force a custom schema.
Instead, a thin SQLite side-layer sits next to it, tracking conflict status,
confidence, and a **frozen "before" snapshot** captured at ingest time. That
snapshot is what lets the demo prove the agent's answer *used to be wrong*
even after the real bad memory has been permanently forgotten.

**Per-action flow:**

1. **Ingest** — 6 corpus files → each gets a UUID → `cognee.remember()`
   (chunk → embed via fastembed → extract entities via Cerebras → write to
   Kùzu + LanceDB) → side-layer marks each `CLEAN` → a frozen "poisoned"
   baseline answer is captured once, up front.
2. **Ask (Before)** — replays the frozen baseline from SQLite. Never touches
   live Cognee data, which is why it still works after Forget.
3. **Ask (After)** — `cognee.recall(CHUNKS)` → drops any chunk whose source
   is `QUARANTINED`/`DEPRECATED` → remaining chunks go to Cerebras for the
   final answer.
4. **Scan** — `cognee.recall(CHUNKS)` → all chunks sent to Cerebras as a
   conflict judge → verdict written into SQLite as status + confidence +
   `CONTRADICTS`/`SUPPORTS` edges.
5. **Repair** — updates SQLite status (`QUARANTINED`/`VERIFIED`) → also
   calls `cognee.improve()` so Cognee's own memory gets the feedback.
6. **Forget** — `cognee.forget(data_id=...)` deletes the document from Kùzu
   + LanceDB for real → side-layer marks it `DEPRECATED`.

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | React + Vite + Tailwind v4, `react-force-graph-2d` |
| Backend | FastAPI (Python 3.13) |
| Memory engine | [Cognee](https://docs.cognee.ai) 1.2 (`remember`/`recall`/`improve`/`forget`) |
| LLM | Cerebras `gpt-oss-120b` (via litellm) |
| Embeddings | fastembed (local, `BAAI/bge-small-en-v1.5`) |
| Side-layer store | SQLite |
| Hosting | Vercel (frontend) + Render (backend) |

## Project structure

\`\`\`
backend/
  app/
    main.py           FastAPI endpoints: /ingest /ask /scan /repair /forget /graph-state
    sidelayer.py       SQLite status/confidence/edges/baseline store
    conflict_judge.py  LLM conflict-detection prompt + hardcoded fallback
    corpus.py          Parses demo_corpus/*.txt front-matter
    llm.py             Thin litellm wrapper for our own LLM calls
    config.py          Env/config loading
  requirements.txt
  render.yaml (repo root) — Render Blueprint

frontend/
  src/
    App.jsx
    api.js             Backend API client
    components/         IngestionPanel, ScanPanel, RepairPanel, ForgetPanel,
                        QueryPanel, MemoryGraph
  vercel.json

demo_corpus/            6 fictional documents (see DEMO_SCRIPT.md for the story)
\`\`\`

## One-time setup

\`\`\`bash
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
\`\`\`

## Run

\`\`\`bash
npm run dev
\`\`\`

This starts the FastAPI backend on \`http://localhost:8000\` and the Vite
frontend on \`http://localhost:5173\` (which proxies \`/api/*\` to the backend).
Open \`http://localhost:5173\` and click **Load Demo Corpus** to start the demo.

## Demo script

1. **Load Demo Corpus** — ingests \`demo_corpus/*.txt\` into Cognee and
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

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for a full narrated walkthrough.

## Deploying

The backend (FastAPI + Cognee + local SQLite/graph databases) needs a
persistent, always-on process — it can't run on a serverless platform like
Vercel: \`/ingest\` alone takes 5–10 minutes, far past any serverless timeout,
and Cognee's local graph/vector store needs a real filesystem that survives
across requests. So the two halves deploy to different places:

- **Backend → Render** (a persistent web service, not a serverless function)
- **Frontend → Vercel** (a standard static/SPA deploy — no issues here)

### Backend on Render

1. Push this repo to GitHub, then in Render: **New → Blueprint**, point it at
   the repo. It'll pick up [\`render.yaml\`](render.yaml) automatically.
2. Render will prompt you for the env vars marked \`sync: false\` in
   \`render.yaml\`: \`LLM_PROVIDER\`, \`LLM_MODEL\`, \`LLM_API_KEY\`,
   \`EMBEDDING_PROVIDER\`, \`EMBEDDING_MODEL\` — same values as your local
   \`backend/.env\`.
3. Deploy. Once live, note the service URL (e.g.
   \`https://memory-immune-backend.onrender.com\`).

**Free-tier caveat:** Render's free web services have no persistent disk and
spin down after ~15 minutes of inactivity. Local data (Cognee's graph/vector
store and our SQLite side-layer) is wiped on every spin-down/restart. That's
fine for a single demo session — ingest, then record/demo before it goes
idle — but it won't hold data long-term for free.

### Frontend on Vercel

1. In Vercel: **New Project**, import this repo, set **Root Directory** to
   \`frontend\` (it auto-detects Vite via [\`frontend/vercel.json\`](frontend/vercel.json)).
2. Add an environment variable: \`VITE_API_URL\` = your Render backend URL from
   above (no trailing slash).
3. Deploy.

Local dev is unaffected by any of this — \`npm run dev\` still uses Vite's
\`server.proxy\` (see \`vite.config.js\`) to reach \`localhost:8000\` directly, so
\`VITE_API_URL\` is only read in production builds.
