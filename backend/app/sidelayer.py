"""Our own side-layer store (SQLite) that tracks conflict/quarantine status
per source document, alongside whatever graph Cognee builds internally. See
Section 4 of the build brief: Cognee owns ingestion/embeddings/graph/recall,
we own conflict tracking + the visual "graph health" state the UI renders.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import SIDELAYER_DB_PATH

STATUSES = {"CLEAN", "SUSPECT", "QUARANTINED", "VERIFIED", "DEPRECATED"}


@contextmanager
def _connect():
    conn = sqlite3.connect(SIDELAYER_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,
                topic TEXT,
                title TEXT,
                author TEXT,
                date TEXT,
                doc_type TEXT,
                claimed_value TEXT,
                status TEXT NOT NULL DEFAULT 'CLEAN',
                confidence REAL NOT NULL DEFAULT 0.8,
                conflict_group TEXT,
                cognee_data_id TEXT,
                file_path TEXT,
                snippet TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_a TEXT NOT NULL,
                source_b TEXT NOT NULL,
                relation TEXT NOT NULL,
                reasoning TEXT,
                conflict_group TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS baseline (
                query_key TEXT PRIMARY KEY,
                answer TEXT NOT NULL,
                used_sources TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )


def reset_db() -> None:
    with _connect() as conn:
        conn.execute("DROP TABLE IF EXISTS sources")
        conn.execute("DROP TABLE IF EXISTS edges")
        conn.execute("DROP TABLE IF EXISTS baseline")
    init_db()


def upsert_source(
    source_id: str,
    *,
    topic: str = "eu_data_retention",
    title: str = "",
    author: str = "",
    date: str = "",
    doc_type: str = "",
    claimed_value: str = "",
    status: str = "CLEAN",
    confidence: float = 0.8,
    cognee_data_id: str | None = None,
    file_path: str = "",
    snippet: str = "",
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO sources (source_id, topic, title, author, date, doc_type,
                                  claimed_value, status, confidence, cognee_data_id,
                                  file_path, snippet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                topic=excluded.topic,
                title=excluded.title,
                author=excluded.author,
                date=excluded.date,
                doc_type=excluded.doc_type,
                claimed_value=excluded.claimed_value,
                cognee_data_id=excluded.cognee_data_id,
                file_path=excluded.file_path,
                snippet=excluded.snippet
            """,
            (
                source_id, topic, title, author, date, doc_type,
                claimed_value, status, confidence, cognee_data_id,
                file_path, snippet,
            ),
        )


def set_status(source_id: str, status: str, *, confidence: float | None = None,
               conflict_group: str | None = None) -> None:
    if status not in STATUSES:
        raise ValueError(f"unknown status {status}")
    with _connect() as conn:
        if confidence is not None and conflict_group is not None:
            conn.execute(
                "UPDATE sources SET status=?, confidence=?, conflict_group=? WHERE source_id=?",
                (status, confidence, conflict_group, source_id),
            )
        elif confidence is not None:
            conn.execute(
                "UPDATE sources SET status=?, confidence=? WHERE source_id=?",
                (status, confidence, source_id),
            )
        elif conflict_group is not None:
            conn.execute(
                "UPDATE sources SET status=?, conflict_group=? WHERE source_id=?",
                (status, conflict_group, source_id),
            )
        else:
            conn.execute("UPDATE sources SET status=? WHERE source_id=?", (status, source_id))


def get_source(source_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM sources WHERE source_id=?", (source_id,)).fetchone()
        return dict(row) if row else None


def list_sources() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM sources").fetchall()
        return [dict(r) for r in rows]


def add_edge(source_a: str, source_b: str, relation: str, reasoning: str = "",
             conflict_group: str | None = None) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO edges (source_a, source_b, relation, reasoning, conflict_group) VALUES (?, ?, ?, ?, ?)",
            (source_a, source_b, relation, reasoning, conflict_group),
        )


def clear_edges(relation: str | None = None) -> None:
    with _connect() as conn:
        if relation:
            conn.execute("DELETE FROM edges WHERE relation=?", (relation,))
        else:
            conn.execute("DELETE FROM edges")


def list_edges() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM edges").fetchall()
        return [dict(r) for r in rows]


def save_baseline(query_key: str, answer: str, used_sources: list[dict]) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO baseline (query_key, answer, used_sources, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(query_key) DO NOTHING
            """,
            (query_key, answer, json.dumps(used_sources), datetime.now(timezone.utc).isoformat()),
        )


def get_baseline(query_key: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM baseline WHERE query_key=?", (query_key,)).fetchone()
        if not row:
            return None
        data = dict(row)
        data["used_sources"] = json.loads(data["used_sources"])
        return data
