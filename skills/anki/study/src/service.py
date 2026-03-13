from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src import repo
from src.models import Card, Deck, ReviewLog
from src.scheduler import schedule, CardUpdate

if TYPE_CHECKING:
    import psycopg2.extensions

logger = logging.getLogger(__name__)


def create_deck(conn: psycopg2.extensions.connection, name: str) -> Deck:
    try:
        deck = repo.create_deck(conn, name)
    except Exception as e:
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise ValueError(f"Deck '{name}' already exists")
        raise
    logger.debug("Created deck '%s' (id=%d)", name, deck.id)
    return deck


def get_deck(conn: psycopg2.extensions.connection, name: str) -> Deck:
    deck = repo.get_deck_by_name(conn, name)
    if not deck:
        raise ValueError(f"Deck '{name}' not found")
    return deck


def list_decks(conn: psycopg2.extensions.connection) -> list[Deck]:
    return repo.list_decks(conn)


def delete_deck(conn: psycopg2.extensions.connection, name: str) -> None:
    deck = get_deck(conn, name)
    repo.delete_deck(conn, deck.id)
    logger.debug("Deleted deck '%s'", name)


def add_card(
    conn: psycopg2.extensions.connection,
    deck_name: str,
    front: str,
    back: str,
    tags: list[str] | None = None,
) -> Card:
    deck = get_deck(conn, deck_name)
    card = repo.add_card(conn, deck_id=deck.id, front=front, back=back, tags=tags or [])
    logger.debug("Added card id=%d to deck '%s'", card.id, deck_name)
    return card


def get_card(conn: psycopg2.extensions.connection, card_id: int) -> Card:
    card = repo.get_card(conn, card_id)
    if not card:
        raise ValueError(f"Card {card_id} not found")
    return card


def get_card_history(
    conn: psycopg2.extensions.connection,
    card_id: int,
) -> list[ReviewLog]:
    get_card(conn, card_id)  # raises if not found
    return repo.get_card_history(conn, card_id)


def edit_card(
    conn: psycopg2.extensions.connection,
    card_id: int,
    front: str | None = None,
    back: str | None = None,
    tags: list[str] | None = None,
) -> Card:
    get_card(conn, card_id)
    return repo.update_card(conn, card_id, front=front, back=back, tags=tags)


def delete_card(conn: psycopg2.extensions.connection, card_id: int) -> None:
    get_card(conn, card_id)
    repo.delete_card(conn, card_id)


def suspend_card(conn: psycopg2.extensions.connection, card_id: int) -> None:
    get_card(conn, card_id)
    repo.set_suspended(conn, card_id, True)


def unsuspend_card(conn: psycopg2.extensions.connection, card_id: int) -> None:
    get_card(conn, card_id)
    repo.set_suspended(conn, card_id, False)


def list_cards(conn: psycopg2.extensions.connection, deck_name: str) -> list[Card]:
    deck = get_deck(conn, deck_name)
    return repo.list_cards(conn, deck.id)


def get_study_queue(
    conn: psycopg2.extensions.connection,
    deck_name: str,
    cram: bool = False,
    limit: int = 200,
) -> list[Card]:
    deck = get_deck(conn, deck_name)
    if cram:
        return repo.get_all_cards_for_cram(conn, deck.id)
    return repo.get_due_cards(conn, deck_id=deck.id, limit=limit)


def snapshot_card(card: Card) -> dict:
    return {
        "state": card.state, "due": card.due, "interval": card.interval,
        "ease_factor": card.ease_factor, "reps": card.reps, "lapses": card.lapses,
        "step_index": card.step_index, "suspended": card.suspended,
    }


def review_card(
    conn: psycopg2.extensions.connection,
    card_id: int,
    rating: int,
) -> Card:
    card = get_card(conn, card_id)
    prior = snapshot_card(card)
    update: CardUpdate = schedule(
        {"state": card.state, "interval": card.interval,
         "ease_factor": card.ease_factor, "reps": card.reps,
         "lapses": card.lapses, "step_index": card.step_index,
         "suspended": card.suspended},
        rating=rating,
    )
    if update.interval > 365:
        logger.warning("Card %d scheduled for %d days — unusually large interval",
                       card_id, update.interval)
    repo.update_card_state(
        conn, card_id,
        state=update.state, due=update.due, interval=update.interval,
        ease_factor=update.ease_factor, reps=update.reps, lapses=update.lapses,
        step_index=update.step_index, suspended=update.suspended,
    )
    repo.log_review(
        conn, card_id=card_id, rating=rating,
        prior_state=prior["state"], prior_interval=prior["interval"],
        prior_ease_factor=prior["ease_factor"],
        new_interval=update.interval, new_ease_factor=update.ease_factor,
    )
    logger.debug("Reviewed card %d: rating=%d state=%s->%s interval=%d",
                 card_id, rating, prior["state"], update.state, update.interval)
    return get_card(conn, card_id)


def undo_review(
    conn: psycopg2.extensions.connection,
    card_id: int,
    snapshot: dict,
) -> None:
    repo.restore_card_state(conn, card_id, **snapshot)
    logger.debug("Undid review for card %d", card_id)


def get_stats(
    conn: psycopg2.extensions.connection,
    deck_name: str | None = None,
) -> dict:
    if deck_name:
        deck = get_deck(conn, deck_name)
        counts = repo.get_deck_stats(conn, deck.id)
        counts["deck"] = deck_name
        counts["daily_counts"] = repo.get_daily_counts(conn, days=7, deck_id=deck.id)
        return counts
    return {
        "deck": None,
        "daily_counts": repo.get_daily_counts(conn, days=7),
    }
