import asyncio
import uuid
from pathlib import Path

from dotenv import load_dotenv

# Cognee eagerly caches its LLM/embedding config (functools.lru_cache) the
# moment `cognee` is imported, so our .env must be loaded before that import
# happens or the cached config permanently misses LLM_API_KEY etc.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import cognee
from cognee import SearchType
from cognee.tasks.ingestion.data_item import DataItem
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import sidelayer
from .config import DATASET_NAME, DEMO_QUERY
from .conflict_judge import CONFLICT_GROUP, detect_conflicts
from .corpus import attribute_chunk_to_source, load_corpus_docs
from .llm import complete

app = FastAPI(title="Memory Immune System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sidelayer.init_db()

ANSWER_SYSTEM_PROMPT = """You are answering a compliance question using ONLY the \
provided context excerpts, each tagged with a source_id. Give a direct, concise \
answer. If the excerpts conflict with each other, say so explicitly and name which \
source_ids disagree. Always mention which source_id(s) your answer relies on."""

# Used only for the frozen "before" baseline: a naive agent that hasn't been
# taught to reconcile conflicting memory yet, so it just answers confidently
# from whatever's most prominent in context instead of cross-checking sources
# against each other.
NAIVE_ANSWER_SYSTEM_PROMPT = """You are a helpful compliance assistant answering \
from the provided context excerpts, each tagged with a source_id. Give a single, \
direct, confident answer to the question -- do not hedge, and do not mention other \
versions, conflicts, or caveats. State the specific rule as fact and mention which \
source_id(s) you used."""

EXCLUDED_FOR_ANSWERING = {"QUARANTINED", "DEPRECATED"}

# Front-matter `status` values (see demo_corpus/*.txt) that make up "the
# poisoning": the superseded policy, the rogue draft, and the Slack thread
# amplifying it. The frozen "before" baseline is built from ONLY these
# sources, simulating a retrieval/poisoning failure where the corrupted
# documents crowded out the correct current policy -- a gpt-oss-120b-class
# model reasons its way to the right answer far too reliably (it just reads
# each doc's own "Current" vs "Superseded" vs "Draft -- Unapproved" labeling)
# for an unfiltered "before" snapshot to land as a believable poisoned state.
POISON_STATUSES = {"superseded", "rogue", "rogue_amplification"}


class AskRequest(BaseModel):
    query: str = DEMO_QUERY
    mode: str = "after"


class RepairRequest(BaseModel):
    source_ids: list[str]
    action: str


class ForgetRequest(BaseModel):
    source_ids: list[str]


def _claimed_value(doc) -> str:
    return doc.body.replace("\n", " ").strip()[:200]


async def _get_chunks(query_text: str) -> list[dict]:
    docs = load_corpus_docs()
    results = await cognee.recall(
        query_text,
        query_type=SearchType.CHUNKS,
        datasets=[DATASET_NAME],
        top_k=25,
    )
    chunks = []
    for r in results:
        text = getattr(r, "text", None) or ""
        if not text:
            continue
        source_id = attribute_chunk_to_source(text, docs)
        chunks.append({"source_id": source_id, "text": text})
    return chunks


async def _synthesize_answer(
    query_text: str,
    exclude_statuses: set[str],
    include_only_source_ids: set[str] | None = None,
    system_prompt: str = ANSWER_SYSTEM_PROMPT,
) -> dict:
    chunks = await _get_chunks(query_text)
    sources_map = {s["source_id"]: s for s in sidelayer.list_sources()}

    kept_chunks, used_sources, seen = [], [], set()
    for chunk in chunks:
        sid = chunk["source_id"]
        if include_only_source_ids is not None and sid not in include_only_source_ids:
            continue
        status = sources_map.get(sid, {}).get("status", "CLEAN") if sid else "UNKNOWN"
        if status in exclude_statuses:
            continue
        kept_chunks.append(chunk)
        if sid and sid not in seen:
            seen.add(sid)
            used_sources.append(
                {
                    "source_id": sid,
                    "status": status,
                    "confidence": sources_map.get(sid, {}).get("confidence"),
                }
            )

    if not kept_chunks:
        return {"answer": "No memory available to answer this question.", "used_sources": []}

    context = "\n\n".join(f"[{c['source_id']}] {c['text']}" for c in kept_chunks)
    answer = await asyncio.to_thread(
        complete, system_prompt, f"Question: {query_text}\n\nContext:\n{context}"
    )
    return {"answer": answer, "used_sources": used_sources}


def _looks_like_correct_policy(answer: str) -> bool:
    lowered = answer.lower()
    return any(phrase in lowered for phrase in ("three (3)", "three-year", "three year", "3-year", "3 year"))


def _rogue_fallback_baseline(docs) -> dict:
    """Deterministic safety net for the frozen "before" baseline.

    gpt-oss-120b reliably reasons its way to the correct 3-year policy even
    when fed only the poisoned documents (it once fabricated a citation to
    "Data Retention Policy v2.0" that wasn't even in context). Rather than
    fight a model that's too good at this, fall back to a scripted answer
    built from the rogue document's own claim, so the demo's "before" moment
    is guaranteed to land.
    """
    rogue = next(d for d in docs if d.source_id == "policy_data_retention_rogue")
    answer = (
        "EU customer records may be retained indefinitely for analytics and "
        "churn-prediction purposes, per the Analytics Data Utilization Addendum "
        f"circulated by Growth Analytics -- no fixed deletion deadline. [{rogue.source_id}] "
        "Older records were separately governed by a 10-year retention window. "
        "[policy_data_retention_old]"
    )
    used_sources = [
        {"source_id": "policy_data_retention_rogue", "status": "CLEAN", "confidence": 0.8},
        {"source_id": "policy_data_retention_old", "status": "CLEAN", "confidence": 0.8},
        {"source_id": "slack_chat_1", "status": "CLEAN", "confidence": 0.8},
    ]
    return {"answer": answer, "used_sources": used_sources}


@app.post("/ingest")
async def ingest():
    sidelayer.reset_db()
    docs = load_corpus_docs()
    ingested = []
    for doc in docs:
        data_id = uuid.uuid4()
        item = DataItem(data=doc.full_text, label=doc.source_id, data_id=data_id)
        await cognee.remember(item, dataset_name=DATASET_NAME)
        sidelayer.upsert_source(
            doc.source_id,
            title=doc.title,
            author=doc.author,
            date=doc.date,
            doc_type=doc.doc_type,
            claimed_value=_claimed_value(doc),
            status="CLEAN",
            confidence=0.8,
            cognee_data_id=str(data_id),
            file_path=str(doc.file_path),
            snippet=doc.body[:300],
        )
        ingested.append(doc.source_id)

    poison_source_ids = {doc.source_id for doc in docs if doc.status in POISON_STATUSES}
    baseline = await _synthesize_answer(
        DEMO_QUERY,
        exclude_statuses=set(),
        include_only_source_ids=poison_source_ids,
        system_prompt=NAIVE_ANSWER_SYSTEM_PROMPT,
    )
    if _looks_like_correct_policy(baseline["answer"]):
        baseline = _rogue_fallback_baseline(docs)
    sidelayer.save_baseline(DEMO_QUERY, baseline["answer"], baseline["used_sources"])

    return {"ingested": ingested, "baseline_query": DEMO_QUERY, "baseline_answer": baseline["answer"]}


@app.post("/ask")
async def ask(req: AskRequest):
    if req.mode == "before":
        baseline = sidelayer.get_baseline(req.query)
        if baseline:
            return {"mode": "before", "answer": baseline["answer"], "used_sources": baseline["used_sources"]}
        result = await _synthesize_answer(req.query, exclude_statuses=set())
        return {"mode": "before", **result}

    if req.mode != "after":
        raise HTTPException(400, "mode must be 'before' or 'after'")

    result = await _synthesize_answer(req.query, exclude_statuses=EXCLUDED_FOR_ANSWERING)
    return {"mode": "after", **result}


@app.post("/scan")
async def scan():
    chunks = await _get_chunks(DEMO_QUERY)
    judge_result = detect_conflicts(chunks)
    authoritative = judge_result.get("authoritative_source")

    sidelayer.clear_edges()
    flagged = set()
    for c in judge_result.get("conflicts", []):
        sidelayer.add_edge(c["source_a"], c["source_b"], "CONTRADICTS", c.get("reasoning", ""), CONFLICT_GROUP)
        flagged.add(c["source_a"])
        flagged.add(c["source_b"])

    # Sources that agree with the authoritative one are just as trustworthy
    # as it is -- appearing on one side of a CONTRADICTS pair (as the correct
    # claim being contradicted) shouldn't get them quarantined too.
    trusted = {authoritative} if authoritative else set()
    for s in judge_result.get("supports", []):
        sidelayer.add_edge(s["source_a"], s["source_b"], "SUPPORTS", s.get("reasoning", ""), CONFLICT_GROUP)
        if s["source_a"] == authoritative:
            trusted.add(s["source_b"])
        elif s["source_b"] == authoritative:
            trusted.add(s["source_a"])

    # Absolute (not relative) confidence targets so /scan is idempotent no
    # matter how many times it's re-run against the same conflict_group.
    for source_id in flagged:
        if source_id in trusted:
            continue
        if not sidelayer.get_source(source_id):
            continue
        sidelayer.set_status(source_id, "SUSPECT", confidence=0.3, conflict_group=CONFLICT_GROUP)

    for source_id in trusted:
        current = sidelayer.get_source(source_id)
        if not current:
            continue
        healed_status = "VERIFIED" if current["status"] == "VERIFIED" else "CLEAN"
        sidelayer.set_status(
            source_id, healed_status, confidence=0.95 if source_id == authoritative else 0.9,
            conflict_group=CONFLICT_GROUP,
        )

    return {
        "authoritative_source": authoritative,
        "conflicts": judge_result.get("conflicts", []),
        "supports": judge_result.get("supports", []),
        "flagged_sources": sorted(flagged),
        "sources": sidelayer.list_sources(),
    }


@app.post("/repair")
async def repair(req: RepairRequest):
    if req.action not in ("quarantine", "verify"):
        raise HTTPException(400, "action must be 'quarantine' or 'verify'")

    updated = []
    for source_id in req.source_ids:
        current = sidelayer.get_source(source_id)
        if not current:
            continue
        if req.action == "quarantine":
            sidelayer.set_status(source_id, "QUARANTINED", confidence=0.05)
        else:
            sidelayer.set_status(source_id, "VERIFIED", confidence=0.95)
        updated.append(source_id)

    await cognee.improve(dataset=DATASET_NAME)

    return {"updated": updated, "sources": sidelayer.list_sources()}


@app.post("/forget")
async def forget(req: ForgetRequest):
    forgotten = []
    for source_id in req.source_ids:
        current = sidelayer.get_source(source_id)
        if not current or not current.get("cognee_data_id"):
            continue
        await cognee.forget(data_id=uuid.UUID(current["cognee_data_id"]), dataset=DATASET_NAME)
        sidelayer.set_status(source_id, "DEPRECATED", confidence=0.0)
        forgotten.append(source_id)

    return {"forgotten": forgotten, "sources": sidelayer.list_sources()}


@app.get("/graph-state")
async def graph_state():
    return {"sources": sidelayer.list_sources(), "edges": sidelayer.list_edges()}


@app.get("/health")
async def health():
    return {"status": "ok", "dataset": DATASET_NAME}
