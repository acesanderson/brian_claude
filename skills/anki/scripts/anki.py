"""Anki flashcard CLI — pipe-delimited CSV storage."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

STATE_DIR = Path.home() / ".local" / "state" / "anki"


def deck_path(deck_name: str) -> Path:
    safe = re.sub(r"[^\w\s-]", "", deck_name).strip()
    safe = re.sub(r"[\s_]+", "_", safe)
    return STATE_DIR / f"{safe}.csv"


def deck_display_name(path: Path) -> str:
    return path.stem.replace("_", " ")


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def add_cards(deck_name: str, cards: list[dict]) -> int:
    ensure_state_dir()
    path = deck_path(deck_name)
    new_file = not path.exists()

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="|")
        if new_file:
            writer.writerow(["front", "back"])
        for card in cards:
            writer.writerow([card["front"], card["back"]])

    return len(cards)


def list_decks() -> None:
    ensure_state_dir()
    decks = sorted(STATE_DIR.glob("*.csv"))
    if not decks:
        print("No decks found.")
        return

    print(f"{'Deck':<30} {'Cards':>6}")
    print("-" * 38)
    for path in decks:
        with open(path, encoding="utf-8") as f:
            count = sum(1 for _ in f) - 1  # subtract header
        print(f"{deck_display_name(path):<30} {max(0, count):>6}")


def list_cards(deck_name: str) -> None:
    path = deck_path(deck_name)
    if not path.exists():
        print(f"Deck '{deck_name}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="|")
        rows = list(reader)

    if len(rows) <= 1:
        print("No cards in this deck.")
        return

    for i, row in enumerate(rows[1:], 1):
        if len(row) >= 2:
            print(f"[{i}] Q: {row[0]}")
            print(f"    A: {row[1]}")
            print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Anki flashcard CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a single card to a deck")
    add_parser.add_argument("--deck", required=True)
    add_parser.add_argument("--front", required=True)
    add_parser.add_argument("--back", required=True)

    batch_parser = subparsers.add_parser("add-batch", help="Add cards from a JSON file")
    batch_parser.add_argument("--deck", required=True)
    batch_parser.add_argument("--file", required=True, help="JSON file: [{front, back}, ...]")

    subparsers.add_parser("list-decks", help="List all decks with card counts")

    lc_parser = subparsers.add_parser("list-cards", help="List cards in a deck")
    lc_parser.add_argument("--deck", required=True)

    args = parser.parse_args()

    if args.command == "add":
        count = add_cards(args.deck, [{"front": args.front, "back": args.back}])
        print(f"Added {count} card(s) to deck '{args.deck}'.")

    elif args.command == "add-batch":
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(file_path, encoding="utf-8") as f:
            cards = json.load(f)
        if not isinstance(cards, list):
            print("Expected a JSON array of {front, back} objects.", file=sys.stderr)
            sys.exit(1)
        count = add_cards(args.deck, cards)
        print(f"Added {count} card(s) to deck '{args.deck}'.")

    elif args.command == "list-decks":
        list_decks()

    elif args.command == "list-cards":
        list_cards(args.deck)


if __name__ == "__main__":
    main()
