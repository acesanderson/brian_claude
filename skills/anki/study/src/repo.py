from __future__ import annotations
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from src.models import Card, Deck, ReviewLog

if TYPE_CHECKING:
    import psycopg2.extensions


def create_deck(conn: psycopg2.extensions.connection, name: str) -> Deck:
    with conn.cursor() as cur:
        cur.execute("SAVEPOINT create_deck")
        try:
            cur.execute(
                "INSERT INTO decks (name) VALUES (%s) RETURNING id, name, created_at",
                (name,)
            )
            row = cur.fetchone()
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT create_deck")
            raise
        else:
            cur.execute("RELEASE SAVEPOINT create_deck")
    conn.commit()
    return Deck(id=row[0], name=row[1], created_at=row[2])


def get_deck_by_name(conn: psycopg2.extensions.connection, name: str) -> Deck | None:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, created_at FROM decks WHERE name = %s", (name,))
        row = cur.fetchone()
    return Deck(id=row[0], name=row[1], created_at=row[2]) if row else None


def list_decks(conn: psycopg2.extensions.connection) -> list[Deck]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, created_at FROM decks ORDER BY name")
        rows = cur.fetchall()
    return [Deck(id=r[0], name=r[1], created_at=r[2]) for r in rows]


def delete_deck(conn: psycopg2.extensions.connection, deck_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM decks WHERE id = %s", (deck_id,))
    conn.commit()


def add_card(
    conn: psycopg2.extensions.connection,
    deck_id: int,
    front: str,
    back: str,
    tags: list[str] | None = None,
) -> Card:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cards (deck_id, front, back, tags)
            VALUES (%s, %s, %s, %s)
            RETURNING id, deck_id, front, back, tags, created_at,
                      state, due, interval, ease_factor, reps, lapses,
                      step_index, suspended
            """,
            (deck_id, front, back, tags or []),
        )
        row = cur.fetchone()
    conn.commit()
    return _row_to_card(row)


def get_card(conn: psycopg2.extensions.connection, card_id: int) -> Card | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, deck_id, front, back, tags, created_at,
                   state, due, interval, ease_factor, reps, lapses,
                   step_index, suspended
            FROM cards WHERE id = %s
            """,
            (card_id,),
        )
        row = cur.fetchone()
    return _row_to_card(row) if row else None


def update_card(
    conn: psycopg2.extensions.connection,
    card_id: int,
    front: str | None = None,
    back: str | None = None,
    tags: list[str] | None = None,
) -> Card:
    updates, values = [], []
    if front is not None:
        updates.append("front = %s"); values.append(front)
    if back is not None:
        updates.append("back = %s"); values.append(back)
    if tags is not None:
        updates.append("tags = %s"); values.append(tags)
    if not updates:
        return get_card(conn, card_id)
    values.append(card_id)
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE cards SET {', '.join(updates)} WHERE id = %s "
            "RETURNING id, deck_id, front, back, tags, created_at, "
            "state, due, interval, ease_factor, reps, lapses, step_index, suspended",
            values,
        )
        row = cur.fetchone()
    conn.commit()
    return _row_to_card(row)


def update_card_state(
    conn: psycopg2.extensions.connection,
    card_id: int,
    state: str,
    due: datetime,
    interval: int,
    ease_factor: int,
    reps: int,
    lapses: int,
    step_index: int,
    suspended: bool,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE cards SET state=%s, due=%s, interval=%s, ease_factor=%s,
                reps=%s, lapses=%s, step_index=%s, suspended=%s
            WHERE id = %s
            """,
            (state, due, interval, ease_factor, reps, lapses,
             step_index, suspended, card_id),
        )
    conn.commit()


def set_suspended(conn: psycopg2.extensions.connection, card_id: int, suspended: bool) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE cards SET suspended = %s WHERE id = %s", (suspended, card_id))
    conn.commit()


def delete_card(conn: psycopg2.extensions.connection, card_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM cards WHERE id = %s", (card_id,))
    conn.commit()


def list_cards(conn: psycopg2.extensions.connection, deck_id: int) -> list[Card]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, deck_id, front, back, tags, created_at,
                   state, due, interval, ease_factor, reps, lapses,
                   step_index, suspended
            FROM cards WHERE deck_id = %s ORDER BY id
            """,
            (deck_id,),
        )
        rows = cur.fetchall()
    return [_row_to_card(r) for r in rows]


def get_due_cards(
    conn: psycopg2.extensions.connection,
    deck_id: int,
    limit: int = 100,
    now: datetime | None = None,
) -> list[Card]:
    with conn.cursor() as cur:
        if now is None:
            # Use DB-side NOW() to avoid clock skew between client and server.
            cur.execute(
                """
                SELECT id, deck_id, front, back, tags, created_at,
                       state, due, interval, ease_factor, reps, lapses,
                       step_index, suspended
                FROM cards
                WHERE deck_id = %s AND due <= NOW() AND suspended = FALSE
                ORDER BY due ASC
                LIMIT %s
                """,
                (deck_id, limit),
            )
        else:
            cur.execute(
                """
                SELECT id, deck_id, front, back, tags, created_at,
                       state, due, interval, ease_factor, reps, lapses,
                       step_index, suspended
                FROM cards
                WHERE deck_id = %s AND due <= %s AND suspended = FALSE
                ORDER BY due ASC
                LIMIT %s
                """,
                (deck_id, now, limit),
            )
        rows = cur.fetchall()
    return [_row_to_card(r) for r in rows]


