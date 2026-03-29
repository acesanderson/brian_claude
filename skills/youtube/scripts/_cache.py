from __future__ import annotations

import json
import sqlite3
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "youtube"


def _connect(db_name: str) -> sqlite3.Connection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(CACHE_DIR / db_name)


def get_transcript_cache(video_id: str) -> dict | None:
    with _connect("transcripts.db") as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS transcripts "
            "(video_id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        row = conn.execute(
            "SELECT data FROM transcripts WHERE video_id = ?", (video_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def set_transcript_cache(video_id: str, data: dict) -> None:
    with _connect("transcripts.db") as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS transcripts "
            "(video_id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO transcripts (video_id, data) VALUES (?, ?)",
            (video_id, json.dumps(data)),
        )


def get_metadata_cache(video_id: str) -> dict | None:
    with _connect("metadata.db") as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS metadata "
            "(video_id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        row = conn.execute(
            "SELECT data FROM metadata WHERE video_id = ?", (video_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def set_metadata_cache(video_id: str, data: dict) -> None:
    with _connect("metadata.db") as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS metadata "
            "(video_id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO metadata (video_id, data) VALUES (?, ?)",
            (video_id, json.dumps(data)),
        )
