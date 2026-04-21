# Post-Scrape Catalog Sync

Fires after any catalog scrape writes `partners/<slug>/report.md`.

1. Read `context/google_docs.json` to get `catalog_index.id`.
2. Get the course count from the DB:
   ```bash
   uv run --project ~/vibe/licensing-project/catalog catalog providers
   ```
   Find the row for this provider slug and read the `Courses` column.
3. Create a catalog sheet for this partner:
   - If no sheet exists yet: create one via `create_google_sheets_spreadsheet`
     titled `"[Partner] — Course Catalog ([Month Year])"`. Write a header row:
     `provider, title, url, format, level, duration, category, date_scraped`.
     `level` must be one of: `Beginner` | `Intermediate` | `Advanced`. Map raw partner
     values to this enum before writing (e.g., "Introductory" → Beginner, "Professional"
     → Intermediate). Register in `context/google_docs.json` under `"read_write_docs"`
     with `"permissions": "read-write"` and a description noting course count and date.
   - If a sheet already exists (check `google_docs.json`): skip creation.
4. Append one row to the catalog index sheet (`catalog_index.id`) via
   `write_google_sheets_by_id` (mode: append):

   | Partner | Catalog Sheet URL | Context | Courses | Status | Date Scraped | Notes |

   - **Context (col C):** `[Stage] — [POC]. [1-2 sentence description.]`
     Stage must be from the official enum — see `~/.claude/skills/licensing/pipeline-stages.md`.
   - **Courses (col E):** from the DB (step 2), not from any file.
   - **Status enum:** `complete | partial | blocked | pending`
     - `complete` — full catalog, no known gaps
     - `partial` — scrape incomplete (auth/JS walls); more data potentially recoverable
     - `blocked` — structural issue (no catalog, wrong format, MIT-licensed) — don't retry
     - `pending` — scrape dispatched, not yet complete

5. Append to `manifest.md`:
   `- YYYY-MM-DD | synced | catalog_index → Google Sheet | <Slug>: N courses`

6. Clean up temp files:
   ```bash
   rm -f /tmp/scrape_<slug>.json
   rm -f ~/licensing/scrape_<slug>.py
   ```
