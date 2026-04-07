# Licensing Tooling Reference

Supplemental implementation details for the licensing skill. Load specific sections on demand — don't read end-to-end.

---

## Sync Gate Log

When Brian says "sync gate log" (or "sync gate log to sheet"):

1. Read `gate_log.json`.
2. Read `context/google_docs.json` to find the gate log sheet ID under `"gate_log_sheet"`.
   - If not yet registered: create a new Google Sheet named "Licensing — Gate Log" via `create_google_sheets_spreadsheet`, register under `"gate_log_sheet"` with `"permissions": "read-write"`, append to `manifest.md`.
3. Build payload: header row + one data row per entry, columns: id, partner_slug, partner_display, course_title, course_url, gate, gate_name, submitted_date, decided_date, velocity_days, decision, reason_code, reason_detail, decided_by, logged_date, notes.
4. Write via `write_google_sheets_by_id` — full overwrite of tab "Gate Log" (create if absent). `gate_log.json` is always the SOT.
5. Append to `manifest.md`: `- YYYY-MM-DD | synced | gate_log.json → Google Sheet | <N> entries`

---

## IMPORTRANGE + QUERY Formulas (Google Sheets API)

When writing `QUERY(IMPORTRANGE(...))` formulas via the API (`input_option: USER_ENTERED`):
- Use `Col4 is not null` NOT `Col4 <> ''` — the empty-string literal gets mangled in transit and causes PARSE_ERROR
- Avoid `LABEL` clauses in QUERY strings — single quotes inside label names also cause parse errors
- For custom stage ordering, use separate `COUNTIF(IMPORTRANGE(...), "stage_name")` cells rather than QUERY+ORDER BY — gives exact column control and avoids sort limitations
- Always create a fresh sheet for IMPORTRANGE dashboards; pre-existing data in cells causes formula conflicts
- IMPORTRANGE requires one-time manual authorization in the UI (click "Allow access" on first open)

---

## Catalog Row Batching (write_google_sheets_by_id)

`write_google_sheets_by_id` has an inline parameter size limit. Passing a large `values` array causes the tool to store output as a file rather than returning it inline — making it inaccessible as a parameter. Fix: write in batches of ≤40 rows.

```bash
# Print one batch to stdout — paste directly as `values` in the tool call
python3 -c "
import json
with open('partners/<slug>/catalog.json') as f:
    courses = json.load(f)
cols = ['provider','title','url','format','level','duration','category','date_scraped']
rows = [[c.get(col,'') or '' for col in cols] for c in courses]
print(json.dumps(rows[0:40]))   # change slice per batch: [40:80], [80:120], etc.
"
```

Call sequence:
1. `overwrite` — header row only: `[["provider","title","url","format","level","duration","category","date_scraped"]]`
2. `append` — batch 1: `rows[0:40]`
3. `append` — batch 2: `rows[40:80]`
4. Continue until done. Expected final row count = 1 + len(courses).

---

## Trino — Detailed Table Notes

**`u_llsdsgroup.courseperformance_sc_dash`**
- Grain: `week_end_date` (YYYYMMDD int) × `course_id` × `learner_type` × learner demographics
- **SUM metric columns** — naive row counts will undercount; always use SUM
- Date range: 2025-01-11 → present; most recent partition: `week_end_date = 20260314`
  Run `SELECT MAX(week_end_date) FROM u_llsdsgroup.courseperformance_sc_dash` to confirm current partition.
- Access: open (no permission request needed as of 2026-03-18)
- Software/vendor filters: `course_primary_software`, `course_primary_software_provider`

Full column reference and query patterns: `~/licensing/context/metrics-definitions.md`

---

## Catalog DB — UfB Flag

**UfB flag (`platform_courses.ufb`)**: Boolean marking courses in the Udemy for Business catalog (~11,989 courses, 7.3% of 164K). UfB courses have a contractual exclusivity clause — instructors are bound to Udemy for those specific courses. Treat as a soft blocker. Exception: high-tier instructors (~200K+ reviews) have occasionally negotiated carve-outs.

Two sourcing modes for `platform-search`:
- `--ufb exclude` (default): sourcing mode — licensable non-UfB candidates only
- `--ufb only`: benchmark mode — what the best content on a topic looks like (mostly blocked)

Review count gap between modes: typically 10–50x. Non-UfB Udemy content skews toward lower-volume instructors.

Refresh UfB flag:
```bash
curl -sL "https://info.udemy.com/rs/udemy/images/UdemyforBusinessCourseList.pdf" -o /tmp/ufb.pdf
uv run --project ~/vibe/licensing-project/catalog python scripts/load_ufb.py /tmp/ufb.pdf
```

---

## Catalog DB — industry_courses Tiers

Ingested 2026-03-31 from sheet `1rPrvwU7XoarZU0dGDXnrt5YrJzBcJpCfigkLks7SrEw`. Five tiers:
- `lps_strategic` — 63 major enterprise accounts (Adobe, Cisco, Microsoft, SAP, ServiceNow, etc.)
- `lps_targeted` — 700 additional targeted accounts
- `frontier` — 13 Frontier Firms (includes `is_strategic_account` flag)
- `research` — 1,606 companies with training-evidence research (confidence_score, evidence_url, etc.)
- `skills` — 1,213 skill-cluster phrases (stored in `company` column; rarely useful for company search)

Re-ingest (full refresh): `catalog industry-ingest /tmp/industry_courses_all.json`

---

## Catalog DB — Interest Form Refresh

Refresh Lake 3 (interest form) monthly:
1. Run the Trino query at `~/.claude/skills/licensing/queries/interest_form.sql` via `execute_trino_query` MCP
2. Write result to `~/licensing/interest_form_YYYY-MM-DD.json`
3. Run: `uv run --project ~/vibe/licensing-project/catalog python /Users/bianders/vibe/licensing-project/catalog/scripts/load_interest_form.py ~/licensing/interest_form_YYYY-MM-DD.json`