def get_all_cards_for_cram(
    conn: psycopg2.extensions.connection,
    deck_id: int,
) -> list[Card]:
    import random
    cards = [c for c in list_cards(conn, deck_id) if not c.suspended]
    random.shuffle(cards)
    return cards


def log_review(
    conn: psycopg2.extensions.connection,
    card_id: int,
    rating: int,
    prior_state: str,
    prior_interval: int,
    prior_ease_factor: int,
    new_interval: int,
    new_ease_factor: int,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO review_log
                (card_id, rating, prior_state, prior_interval, prior_ease_factor,
                 new_interval, new_ease_factor)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (card_id, rating, prior_state, prior_interval, prior_ease_factor,
             new_interval, new_ease_factor),
        )
        row = cur.fetchone()
    conn.commit()
    return row[0]


def delete_last_review_log(conn: psycopg2.extensions.connection, card_id: int) -> None:
    """Delete the most recent review_log entry for this card, identified by highest id."""
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM review_log WHERE id = (
                SELECT id FROM review_log WHERE card_id = %s
                ORDER BY id DESC LIMIT 1
            )
            """,
            (card_id,),
        )
    conn.commit()


def get_card_history(
    conn: psycopg2.extensions.connection,
    card_id: int,
) -> list[ReviewLog]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, card_id, reviewed_at, rating, prior_state,
                   prior_interval, prior_ease_factor, new_interval, new_ease_factor
            FROM review_log WHERE card_id = %s ORDER BY id ASC
            """,
            (card_id,),
        )
        rows = cur.fetchall()
    return [
        ReviewLog(id=r[0], card_id=r[1], reviewed_at=r[2], rating=r[3],
                  prior_state=r[4], prior_interval=r[5], prior_ease_factor=r[6],
                  new_interval=r[7], new_ease_factor=r[8])
        for r in rows
    ]


def get_deck_stats(conn: psycopg2.extensions.connection, deck_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT state, suspended, COUNT(*)
            FROM cards WHERE deck_id = %s
            GROUP BY state, suspended
            """,
            (deck_id,),
        )
        rows = cur.fetchall()
    counts: dict[str, int] = {"new": 0, "learning": 0, "review": 0,
                               "relearning": 0, "suspended": 0, "total": 0}
    for state, suspended, count in rows:
        counts["total"] += count
        if suspended:
            counts["suspended"] += count
        else:
            counts[state] = counts.get(state, 0) + count
    return counts


def get_daily_counts(
    conn: psycopg2.extensions.connection,
    days: int = 7,
    deck_id: int | None = None,
) -> list[dict]:
    """
    Return review counts per day for the last N days.
    Uses parameterized interval: NOW() - (%s * INTERVAL '1 day')
    """
    if deck_id is not None:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DATE(rl.reviewed_at AT TIME ZONE 'UTC') AS day, COUNT(*)
                FROM review_log rl
                JOIN cards c ON rl.card_id = c.id
                WHERE c.deck_id = %s
                  AND rl.reviewed_at >= NOW() - (%s * INTERVAL '1 day')
                GROUP BY day
                ORDER BY day DESC
                """,
                (deck_id, days),
            )
            rows = cur.fetchall()
    else:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DATE(reviewed_at AT TIME ZONE 'UTC') AS day, COUNT(*)
                FROM review_log
                WHERE reviewed_at >= NOW() - (%s * INTERVAL '1 day')
                GROUP BY day
                ORDER BY day DESC
                """,
                (days,),
            )
            rows = cur.fetchall()
    return [{"date": str(r[0]), "reviewed": r[1]} for r in rows]


def restore_card_state(
    conn: psycopg2.extensions.connection,
    card_id: int,
    state: str,
    due: datetime,
    interval: int,
    ease_factor: int,
    reps: int,
    lapses: int,
    step_index: int,
    suspended: bool,
) -> None:
    update_card_state(conn, card_id, state, due, interval, ease_factor,
                      reps, lapses, step_index, suspended)
    delete_last_review_log(conn, card_id)


def _row_to_card(row: tuple) -> Card:
    return Card(
        id=row[0], deck_id=row[1], front=row[2], back=row[3],
        tags=list(row[4]) if row[4] else [],
        created_at=row[5], state=row[6], due=row[7],
        interval=row[8], ease_factor=row[9], reps=row[10],
        lapses=row[11], step_index=row[12], suspended=row[13],
    )
