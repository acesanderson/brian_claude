#!/usr/bin/env python
"""Anki study REPL — line-by-line interactive study session."""
from __future__ import annotations
import argparse
import sys
import tty
import termios
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule

from src.db import get_conn, init_schema
from src import service
from src.models import Card, SessionStats

console = Console()


def read_key() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def render_card_side(text: str) -> None:
    console.print(Markdown(text))


def print_header(deck_name: str, total: int, position: int) -> None:
    console.print(Rule(f"[bold]{deck_name}[/bold]  Card {position + 1}/{total}"))


def prompt_add_card(conn, current_deck: str) -> None:
    console.print("\n[dim]Add card[/dim]")
    deck_input = input(f"  Deck (default: {current_deck}): ").strip()
    deck_name = deck_input or current_deck
    front = input("  Front: ").strip()
    if not front:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    back = input("  Back: ").strip()
    if not back:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    tags_raw = input("  Tags (comma-separated, optional): ").strip()
    tags = [t.strip() for t in tags_raw.split(",")] if tags_raw else []
    try:
        card = service.add_card(conn, deck_name=deck_name, front=front, back=back, tags=tags)
        console.print(f"[green]Added card {card.id} to '{deck_name}'.[/green]")
        console.print("[dim](Card not added to current session queue.)[/dim]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


def print_session_summary(stats: SessionStats) -> None:
    console.print(Rule("Session complete"))
    if stats.reviewed == 0:
        console.print("[dim]No cards reviewed.[/dim]")
        return
    console.print(f"  Reviewed: {stats.reviewed}")
    for label, count in [("Again", stats.again), ("Hard", stats.hard),
                          ("Good", stats.good), ("Easy", stats.easy)]:
        pct = round(count / stats.reviewed * 100)
        console.print(f"  {label:<6} {count:>3}  ({pct}%)")


def run_session(conn, deck_name: str, cram: bool) -> None:
    queue = service.get_study_queue(conn, deck_name=deck_name, cram=cram)
    if not queue:
        console.print(f"[green]Nothing due in '{deck_name}'.[/green]")
        return

    stats = SessionStats()
    # undo_stack: list of (card_id, snapshot, rating) — rating needed for unrecord()
    undo_stack: list[tuple[int, dict, int]] = []
    i = 0

    while i < len(queue):
        card = queue[i]
        console.clear()
        print_header(deck_name, len(queue), i)
        console.print()
        render_card_side(card.front)
        console.print()
        console.print("[dim]Press ENTER to flip...[/dim]")

        while True:
            key = read_key()
            if key in ("\r", "\n", " "):
                break
            elif key == "q":
                print_session_summary(stats)
                return

        console.print(Rule())
        render_card_side(card.back)
        console.print()
        console.print(
            "  [bold cyan][1][/bold cyan] Again  "
            "[bold yellow][2][/bold yellow] Hard  "
            "[bold green][3][/bold green] Good  "
            "[bold blue][4][/bold blue] Easy  "
            "[dim][a][/dim] Add  [dim][u][/dim] Undo  [dim][q][/dim] Quit"
        )

        while True:
            key = read_key().lower()
            if key in ("1", "2", "3", "4"):
                rating = int(key)
                snapshot = service.snapshot_card(card)
                try:
                    updated = service.review_card(conn, card_id=card.id, rating=rating)
                    stats.record(rating)
                    undo_stack.append((card.id, snapshot, rating))
                    if updated.suspended:
                        console.print(
                            f"\n[yellow]Leech: card {card.id} suspended after "
                            f"{updated.lapses} lapses.[/yellow]"
                        )
                        read_key()  # pause so user sees the warning
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                i += 1
                break
            elif key == "a":
                prompt_add_card(conn, current_deck=deck_name)
                console.print(
                    "  [bold cyan][1][/bold cyan] Again  "
                    "[bold yellow][2][/bold yellow] Hard  "
                    "[bold green][3][/bold green] Good  "
                    "[bold blue][4][/bold blue] Easy  "
                    "[dim][a][/dim] Add  [dim][u][/dim] Undo  [dim][q][/dim] Quit"
                )
            elif key == "u":
                if undo_stack:
                    prev_id, prev_snap, prev_rating = undo_stack.pop()
                    service.undo_review(conn, card_id=prev_id, snapshot=prev_snap)
                    stats.unrecord(prev_rating)
                    i = max(0, i - 1)
                    console.print("[dim]Undone.[/dim]")
                else:
                    console.print("[dim]Nothing to undo.[/dim]")
                break
            elif key == "q":
                print_session_summary(stats)
                return

    print_session_summary(stats)


def main() -> None:
    if not sys.stdin.isatty():
        print("Error: study requires an interactive terminal", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(prog="anki-study")
    parser.add_argument("--deck", default=None)
    parser.add_argument("--cram", action="store_true")
    args = parser.parse_args()

    try:
        with get_conn() as conn:
            init_schema(conn)

            if args.deck is None:
                decks = service.list_decks(conn)
                if not decks:
                    console.print("[red]No decks found. Add cards first.[/red]")
                    sys.exit(1)
                console.print("Available decks:")
                for d in decks:
                    console.print(f"  {d.name}")
                deck_name = input("Deck: ").strip()
            else:
                deck_name = args.deck

            # Validate deck exists before entering session
            service.get_deck(conn, deck_name)  # raises ValueError if not found
            run_session(conn, deck_name=deck_name, cram=args.cram)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except ConnectionError as e:
        console.print(f"[red]DB connection failed: {e}[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")


if __name__ == "__main__":
    main()
