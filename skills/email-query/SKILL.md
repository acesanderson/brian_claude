# email-query

Query Brian's Outlook email database (Postgres + pgvector). Use when asked about emails,
searching for messages, looking up threads, or checking sent/received history.

## Prerequisites

- `uv` installed: https://docs.astral.sh/uv/getting-started/installation/
- `ONEDRIVE` and `POSTGRES_PASSWORD` env vars set
- `outlook-email-project` installed: `cd /Users/bianders/vibe/outlook-email-project && uv pip install -e .`

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
email-query search "topic or phrase" --limit 20
email-query search "topic" --since 2026-01-01 --limit 10
```
Requires headwater ML server running. Returns results ranked by cosine similarity. Emails with NULL embeddings are excluded.

### Keyword / full-text search
```bash
email-query search "exact phrase" --text --limit 20
```
Works without headwater. Searches subject and body_plain via ILIKE. Includes NULL-embedding rows.

### List with filters
```bash
email-query list --folder inbox --limit 20
email-query list --folder sent --limit 10
email-query list --folder all --limit 20
email-query list --from "*.linkedin.com" --limit 20
email-query list --from "user@example.com" --limit 10
email-query list --to "*@gmail.com" --limit 10
email-query list --since 2026-02-01 --limit 20
```

Domain wildcard patterns:
- `*.linkedin.com` matches any `@linkedin.com` or `@subdomain.linkedin.com` sender
- `*@gmail.com` matches any `@gmail.com` sender or recipient
- `user@example.com` exact match (case-insensitive)

### Get full email
```bash
email-query get <message_id>
```
Returns subject, from, to, cc, date, folder, and full body_plain.

### Get full thread
```bash
email-query thread <conversation_id>
```
Returns all emails in the thread in chronological order, each with folder label (inbox/sent).

### Database stats
```bash
email-query stats
```
Shows total email count, inbox/sent breakdown, thread count, embedding coverage, and date range.

## Workflow patterns

**Find and read an email:**
1. `email-query search "topic"` or `email-query search "topic" --text` to find candidates
2. Note the `message_id` from the result
3. `email-query get <message_id>` to read the full body

**Explore a conversation:**
1. `email-query search "topic"` to find an email in the thread
2. Note the `conversation_id` from the result (use `email-query get <message_id>` if needed)
3. `email-query thread <conversation_id>` to read the entire thread

**Find emails from a company:**
```bash
email-query list --from "*.company.com" --limit 20
```

**Find emails to a specific address:**
```bash
email-query list --to "user@domain.com" --limit 20
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
