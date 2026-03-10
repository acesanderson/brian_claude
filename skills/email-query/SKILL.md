# email-query

Query Brian's Outlook email database (Postgres + pgvector). Use when asked about emails,
searching for messages, looking up threads, or checking sent/received history.

## Prerequisites

- `uv` installed: https://docs.astral.sh/uv/getting-started/installation/
- `ONEDRIVE` and `POSTGRES_PASSWORD` env vars set
- `outlook-email-project` installed: `cd /Users/bianders/vibe/outlook-email-project && uv pip install -e .`

## Invocation

`email-query` is NOT on the global PATH. Always invoke via:
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project email-query <command>
```

Do NOT use bare `psql` to query the DB directly — the connection goes through `dbclients`, not raw TCP. `caruana.local` is not reachable via direct psql from this machine.

## When to use this skill

Invoke when the user asks to:
- Find emails about a topic: use `email-query search`
- List recent emails from someone: use `email-query list --from`
- Read a specific email: use `email-query get`
- See a full conversation: use `email-query thread`
- Check DB health or counts: use `email-query stats`

## Commands

### Semantic search (default)
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project email-query search "topic or phrase" --limit 20
uv run --directory /Users/bianders/vibe/outlook-email-project email-query search "topic" --since 2026-01-01 --limit 10
```
Requires headwater ML server running. Returns results ranked by cosine similarity. Emails with NULL embeddings are excluded.

### Keyword / full-text search
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project email-query search "exact phrase" --text --limit 20
```
Works without headwater. Searches subject and body_plain via ILIKE. Includes NULL-embedding rows.

**Note:** `search` has no `--folder` filter. It searches all folders.

### List with filters
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --folder inbox --limit 20
uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --folder sent --limit 10
uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --folder all --limit 20
uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --from "*.linkedin.com" --limit 20
uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --from "user@example.com" --limit 10
uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --to "*@gmail.com" --limit 10
uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --since 2026-02-01 --limit 20
```

Domain wildcard patterns:
- `*.linkedin.com` matches any `@linkedin.com` or `@subdomain.linkedin.com` sender
- `*@gmail.com` matches any `@gmail.com` sender or recipient
- `user@example.com` exact match (case-insensitive)

### Get full email
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project email-query get <message_id>
```
Returns subject, from, to, cc, date, folder, and full body_plain.

**Warning:** `list` and `search` table output truncates message_ids. They cannot be used directly with `get`. Use the Python snippet below to retrieve the full message_id when needed.

### Get full thread
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project email-query thread <conversation_id>
```
Returns all emails in the thread in chronological order, each with folder label (inbox/sent).

### Database stats
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project email-query stats
```
Shows total email count, inbox/sent breakdown, thread count, embedding coverage, and date range.

## Workflow patterns

**Find and read an email:**
1. `email-query search "topic" --text` to find candidates
2. If the message_id is truncated, use the Python snippet below to get the full ID
3. `email-query get <full_message_id>` to read the full body

**Get full message_id when table output truncates it:**
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project python -c "
from dbclients.clients.postgres import get_sync_client
conn = get_sync_client(dbname='emails')
cur = conn.cursor()
cur.execute(\"SELECT message_id, subject FROM emails WHERE subject ILIKE '%keyword%' ORDER BY received_at DESC LIMIT 5\")
for row in cur.fetchall(): print(row)
conn.close()
"
```

**Explore a conversation:**
1. `email-query search "topic" --text` to find an email in the thread
2. Get the full message_id if needed (Python snippet above)
3. `email-query get <message_id>` to get the conversation_id
4. `email-query thread <conversation_id>` to read the entire thread

**Find emails from a company:**
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --from "*.company.com" --limit 20
```

**Find emails to a specific address:**
```bash
uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --to "user@domain.com" --limit 20
```

## Re-syncing new emails

New emails from OneDrive are not synced automatically. To pull in new files:
```bash
sync run
```

## Re-embedding after headwater downtime

If semantic search is unavailable because embeddings are NULL:
```bash
sync re-embed
```
Or re-embed a limited batch first:
```bash
sync re-embed --limit 100
```
