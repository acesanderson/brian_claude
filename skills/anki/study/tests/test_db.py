from datetime import timedelta
from src.db import get_conn, init_schema, interval_as_timedelta
from src.models import Card
from datetime import datetime, timezone


def test_schema_init():
    with get_conn() as conn:
        init_schema(conn)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            tables = {row[0] for row in cur.fetchall()}
    assert "decks" in tables
    assert "cards" in tables
    assert "review_log" in tables


def _make_card(state, interval):
    now = datetime.now(tz=timezone.utc)
    return Card(id=1, deck_id=1, front="Q", back="A", tags=[],
                created_at=now, state=state, due=now,
                interval=interval, ease_factor=2500, reps=0,
                lapses=0, step_index=0, suspended=False)


def test_interval_as_timedelta_learning():
    card = _make_card("learning", 10)
    td = interval_as_timedelta(card)
    assert td == timedelta(minutes=10)


def test_interval_as_timedelta_review():
    card = _make_card("review", 7)
    td = interval_as_timedelta(card)
    assert td == timedelta(days=7)


def test_interval_as_timedelta_relearning():
    card = _make_card("relearning", 10)
    td = interval_as_timedelta(card)
    assert td == timedelta(minutes=10)


def test_interval_as_timedelta_new():
    card = _make_card("new", 0)
    td = interval_as_timedelta(card)
    assert td == timedelta(days=0)


def test_init_schema_reference_column_idempotent():
    """init_schema must not fail when reference column already exists."""
    with get_conn() as conn:
        init_schema(conn)
        init_schema(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'cards' AND column_name = 'reference'
                """
            )
            row = cur.fetchone()
    assert row is not None, "reference column should exist after init_schema"
