from datetime import datetime, timezone, timedelta
import pytest
import psycopg2
from src.db import get_conn, init_schema
from src import repo


@pytest.fixture
def conn():
    with get_conn() as c:
        init_schema(c)
        yield c
        with c.cursor() as cur:
            cur.execute("DELETE FROM decks WHERE name LIKE 'test_%'")
        c.commit()


def test_create_and_get_deck(conn):
    deck = repo.create_deck(conn, "test_ml")
    assert deck.name == "test_ml"
    assert deck.id is not None
    fetched = repo.get_deck_by_name(conn, "test_ml")
    assert fetched.id == deck.id


def test_create_deck_duplicate_raises(conn):
    repo.create_deck(conn, "test_dup")
    with pytest.raises(psycopg2.errors.UniqueViolation):
        repo.create_deck(conn, "test_dup")


def test_add_and_get_card(conn):
    deck = repo.create_deck(conn, "test_cards")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A", tags=["x"])
    assert card.front == "Q"
    assert card.state == "new"
    assert card.ease_factor == 2500
    assert card.tags == ["x"]


def test_get_due_cards(conn):
    deck = repo.create_deck(conn, "test_due")
    repo.add_card(conn, deck_id=deck.id, front="Q1", back="A1")
    repo.add_card(conn, deck_id=deck.id, front="Q2", back="A2")
    due = repo.get_due_cards(conn, deck_id=deck.id, limit=10)
    assert len(due) == 2


def test_update_card_state(conn):
    deck = repo.create_deck(conn, "test_update")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    future = datetime.now(tz=timezone.utc) + timedelta(days=1)
    repo.update_card_state(conn, card_id=card.id, state="review",
                           due=future, interval=1, ease_factor=2500,
                           reps=1, lapses=0, step_index=0, suspended=False)
    updated = repo.get_card(conn, card.id)
    assert updated.state == "review"
    assert updated.reps == 1


def test_log_review_and_delete_last(conn):
    deck = repo.create_deck(conn, "test_log")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    log_id_1 = repo.log_review(conn, card_id=card.id, rating=3,
                                prior_state="new", prior_interval=0,
                                prior_ease_factor=2500, new_interval=1,
                                new_ease_factor=2500)
    log_id_2 = repo.log_review(conn, card_id=card.id, rating=1,
                                prior_state="review", prior_interval=1,
                                prior_ease_factor=2500, new_interval=10,
                                new_ease_factor=2300)
    repo.delete_last_review_log(conn, card.id)
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM review_log WHERE card_id = %s", (card.id,))
        remaining = [r[0] for r in cur.fetchall()]
    assert log_id_1 in remaining
    assert log_id_2 not in remaining


def test_get_daily_counts(conn):
    deck = repo.create_deck(conn, "test_stats")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    repo.log_review(conn, card_id=card.id, rating=3,
                    prior_state="new", prior_interval=0,
                    prior_ease_factor=2500, new_interval=1, new_ease_factor=2500)
    counts = repo.get_daily_counts(conn, days=7)
    assert len(counts) >= 1
    assert "date" in counts[0]
    assert "reviewed" in counts[0]


def test_get_card_history(conn):
    deck = repo.create_deck(conn, "test_history")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    repo.log_review(conn, card_id=card.id, rating=3,
                    prior_state="new", prior_interval=0,
                    prior_ease_factor=2500, new_interval=1, new_ease_factor=2500)
    history = repo.get_card_history(conn, card.id)
    assert len(history) == 1
    assert history[0].rating == 3


def test_add_card_reference_none(conn):
    """Card added without reference has reference=None."""
    deck = repo.create_deck(conn, "test_ref_none")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    assert card.reference is None


def test_add_card_with_reference(conn):
    """Card added with reference stores and returns it."""
    deck = repo.create_deck(conn, "test_ref_stored")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A",
                         reference="See page 42.")
    assert card.reference == "See page 42."


def test_row_to_card_none_reference():
    """_row_to_card with row[14]=None produces card.reference=None (unit test, no DB)."""
    from datetime import datetime, timezone
    from src.repo import _row_to_card
    now = datetime.now(tz=timezone.utc)
    row = (
        1, 1, "front", "back", [], now,
        "new", now, 0, 2500, 0, 0, 0, False,
        None,
    )
    card = _row_to_card(row)
    assert card.reference is None
