# Generate TOCs — Subskill

Produces completed PTOC Cosmo Template Google Sheets for a licensed partner's submitted courses.
One sheet per course, placed in a partner-specific Drive folder, with chapter and video names pre-populated in cols C and G.

---

## Prerequisites

- Captain MCP: handles sheet writes, file moves, and Drive searches as bianderson@linkedin.com
- Service account (for rename only): `/Users/bianders/.config/gcp/automated-lodge-491821-a1-0febab0041c3.json`
  - Email: `protean-topic@automated-lodge-491821-a1.iam.gserviceaccount.com`
  - Can rename/update Drive files shared with it; cannot create files (no Drive quota)
- TOC pool: `1PXu7CEkvyBtsaS3cBkOUIoaNDdT_Zldz` (see `context/google_docs.json` → `toc_blank_pool`)
- Cleaned template (source of truth for pool): `15G2baSIDGNSbUcraomNlzD-px5C9GZgj7iuKEHHWEMw` (gid `1342669638` = TOC tab)

---

## Golden Path

### Phase 1 — Scrape course structure

**Public course pages:** Use `WebFetch` first — fast, no browser needed:
```
WebFetch(url=COURSE_URL, prompt="Extract all chapter and video names as a structured list")
```

**Gated/auth-required pages:** Fall back to Playwright + CDP (Chrome must be running with `--remote-debugging-port=9222`, user logged in to the LMS):

```python
# /// script
# dependencies = ["playwright"]
# ///
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].new_page()
    page.goto(COURSE_URL, wait_until="networkidle")
    # Thinkific selectors:
    for btn in page.locator(".accordion-button.collapsed").all():
        btn.click(); page.wait_for_timeout(300)
    chapters = page.locator(".accordion-item").all()
    # extract .accordion-button text (chapter) + .course-curriculum__title text (videos)
```

For other LMS platforms, inspect the DOM and adapt selectors — look for chapter/lesson hierarchy.

---

### Phase 2 — Compute row data

The TOC tab row structure (BD responsibility only):
- **B1**: course title
- **B2**: partner name
- **Chapter rows** (row 8+): col A = chapter number (`1.`), col C = chapter name
- **Video rows**: col E = video number (`1.1`), col G = video name

All other columns (Chapter Id, Video Id, Raw Time, Learning Goal, Video Filename, etc.) are filled by production — leave blank.

---

### Phase 3 — Claim a blank from the TOC pool

Search for the lowest-numbered available blank in the TOC Templates folder:

```
Captain MCP: search_google_drive(
    query="name contains 'TOC Blank' and parents in '1PXu7CEkvyBtsaS3cBkOUIoaNDdT_Zldz'",
    order_by="name asc",
    max_results=1
)
```

Note the file ID — this is the sheet you'll write into.

**Pool replenishment:** When the pool runs low (< 10 remaining), Brian runs the
`generateTOCPool` function in the `generate_templates.gs` script:
- Account: `bianderson@linkedin.com`
- Location: [script.google.com](https://script.google.com) → project **"PTOC Template Scripts (go/PTOC)"**
- Takes ~2-3 min → generates 100 new blanks in the TOC Templates folder

---

### Phase 4 — Write TOC data (Captain MCP)

Two surgical writes — do NOT overwrite the entire sheet:

**Write 1 — header cells only (B1:B2):**
```
write_google_sheets_by_id(
    spreadsheet_id=BLANK_ID,
    sheet="TOC",
    range_a1="TOC!B1:B2",
    mode="overwrite",
    values=[["Course Title"], ["Partner Name"]]
)
```

**Write 2 — TOC content from row 8:**
```
write_google_sheets_by_id(
    spreadsheet_id=BLANK_ID,
    sheet="TOC",
    range_a1="TOC!A8",
    mode="overwrite",
    values=[
        ["1.", "", "Chapter Name", "", "", "", ""],   # chapter row
        ["", "", "", "", "1.1", "", "Video Name"],    # video row
        ...
    ]
)
```

Never write rows 1–7 wholesale — the template has formatting and formulas there that must be preserved. Only touch B1, B2, and A8 onwards.

---

### Phase 5 — Rename, move, and register

**ORDERING IS CRITICAL: always rename before moving.**
The TOC Templates pool folder is shared with the service account. After moving a file
to a partner folder (which is NOT shared with the service account), the service account
loses access and the rename will fail. Do rename → move, never move → rename.

**Rename** via service account (Captain MCP has no rename tool):
```bash
uv run --with google-auth --with google-api-python-client python3 - <<'EOF'
from google.oauth2 import service_account
from googleapiclient.discovery import build
from pathlib import Path

creds = service_account.Credentials.from_service_account_file(
    str(Path.home() / ".config/gcp/automated-lodge-491821-a1-0febab0041c3.json"),
    scopes=["https://www.googleapis.com/auth/drive"]
)
drive = build("drive", "v3", credentials=creds)
drive.files().update(fileId=FILE_ID, body={"name": "Partner — Course Name TOC"}, fields="id,name").execute()
EOF
```

**Move** to partner folder:
```
Captain MCP: move_google_drive_file(file_id=BLANK_ID, destination_folder_id=PARTNER_FOLDER_ID)
```

**Register** in `context/google_docs.json` under `"<partner>_tocs".sheets`:
```json
{
  "name": "Partner — Course Name TOC",
  "id": "BLANK_ID",
  "url": "https://docs.google.com/spreadsheets/d/BLANK_ID/edit",
  "permissions": "read-write",
  "created": "YYYY-MM-DD"
}
```

Append to `manifest.md`.

---

## Completed Example

**Partner:** Anaconda (2026-04-15)
**Course:** Debugging with GenAI
**Sheet ID:** `1ZQLxm9GdUyjFCjpPXebh-mUNKZ2HKoFqbtUNaETLvLg`
**Folder:** `1k6gZTxKToyhZmereGv70wj-MeFRYncTW` (Anaconda Courses)
**Scrape method:** WebFetch (public page)
**Blank used:** TOC Blank 001

---

## Adapting for Other Partners

| LMS Platform | DOM Pattern |
|---|---|
| Thinkific | `.accordion-item` > `button.accordion-button` + `.course-curriculum__title` |
| LearnWorlds | TBD |
| Teachable | TBD |
| Custom | Inspect DOM; look for chapter/lesson hierarchy |
