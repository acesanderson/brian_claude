"""Runner script for the claude-history Claude Code skill.

Imports from claude_history.skill, handles argparse, serializes results to JSON on stdout.

Usage (via uv):
  uv run --directory ~/vibe/claude-history-project python ~/.claude/skills/claude-history/run.py search "QUERY"
  uv run --directory ~/vibe/claude-history-project python ~/.claude/skills/claude-history/run.py sessions
  uv run --directory ~/vibe/claude-history-project python ~/.claude/skills/claude-history/run.py turns SESSION_ID
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime


def _serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"not serializable: {type(obj)}")


def cmd_search(args: argparse.Namespace) -> list[dict]:
    from claude_history.skill import search

    return search(
        query=args.query,
        mode=args.mode,
        limit=args.limit,
        offset=args.offset,
        include_subagents=args.subagents,
    )


def cmd_sessions(args: argparse.Namespace) -> list[dict]:
    from claude_history.skill import list_sessions

    since = datetime.fromisoformat(args.since) if args.since else None
    until = datetime.fromisoformat(args.until) if args.until else None

    return list_sessions(
        project=args.project,
        since=since,
        until=until,
        include_subagents=args.subagents,
        limit=args.limit,
        offset=args.offset,
    )


def cmd_turns(args: argparse.Namespace) -> list[dict]:
    from claude_history.skill import get_session_turns

    return get_session_turns(
        session_id=args.session_id,
        offset=args.offset,
        limit=args.limit,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="claude-history skill runner")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # search
    p_search = sub.add_parser("search", help="Search turn content")
    p_search.add_argument("query")
    p_search.add_argument("--mode", choices=["fts", "semantic", "hybrid"], default="hybrid")
    p_search.add_argument("--limit", type=int, default=20)
    p_search.add_argument("--offset", type=int, default=0)
    p_search.add_argument("--subagents", action="store_true", default=False)

    # sessions
    p_sessions = sub.add_parser("sessions", help="List sessions")
    p_sessions.add_argument("--project", default=None)
    p_sessions.add_argument("--since", default=None, help="YYYY-MM-DD")
    p_sessions.add_argument("--until", default=None, help="YYYY-MM-DD")
    p_sessions.add_argument("--limit", type=int, default=20)
    p_sessions.add_argument("--offset", type=int, default=0)
    p_sessions.add_argument("--subagents", action="store_true", default=False)

    # turns
    p_turns = sub.add_parser("turns", help="Get turns for a session")
    p_turns.add_argument("session_id")
    p_turns.add_argument("--limit", type=int, default=50)
    p_turns.add_argument("--offset", type=int, default=0)

    args = parser.parse_args()

    try:
        if args.cmd == "search":
            results = cmd_search(args)
        elif args.cmd == "sessions":
            results = cmd_sessions(args)
        else:
            results = cmd_turns(args)
    except Exception as exc:
        print(f"claude-history: {exc}", file=sys.stderr)
        print("[]")
        sys.exit(1)

    print(json.dumps(results, default=_serialize))


if __name__ == "__main__":
    main()
