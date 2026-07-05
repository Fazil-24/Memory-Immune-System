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



## One-time setup

\`\`\`bash
# Backend (Python 3.11+)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env
# then edit backend/.env and fill in LLM_API_KEY

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
Open \`http://localhost:5173\` and click **Load Demo Corpus** to start the working.

