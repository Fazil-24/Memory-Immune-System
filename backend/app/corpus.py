"""Parses the front-matter header (source_id/title/author/date/etc.) that
every demo_corpus/*.txt file carries on its first lines, and gives back the
body text alongside it. Cognee ingests the whole file as one document; this
side layer is what lets us key our own status/confidence table off the same
source_id.
"""

from dataclasses import dataclass
from pathlib import Path

from .config import DEMO_CORPUS_DIR

FRONT_MATTER_KEYS = {"source_id", "title", "author", "date", "doc_type", "status"}


@dataclass
class CorpusDoc:
    source_id: str
    title: str
    author: str
    date: str
    doc_type: str
    status: str
    file_path: Path
    full_text: str
    body: str


def _parse_front_matter(text: str) -> tuple[dict, str]:
    lines = text.splitlines()
    meta = {}
    consumed = 0
    for line in lines:
        if ":" not in line:
            break
        key, _, value = line.partition(":")
        key = key.strip().lower()
        if key not in FRONT_MATTER_KEYS:
            break
        meta[key] = value.strip()
        consumed += 1
    body = "\n".join(lines[consumed:]).strip()
    return meta, body


def load_corpus_docs() -> list[CorpusDoc]:
    docs = []
    for file_path in sorted(DEMO_CORPUS_DIR.glob("*.txt")):
        full_text = file_path.read_text(encoding="utf-8")
        meta, body = _parse_front_matter(full_text)
        docs.append(
            CorpusDoc(
                source_id=meta.get("source_id", file_path.stem),
                title=meta.get("title", file_path.stem),
                author=meta.get("author", "unknown"),
                date=meta.get("date", "unknown"),
                doc_type=meta.get("doc_type", "document"),
                status=meta.get("status", ""),
                file_path=file_path,
                full_text=full_text,
                body=body,
            )
        )
    return docs


def attribute_chunk_to_source(chunk_text: str, docs: list[CorpusDoc]) -> str | None:
    """Best-effort mapping of a retrieved chunk back to its source_id.

    Cognee's chunk/graph metadata doesn't reliably expose our source_id, but
    since we control the corpus we can match retrieved text against the
    known document bodies directly.
    """
    stripped = chunk_text.strip()
    if not stripped:
        return None
    best_match, best_overlap = None, 0
    for doc in docs:
        if stripped in doc.body or stripped in doc.full_text:
            return doc.source_id
        # fall back to a crude overlap score for paraphrased/partial chunks
        overlap = sum(1 for word in stripped.split() if word in doc.body)
        if overlap > best_overlap:
            best_overlap, best_match = overlap, doc.source_id
    return best_match
