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


def _open_conn():
    import os
    from dbclients.clients.postgres import get_postgres_client

    db_name = os.environ.get("CH_DB", "claude_history")
    return get_postgres_client(client_type="context_db", dbname=db_name)()


def cmd_alias(args: argparse.Namespace) -> list[dict]:
    from claude_history import db

    with _open_conn() as conn:
        if args.alias_cmd == "set":
            db.set_alias(conn, args.alias, args.session_id)
            return [{"alias": args.alias, "session_id": args.session_id}]
        elif args.alias_cmd == "get":
            session_id = db.get_alias(conn, args.alias)
            if session_id is None:
                print(f"claude-history: alias '{args.alias}' not found", file=sys.stderr)
                sys.exit(1)
            return [{"alias": args.alias, "session_id": session_id}]
        elif args.alias_cmd == "list":
            return db.list_aliases(conn)
        elif args.alias_cmd == "delete":
            deleted = db.delete_alias(conn, args.alias)
            return [{"alias": args.alias, "deleted": deleted}]
    return []


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

    # alias
    p_alias = sub.add_parser("alias", help="Manage session aliases")
    alias_sub = p_alias.add_subparsers(dest="alias_cmd", required=True)

    p_alias_set = alias_sub.add_parser("set", help="Create or update an alias")
    p_alias_set.add_argument("alias")
    p_alias_set.add_argument("session_id")

    p_alias_get = alias_sub.add_parser("get", help="Resolve an alias to a session_id")
    p_alias_get.add_argument("alias")

    alias_sub.add_parser("list", help="List all aliases")

    p_alias_del = alias_sub.add_parser("delete", help="Delete an alias")
    p_alias_del.add_argument("alias")

    args = parser.parse_args()

    try:
        if args.cmd == "search":
            results = cmd_search(args)
        elif args.cmd == "sessions":
            results = cmd_sessions(args)
        elif args.cmd == "alias":
            results = cmd_alias(args)
        else:
            results = cmd_turns(args)
    except Exception as exc:
        print(f"claude-history: {exc}", file=sys.stderr)
        print("[]")
        sys.exit(1)

    print(json.dumps(results, default=_serialize))


if __name__ == "__main__":
    main()
