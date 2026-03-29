# claude-history

Search and browse past Claude Code session transcripts stored in Postgres.

## When to use this skill

Trigger phrases:
- "search my history for ..."
- "find sessions where I worked on ..."
- "what did I do with X last week / last month"
- "show me past sessions in project Y"
- "look up [topic] in my Claude history"
- "find when I last worked on [technology / bug / feature]"
- "what sessions do I have for [project]"
- "show me what was said in session [id]"

## Prerequisites

- **uv** — Install: https://docs.astral.sh/uv/getting-started/installation/
- `~/vibe/claude-history-project` must exist with a `pyproject.toml` containing the DB dependencies (this is Brian's personal project — not portable without it)
- PostgreSQL database accessible via WireGuard VPN

## How to invoke

Run the runner script via `uv run`:

```bash
uv run --directory ~/vibe/claude-history-project python ~/.claude/skills/claude-history/run.py <subcommand> [args]
```

### Subcommands

**search** — find turns matching a query (default: hybrid FTS + semantic)
```bash
python run.py search "QUERY" [--mode fts|semantic|hybrid] [--limit 20] [--offset 0] [--subagents]
```

**sessions** — list sessions, optionally filtered by project or date range
```bash
python run.py sessions [--project NAME] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--limit 20] [--offset 0] [--subagents]
```

**turns** — get all turns in a specific session
```bash
python run.py turns SESSION_ID [--limit 50] [--offset 0]
```

## Choosing the right function

| User intent | Subcommand | Notes |
|-------------|-----------|-------|
| Find content matching a keyword or concept | `search` | Use hybrid mode (default) for best results |
| Exact keyword search, no embeddings loaded | `search --mode fts` | Falls back automatically if no embeddings |
| List recent sessions, browse what exists | `sessions` | Filter by --project for focused browsing |
| Read what was said in a specific session | `turns SESSION_ID` | Paginate with --offset if session is large |

## Pagination guidance

- Default limit is 20 for search/sessions, 50 for turns.
- Always offer to fetch more if the user's answer might be in later pages.
- For `turns`, large sessions (>50 turns) require multiple calls with increasing `--offset`.
- Sessions with many tool-only turns will have sparse `content_text`; those turns are stored but not surfaced in search results.

## Output format

All subcommands print a JSON array to stdout. Parse and present the relevant fields to the user.

Key fields:
- `search` results: `session_id`, `project_name`, `title`, `role`, `content_text`, `ts`, `score`
- `sessions` results: `session_id`, `project_name`, `title`, `started_at`, `ended_at`, `turn_count`, `first_message_snippet`
- `turns` results: `seq`, `role`, `content_text`, `ts`

Timestamps are ISO 8601 UTC. Format them for readability when presenting to the user.

## Notes

- Requires VPN to be up (Postgres is on the local network via WireGuard). If DB is unavailable, the script exits with an error message on stderr and empty array on stdout.
- Subagents are excluded by default. Pass `--subagents` to include them.
- `title` may be `null` for recently ingested sessions whose title hasn't been resolved yet.
