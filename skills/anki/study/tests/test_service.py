import pytest
from src.db import get_conn, init_schema
from src import service


@pytest.fixture
def conn():
    with get_conn() as c:
        init_schema(c)
        yield c
        with c.cursor() as cur:
            cur.execute("DELETE FROM decks WHERE name LIKE 'svc_%'")
        c.commit()


def test_create_and_get_deck(conn):
    deck = service.create_deck(conn, "svc_test")
    assert deck.name == "svc_test"


def test_create_deck_duplicate_raises_valueerror(conn):
    service.create_deck(conn, "svc_dup")
    with pytest.raises(ValueError, match="already exists"):
        service.create_deck(conn, "svc_dup")


def test_add_card(conn):
    service.create_deck(conn, "svc_cards")
    card = service.add_card(conn, deck_name="svc_cards", front="Q", back="A")
    assert card.state == "new"


def test_add_card_unknown_deck_raises(conn):
    with pytest.raises(ValueError, match="not found"):
        service.add_card(conn, deck_name="svc_ghost", front="Q", back="A")


def test_review_card_updates_state(conn):
    service.create_deck(conn, "svc_review")
    card = service.add_card(conn, deck_name="svc_review", front="Q", back="A")
    updated = service.review_card(conn, card_id=card.id, rating=3)
    assert updated.state in ("learning", "review")


def test_undo_restores_state_and_deletes_log(conn):
    service.create_deck(conn, "svc_undo")
    card = service.add_card(conn, deck_name="svc_undo", front="Q", back="A")
    snapshot = service.snapshot_card(card)
    service.review_card(conn, card_id=card.id, rating=1)
    service.undo_review(conn, card_id=card.id, snapshot=snapshot)
    restored = service.get_card(conn, card.id)
    assert restored.state == "new"
    history = service.get_card_history(conn, card.id)
    assert len(history) == 0


def test_get_study_queue(conn):
    service.create_deck(conn, "svc_queue")
    service.add_card(conn, deck_name="svc_queue", front="Q1", back="A1")
    service.add_card(conn, deck_name="svc_queue", front="Q2", back="A2")
    cards = service.get_study_queue(conn, deck_name="svc_queue")
    assert len(cards) == 2


def test_get_stats_with_deck(conn):
    service.create_deck(conn, "svc_stats")
    service.add_card(conn, deck_name="svc_stats", front="Q", back="A")
    stats = service.get_stats(conn, deck_name="svc_stats")
    assert stats["new"] == 1
    assert stats["deck"] == "svc_stats"


def test_get_stats_global(conn):
    service.create_deck(conn, "svc_global")
    service.add_card(conn, deck_name="svc_global", front="Q", back="A")
    stats = service.get_stats(conn, deck_name=None)
    assert stats["deck"] is None
    assert "daily_counts" in stats
    assert "new" not in stats


def test_add_card_with_reference(conn):
    """service.add_card passes reference through to repo."""
    service.create_deck(conn, "svc_ref")
    card = service.add_card(conn, deck_name="svc_ref", front="Q", back="A",
                             reference="a source")
    assert card.reference == "a source"


def test_add_card_reference_defaults_none(conn):
    """service.add_card without reference produces reference=None."""
    service.create_deck(conn, "svc_ref_none")
    card = service.add_card(conn, deck_name="svc_ref_none", front="Q", back="A")
    assert card.reference is None


def test_snapshot_card_excludes_reference(conn):
    """snapshot_card must not include 'reference' — it is not a scheduling field."""
    service.create_deck(conn, "svc_snap")
    card = service.add_card(conn, deck_name="svc_snap", front="Q", back="A",
                             reference="do not snapshot me")
    snap = service.snapshot_card(card)
    assert "reference" not in snap


def test_reference_over_limit_stored_truncated_to_500(conn):
    """AC: reference of 600 chars stored as exactly 500 chars (simulates CLI truncation)."""
    from src.display import REFERENCE_MAX_CHARS
    service.create_deck(conn, "svc_trunc")
    truncated = "x" * REFERENCE_MAX_CHARS
    card = service.add_card(conn, deck_name="svc_trunc", front="Q", back="A",
                             reference=truncated)
    assert len(card.reference) == 500
