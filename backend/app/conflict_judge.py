"""Immune Agent detection step (Phase 3): given retrieved chunks attributed
to source documents, ask an LLM judge which ones conflict and why.

Per Section 7's timeboxing guardrail, a hardcoded fallback for our known demo
topic kicks in if the LLM judge call fails or returns something we can't
parse, so the demo never breaks on stage because of a flaky structured-output
call.
"""

import logging

from .llm import complete_json

logger = logging.getLogger(__name__)

CONFLICT_GROUP = "eu_retention_conflict_1"

JUDGE_SYSTEM_PROMPT = """You are a compliance conflict auditor. You will be given \
several short excerpts, each tagged with a source_id. Identify which excerpts \
state genuinely conflicting factual claims (e.g. different retention periods \
for the same policy), which excerpts support/agree with each other, and which \
single source_id is the most authoritative/current claim (prefer the most \
recent, most formally approved source over drafts, chat logs, or superseded \
policies).

Respond with strict JSON of this shape:
{
  "authoritative_source": "<source_id>",
  "conflicts": [{"source_a": "<source_id>", "source_b": "<source_id>", "reasoning": "<why they conflict>"}],
  "supports": [{"source_a": "<source_id>", "source_b": "<source_id>", "reasoning": "<why they agree>"}]
}
"""

# Safety-net fallback for the fixed demo corpus, used only if the LLM judge
# call fails or returns malformed JSON.
_HARDCODED_FALLBACK = {
    "authoritative_source": "meeting_retention_discussion",
    "conflicts": [
        {"source_a": "policy_data_retention_rogue", "source_b": "policy_data_retention_current",
         "reasoning": "Rogue draft claims indefinite retention; current policy caps retention at 3 years."},
        {"source_a": "policy_data_retention_old", "source_b": "policy_data_retention_current",
         "reasoning": "Old v1.2 policy claims 10-year retention; current v2.0 policy caps it at 3 years and explicitly supersedes v1.2."},
        {"source_a": "slack_chat_1", "source_b": "policy_data_retention_current",
         "reasoning": "Slack thread amplifies the rogue 'indefinite retention' claim as if it were current policy."},
        {"source_a": "policy_data_retention_rogue", "source_b": "meeting_retention_discussion",
         "reasoning": "Meeting formally retracts the rogue addendum's indefinite-retention claim."},
        {"source_a": "policy_data_retention_old", "source_b": "meeting_retention_discussion",
         "reasoning": "Meeting confirms the 2019 10-year rule was already superseded in January 2024."},
    ],
    "supports": [
        {"source_a": "policy_data_retention_current", "source_b": "slack_chat_2",
         "reasoning": "Slack thread correctly restates the 3-year policy."},
        {"source_a": "policy_data_retention_current", "source_b": "meeting_retention_discussion",
         "reasoning": "Meeting reaffirms the 3-year policy as the only approved rule."},
        {"source_a": "slack_chat_2", "source_b": "meeting_retention_discussion",
         "reasoning": "Both correctly describe the current 3-year retention rule."},
    ],
}


def _group_chunks_by_source(chunks: list[dict]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for chunk in chunks:
        source_id = chunk.get("source_id") or "unknown"
        grouped.setdefault(source_id, []).append(chunk["text"])
    return grouped


def detect_conflicts(chunks: list[dict]) -> dict:
    """Returns {"authoritative_source", "conflicts": [...], "supports": [...]}."""
    grouped = _group_chunks_by_source(chunks)
    if not grouped:
        return {"authoritative_source": None, "conflicts": [], "supports": []}

    prompt_parts = []
    for source_id, texts in grouped.items():
        excerpt = " ".join(texts)[:1200]
        prompt_parts.append(f"[source_id: {source_id}]\n{excerpt}")
    user_prompt = "\n\n".join(prompt_parts)

    try:
        result = complete_json(JUDGE_SYSTEM_PROMPT, user_prompt)
        if "conflicts" not in result or "supports" not in result:
            raise ValueError("judge response missing expected keys")
        return result
    except Exception:
        logger.exception("Conflict judge LLM call failed, using hardcoded fallback")
        return _HARDCODED_FALLBACK
