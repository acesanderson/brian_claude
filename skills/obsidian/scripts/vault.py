#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Obsidian vault automation script.

Vault path resolution (in order of precedence):
  1. --vault CLI arg
  2. OBSIDIAN_VAULT env var
  3. Error

Daily notes folder:
  OBSIDIAN_DAILY_NOTES_FOLDER env var (default: "")

Usage:
  uv run scripts/vault.py create "Note Title" --tags tag1 tag2 --body "content"
  uv run scripts/vault.py append "Note Title" "content to append"
  uv run scripts/vault.py daily "content to append"
  uv run scripts/vault.py search "query"
  uv run scripts/vault.py open "Note Title"
  uv run scripts/vault.py ls
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


def resolve_vault(vault_arg: str | None) -> Path:
    vault = vault_arg or os.environ.get("OBSIDIAN_VAULT")
    if not vault:
        sys.exit("Vault path required: pass --vault or set OBSIDIAN_VAULT env var")
    path = Path(vault).expanduser()
    if not path.is_dir():
        sys.exit(f"Vault not found: {path}")
    return path


def note_path(vault: Path, title: str) -> Path:
    slug = re.sub(r"[^\w\s\-]", "", title).strip()
    fname = slug if slug.endswith(".md") else slug + ".md"
    return vault / fname


def build_frontmatter(tags: list[str], aliases: list[str]) -> str:
    if not tags and not aliases:
        return ""
    lines = ["---"]
    if tags:
        lines.append("tags:")
        for t in tags:
            lines.append(f"  - {t}")
    if aliases:
        lines.append("aliases:")
        for a in aliases:
            lines.append(f'  - "{a}"')
    lines.append("---")
    return "\n".join(lines) + "\n"


def cmd_create(vault: Path, args: argparse.Namespace) -> None:
    path = note_path(vault, args.title)
    if path.exists() and not args.force:
        sys.exit(f"Note already exists: {path}\nUse --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = build_frontmatter(args.tags or [], args.aliases or [])
    heading = f"# {args.title}\n\n"
    body = (args.body or "").rstrip() + "\n" if args.body else ""
    path.write_text(fm + heading + body)
    print(path)


def cmd_append(vault: Path, args: argparse.Namespace) -> None:
    path = note_path(vault, args.title)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {args.title}\n\n")
    existing = path.read_text()
    sep = "\n" if existing.endswith("\n") else "\n\n"
    path.write_text(existing + sep + args.content.rstrip() + "\n")
    print(path)


def cmd_daily(vault: Path, args: argparse.Namespace) -> None:
    folder = os.environ.get("OBSIDIAN_DAILY_NOTES_FOLDER", "")
    today = date.today().strftime("%Y-%m-%d")
    daily_dir = vault / folder if folder else vault
    daily_dir.mkdir(parents=True, exist_ok=True)
    path = daily_dir / f"{today}.md"
    if not path.exists():
        path.write_text(f"# {today}\n\n")
    existing = path.read_text()
    sep = "\n" if existing.endswith("\n") else "\n\n"
    path.write_text(existing + sep + args.content.rstrip() + "\n")
    print(path)


def cmd_search(vault: Path, args: argparse.Namespace) -> None:
    query = args.query.lower()
    found = False
    for md in sorted(vault.rglob("*.md")):
        text = md.read_text(errors="replace")
        if query in text.lower():
            rel = md.relative_to(vault)
            if args.show_excerpt:
                for i, line in enumerate(text.splitlines(), 1):
                    if query in line.lower():
                        print(f"{rel}:{i}: {line.strip()}")
                        found = True
                        break
            else:
                print(rel)
                found = True
    if not found:
        print(f"No notes found for: {args.query}")


def cmd_open(vault: Path, args: argparse.Namespace) -> None:
    path = note_path(vault, args.title)
    if not path.exists():
        sys.exit(f"Note not found: {path}")
    vault_name = vault.name
    note_name = path.stem
    uri = f"obsidian://open?vault={vault_name}&file={note_name}"
    subprocess.run(["open", uri], check=False)
    print(uri)


def cmd_ls(vault: Path, args: argparse.Namespace) -> None:
    notes = sorted(vault.rglob("*.md"))
    for note in notes:
        print(note.relative_to(vault))
    print(f"\n{len(notes)} notes")


def main() -> None:
    parser = argparse.ArgumentParser(description="Obsidian vault automation")
    parser.add_argument("--vault", help="Vault path (overrides OBSIDIAN_VAULT)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="Create a new note")
    p_create.add_argument("title")
    p_create.add_argument("--body", help="Initial body content")
    p_create.add_argument("--tags", nargs="*")
    p_create.add_argument("--aliases", nargs="*")
    p_create.add_argument("--force", action="store_true")

    p_append = sub.add_parser("append", help="Append content to a note (creates if absent)")
    p_append.add_argument("title")
    p_append.add_argument("content")

    p_daily = sub.add_parser("daily", help="Append to today's daily note")
    p_daily.add_argument("content")

    p_search = sub.add_parser("search", help="Search notes for a text query")
    p_search.add_argument("query")
    p_search.add_argument("--excerpt", dest="show_excerpt", action="store_true")

    p_open = sub.add_parser("open", help="Open a note in the Obsidian app")
    p_open.add_argument("title")

    sub.add_parser("ls", help="List all notes in the vault")

    args = parser.parse_args()
    vault = resolve_vault(args.vault)

    dispatch = {
        "create": cmd_create,
        "append": cmd_append,
        "daily": cmd_daily,
        "search": cmd_search,
        "open": cmd_open,
        "ls": cmd_ls,
    }
    dispatch[args.cmd](vault, args)


if __name__ == "__main__":
    main()
