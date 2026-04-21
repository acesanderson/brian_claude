# Correspondence Lookup Procedure

Triggers: "email history [partner]", "check correspondence", "pull emails", "have we emailed", "what's our email history with", "correspondence with".

1. Read `partners/<slug>/notes.md` to extract the partner domain from the **Website** field
   (e.g., `anaconda.com` from `https://anaconda.com`).
2. Run all three queries in parallel:
   ```bash
   # Inbound
   uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --from "*.domain.com" --limit 50
   # Outbound
   uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --to "*@domain.com" --limit 50
   # Broad text search (catches name variants, forwarded threads, etc.)
   uv run --directory /Users/bianders/vibe/outlook-email-project email-query search "Partner Name" --text --limit 20 --no-noreply --folder inbox
   ```
3. Deduplicate across the three result sets (same subject + date = same message).
   Sort chronologically ascending.
4. Overwrite the `## Correspondence Log` section in `partners/<slug>/notes.md`:
   ```markdown
   ## Correspondence Log
   _Last pulled: YYYY-MM-DD_

   | Date | Dir | Subject | Contact |
   |---|---|---|---|
   | 2026-03-01 | inbound | Re: LinkedIn Learning partnership | jess@anaconda.com |
   | 2026-03-05 | sent | Re: LinkedIn Learning partnership | jess@anaconda.com |
   ```
   - **Dir**: `inbound` (folder=inbox) or `sent` (folder=sent)
   - **Contact**: the external party's address (from for inbound, to for sent)
   - If a message is part of a thread worth reading, note the conversation_id in a trailing comment
5. Append to `manifest.md`:
   `- YYYY-MM-DD | correspondence-pull | partners/<slug>/notes.md | N emails (X inbound, Y sent)`
6. Surface a brief summary: total count, date range, most recent exchange, any open threads
   (sent with no reply, or reply awaiting response).

**Ad-hoc search flags** (for `email-query search`):
- `--before YYYY-MM-DD` / `--since YYYY-MM-DD` — date bounds
- `--from-domain domain.com` — only emails from that domain
- `--exclude-domain domain.com` — exclude a domain (repeatable)
- `--no-noreply` — strip noreply/donotreply senders
- `--folder inbox|sent` — scope to a folder (default: all)
