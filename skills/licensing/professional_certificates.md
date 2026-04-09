# Professional Certificates — Subskill

**Invoke rarely.** Only when the task is specifically about the Prof Cert BD program. Not for general licensing BD work.

---

## Business Context

Before any strategic Prof Cert work, read:
**`/Users/bianders/morphy/Professional Certificate Context.md`**

Covers: program mechanics (format, scale, engagement funnel), partnership portfolio, enterprise vs. consumer strategy debate, licensing as a Tier 1 vector (Snowflake model), stakeholder map, and current data gaps. Last updated December 2025.

---

## Key Coordinates

| Item | Value |
|---|---|
| Prof Cert Tracker (sheet) | ID: `12IMNi4UVfpn3n5WloNlf-KpJav49z-35POO-xZqOqQI`, tab: "Professional Certificates" (gid: `1382271524`) |
| Trino LP inventory | `hive.u_llsdsgroup.learningpath_inventory` |
| Trino LP engagement | `hive.u_llsdsgroup.lp_lsv_el_engagement_weekly` |
| Trino LP monthly stats | `hive.u_llsdsgroup.test_report_status_learningpath` |

**Sheet column map (A–H):** Partner | Description | Topic/Partner Page | Pro Cert Titles and URLs | Pro Cert LP ID | Courses | Duration (Hrs) | LP Link

Multi-row pattern: partner name, description, and "Click here" in col C appear only on the **first** cert row for a partner. Subsequent cert rows leave A/B/C empty (same pattern as Adobe rows 2+, CSCMP rows 2+, etc.).

---

## Subskill: Update Prof Certs Sheet

Use when asked to add a new LP to the tracker. One automated pass produces ~half the data; HITL steps are required to finish.

### Step 1 — Read the sheet (automated)

Open in browser (hook: use `open`, never Playwright):
```bash
open "https://docs.google.com/spreadsheets/d/12IMNi4UVfpn3n5WloNlf-KpJav49z-35POO-xZqOqQI/edit?gid=1382271524"
```

Read via `read_google_sheets_by_id` (gid: `1382271524`) to understand current structure and locate the partner's existing rows (if any).

### Step 2 — Query Trino for LP metadata (automated)

Invoke the `trino` skill first to check manifest status. Then:

```sql
-- Find the LP
SELECT DISTINCT learningpath_id, learningpath_title, learningpath_slug,
  lp_duration_hours, lp_course_counts
FROM hive.u_llsdsgroup.learningpath_inventory
WHERE LOWER(learningpath_title) LIKE '%<keyword>%'
LIMIT 10
```

```sql
-- Get ordered course list
SELECT DISTINCT li.course_order, ci.course_title
FROM hive.u_llsdsgroup.learningpath_inventory li
JOIN hive.u_llsdsgroup.course_inventory ci ON li.course_id = ci.course_id
WHERE li.learningpath_id = '<lp_id>'
ORDER BY li.course_order
LIMIT 20
```

LP URL: `https://www.linkedin.com/learning/paths/<learningpath_slug>`

**Known data gap:** `lp_course_counts` frequently does not match the number of rows returned by the course join — the inventory can have gaps vs. the live LP. Always flag discrepancies to the user.

### Step 3 — Append to sheet (automated)

```python
write_google_sheets_by_id(
    spreadsheet_id="12IMNi4UVfpn3n5WloNlf-KpJav49z-35POO-xZqOqQI",
    gid=1382271524,
    mode="append",
    input_option="USER_ENTERED",
    values=[[
        "",              # A: empty (sub-row); use partner name if first cert for this partner
        "",              # B: empty (sub-row); use description if first cert
        "",              # C: empty (sub-row); use "Click here" hyperlink if first cert
        "<lp_title>",   # D: Pro Cert Titles and URLs
        "<lp_id>",      # E: Pro Cert LP ID
        "<courses>",    # F: numbered list, \n-separated ("1. Course A\n2. Course B")
        "<duration>",   # G: Duration (Hrs) — from lp_duration_hours
        "<lp_url>",     # H: LP Link
    ]]
)
```

`append` mode places the row at the **bottom of the sheet**. This is expected — see HITL steps.

### HITL Steps (user does these)

1. **Move the row** — Cut the bottom row → in the sheet, right-click on the row immediately *below* the partner's last existing cert → "Insert 1 row above" → paste. Keeps alphabetical ordering and groups certs by partner.

2. **Verify course list** — Cross-check against the live LP page. Trino's `learningpath_inventory` can lag the live product. If `lp_course_counts` and the join count diverged, this step is mandatory.

3. **Column C (new partners only)** — If this is the partner's *first* cert in the sheet, add a "Click here" hyperlink in col C pointing to their topic/brand page on LiL. Existing-partner sub-rows leave C blank.

4. **Row formatting** — Match background color and borders of adjacent partner rows. The Sheets API write does not carry formatting.

5. **Update "Last Updated"** — Cell A1.
