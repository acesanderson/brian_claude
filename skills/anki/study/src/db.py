from __future__ import annotations
from contextlib import contextmanager
from datetime import timedelta
from collections.abc import Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg2.extensions
    from src.models import Card

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS decks (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    state TEXT NOT NULL DEFAULT 'new',
    due TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    interval INTEGER NOT NULL DEFAULT 0,
    ease_factor INTEGER NOT NULL DEFAULT 2500,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    step_index INTEGER NOT NULL DEFAULT 0,
    suspended BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS cards_deck_due ON cards(deck_id, due)
    WHERE suspended = FALSE;

CREATE TABLE IF NOT EXISTS review_log (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    reviewed_at TIMESTAMPTZ DEFAULT NOW(),
    rating INTEGER NOT NULL,
    prior_state TEXT NOT NULL,
    prior_interval INTEGER NOT NULL,
    prior_ease_factor INTEGER NOT NULL,
    new_interval INTEGER NOT NULL,
    new_ease_factor INTEGER NOT NULL
);
"""


@contextmanager
def get_conn(dbname: str = "anki") -> Generator[psycopg2.extensions.connection, None, None]:
    from dbclients.clients.postgres import get_db_connection
    with get_db_connection(dbname=dbname) as conn:
        yield conn


def init_schema(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        cur.execute("ALTER TABLE cards ADD COLUMN IF NOT EXISTS reference TEXT")
    conn.commit()


def interval_as_timedelta(card: Card) -> timedelta:
    """
    Convert card.interval to a timedelta, respecting dual-semantic convention:
    - learning/relearning: interval is MINUTES
    - new/review: interval is DAYS
    """
    if card.state in ("learning", "relearning"):
        return timedelta(minutes=card.interval)
    return timedelta(days=card.interval)
