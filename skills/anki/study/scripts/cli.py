#!/usr/bin/env python
"""Anki study CLI — machine-friendly JSON interface."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_conn, init_schema
from src import service


def _out(data: object) -> None:
    print(json.dumps({"ok": True, "data": data}, default=str))


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def _card_dict(card) -> dict:
    return {
        "id": card.id, "deck_id": card.deck_id,
        "front": card.front, "back": card.back,
        "tags": card.tags, "state": card.state,
        "due": str(card.due), "interval": card.interval,
        "ease_factor": card.ease_factor, "reps": card.reps,
        "lapses": card.lapses, "suspended": card.suspended,
        "reference": card.reference,
    }


def cmd_deck_create(args, conn):
    deck = service.create_deck(conn, args.name)
    _out({"id": deck.id, "name": deck.name, "created_at": str(deck.created_at)})


def cmd_deck_list(args, conn):
    decks = service.list_decks(conn)
    _out([{"id": d.id, "name": d.name} for d in decks])


def cmd_deck_delete(args, conn):
    service.delete_deck(conn, args.name)
    _out({"deleted": args.name})


def cmd_card_add(args, conn):
    from src.display import REFERENCE_MAX_CHARS
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    reference = args.reference[:REFERENCE_MAX_CHARS] if args.reference else None
    card = service.add_card(conn, deck_name=args.deck,
                             front=args.front, back=args.back,
                             tags=tags, reference=reference)
    _out(_card_dict(card))


def cmd_card_edit(args, conn):
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
    card = service.edit_card(conn, args.id, front=args.front, back=args.back, tags=tags)
    _out(_card_dict(card))


def cmd_card_delete(args, conn):
    service.delete_card(conn, args.id)
    _out({"deleted": args.id})


def cmd_card_list(args, conn):
    cards = service.list_cards(conn, args.deck)
    _out([_card_dict(c) for c in cards])


def cmd_card_get(args, conn):
    card = service.get_card(conn, args.id)
    _out(_card_dict(card))


def cmd_card_history(args, conn):
    history = service.get_card_history(conn, args.id)
    _out([{
        "reviewed_at": str(r.reviewed_at),
        "rating": r.rating,
        "prior_state": r.prior_state,
        "prior_interval": r.prior_interval,
        "new_interval": r.new_interval,
        "prior_ease_factor": r.prior_ease_factor,
        "new_ease_factor": r.new_ease_factor,
    } for r in history])


def cmd_card_suspend(args, conn):
    service.suspend_card(conn, args.id)
    _out({"suspended": args.id})


def cmd_card_unsuspend(args, conn):
    service.unsuspend_card(conn, args.id)
    _out({"unsuspended": args.id})


def cmd_stats(args, conn):
    _out(service.get_stats(conn, deck_name=args.deck))


def cmd_db_ping(args, conn):
    from dbclients.clients.postgres import get_connection_params, PREFERRED_HOST
    params = get_connection_params("anki")
    _out({"host": params["host"], "db": "anki"})


def cmd_study(args, conn):
    """Close DB connection and exec study.py. Do not hold conn open during session."""
    conn.close()
    study_script = Path(__file__).parent / "study.py"
    cmd = [sys.executable, str(study_script)]
    if args.deck:
        cmd += ["--deck", args.deck]
    if args.cram:
        cmd.append("--cram")
    os.execv(sys.executable, cmd)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="anki-study")
    sub = p.add_subparsers(dest="entity", required=True)

    deck_p = sub.add_parser("deck")
    dsub = deck_p.add_subparsers(dest="action", required=True)
    dsub.add_parser("create").add_argument("name")
    dsub.add_parser("list")
    dsub.add_parser("delete").add_argument("name")

    card_p = sub.add_parser("card")
    csub = card_p.add_subparsers(dest="action", required=True)
    ca = csub.add_parser("add")
    ca.add_argument("--deck", required=True)
    ca.add_argument("--front", required=True)
    ca.add_argument("--back", required=True)
    ca.add_argument("--tags", default="")
    ca.add_argument("--reference", default=None, help="Optional citation or source text")
    ce = csub.add_parser("edit")
    ce.add_argument("id", type=int)
    ce.add_argument("--front"); ce.add_argument("--back"); ce.add_argument("--tags")
    csub.add_parser("delete").add_argument("id", type=int)
    csub.add_parser("list").add_argument("--deck", required=True)
    csub.add_parser("get").add_argument("id", type=int)
    csub.add_parser("history").add_argument("id", type=int)
    csub.add_parser("suspend").add_argument("id", type=int)
    csub.add_parser("unsuspend").add_argument("id", type=int)

    st = sub.add_parser("stats")
    st.add_argument("--deck", default=None)

    db_p = sub.add_parser("db")
    dbsub = db_p.add_subparsers(dest="action", required=True)
    dbsub.add_parser("ping")

    sy = sub.add_parser("study")
    sy.add_argument("--deck", default=None)
    sy.add_argument("--cram", action="store_true")

    return p


DISPATCH = {
    ("deck", "create"): cmd_deck_create,
    ("deck", "list"): cmd_deck_list,
    ("deck", "delete"): cmd_deck_delete,
    ("card", "add"): cmd_card_add,
    ("card", "edit"): cmd_card_edit,
    ("card", "delete"): cmd_card_delete,
    ("card", "list"): cmd_card_list,
    ("card", "get"): cmd_card_get,
    ("card", "history"): cmd_card_history,
    ("card", "suspend"): cmd_card_suspend,
    ("card", "unsuspend"): cmd_card_unsuspend,
    ("stats", None): cmd_stats,
    ("db", "ping"): cmd_db_ping,
    ("study", None): cmd_study,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    action = getattr(args, "action", None)

    fn = DISPATCH.get((args.entity, action))
    if fn is None:
        _err(f"Unknown command: {args.entity} {action}")

    try:
        with get_conn() as conn:
            init_schema(conn)
            fn(args, conn)
    except ValueError as e:
        _err(f"Error: {e}")
    except ConnectionError as e:
        _err(f"DB connection failed: {e}")


if __name__ == "__main__":
    main()
