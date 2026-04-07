# Generate TOCs — Subskill

Produces completed PTOC Cosmo Template Google Sheets for a licensed partner's submitted courses.
One sheet per course, placed in a partner-specific Drive folder, with chapter and video names pre-populated in cols C and G.

---

## Prerequisites

- `uv` for running Python scraper scripts
- Chrome running with remote debugging (see Tooling section of SKILL.md): `chrome-debug` alias
- Service account credentials: `/Users/bianders/.config/gcp/automated-lodge-491821-a1-0febab0041c3.json`
  - Email: `protean-topic@automated-lodge-491821-a1.iam.gserviceaccount.com`
  - Can READ/WRITE sheets that are shared with it; cannot CREATE files (no Drive quota)
- Captain MCP: handles file moves and sheet writes as bianderson@linkedin.com
- TOC template: `15CcsVriFcHXfeDiylYfaNOSvER9Ouf0Kbx3riq8lZOY` (gid `1342669638` = TOC tab)

---

## Golden Path

### Phase 1 — Scrape course structure

Connect to the partner's LMS via Playwright + CDP:

```python
# /// script
# dependencies = ["playwright"]
# ///
import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]
        await page.goto(COURSE_URL, wait_until="networkidle")
        structure = await page.evaluate("""() => {
            const chapters = [];
            for (const item of document.querySelectorAll('.accordion-item')) {
                const btn = item.querySelector('button.accordion-button');
                if (!btn) continue;
                const btnClone = btn.cloneNode(true);
                btnClone.querySelector('.snap-chapter-duration')?.remove();
                const chapterTitle = btnClone.innerText.trim();
                const lessons = [];
                for (const lEl of item.querySelectorAll('.course-curriculum__title')) {
                    const lClone = lEl.cloneNode(true);
                    lClone.querySelector('i')?.remove();
                    const name = lClone.innerText.trim();
                    if (name) lessons.push(name);
                }
                chapters.push({ chapter: chapterTitle, lessons });
            }
            return chapters;
        }""")
        return structure
```

This targets Thinkific-based LMS platforms (Anaconda uses this). For other LMS platforms, inspect the DOM and adapt selectors. Output: `/tmp/<partner>_toc_final.json`.

**Note:** The Chrome debug session must be running with the user's logged-in profile for any gated content. For public course pages (like Anaconda), the debug profile without auth is fine.

---

### Phase 2 — Compute row data

Transform scraped JSON into PTOC Cosmo Template row format. Output: `/tmp/<partner>_toc_rows.json`.

Row structure:
- **Rows 1–5** (header block): Title/By/With/ID/Loc with metadata in cols A, C, G
- **Row 6**: Template version label
- **Row 7**: Column headers (Ch #, Chapter Id, Chapter, …, Vid #, Video Id, Video Name, …)
- **Chapter rows**: col A = chapter number, col C = chapter title, cols B/D/E/F/G… empty
- **Video rows**: col A = empty, col E = video number within chapter, col G = video title

Kim's guidance: **col C (chapter names) and col G (video names) are the BD responsibility.** Cols A and E (sequential numbering) must be correct. All other columns are filled by production.

Reference the Anaconda compute script logic at `/tmp/scrape_anaconda_toc3.py` and the pre-computed rows at `/tmp/anaconda_toc_rows.json` as a working example.

---

### Phase 3 — Create template copies (user action required)

The service account cannot own new Drive files (no storage quota). Template copies must be created by the user via Apps Script.

Generate the script, then instruct the user:

```javascript
function copyTOCTemplates() {
  var TEMPLATE_ID = "15CcsVriFcHXfeDiylYfaNOSvER9Ouf0Kbx3riq8lZOY";
  var FOLDER_ID   = "<partner Drive folder ID>";
  var COURSES = [ "Partner — Course Name 1 TOC", /* ... */ ];

  var template = DriveApp.getFileById(TEMPLATE_ID);
  var folder   = DriveApp.getFolderById(FOLDER_ID);
  COURSES.forEach(function(name) {
    var copy = template.makeCopy(name, folder);
    Logger.log(name + " -> " + copy.getId());
  });
  Logger.log("Done. Paste the IDs above back to Claude.");
}
```

User steps:
1. `https://script.google.com/create` → paste script → Run → authorize
2. View → Execution log → paste the 7 `name -> id` lines back

This preserves template formatting and all non-TOC tabs used by other teams.

---

### Phase 4 — Write TOC data (Captain MCP)

Use `write_google_sheets_by_id` with `gid=1342669638`.

**Critical**: use `mode=overwrite` with explicit `range_a1` for all batches — **never use `mode=append`**. The template has pre-existing content in rows below the data area, so append lands at row 120+ instead of immediately after the last data row.

```
Batch 1: overwrite, no range_a1 (starts at A1) — rows 1–40
Batch 2 (if >40 rows): overwrite, range_a1="TOC!A41" — remaining rows
```

Row count thresholds by course size:
- ≤40 rows: single write
- 41–80 rows: two writes (A1, A41)
- 81+ rows: three writes (A1, A41, A81)

---

### Phase 5 — Move and register

```python
# Captain MCP: move_google_drive_file for each sheet ID → partner folder ID
# Then add to context/google_docs.json under "<partner>_tocs"
```

Register each sheet in `context/google_docs.json` under a `"<partner>_tocs"` key with `"permissions": "read-write"`.

---

## Completed Example

**Partner:** Anaconda (2026-04-07)
**Courses:** 7 (Build Your Data Science Portfolio, Data Analysis with GenAI, Data Cleaning with pandas, Data Ethics Fundamentals, Data Storytelling, Data Visualization with GenAI, Exploratory Data Analysis with Python)
**Folder:** `1k6gZTxKToyhZmereGv70wj-MeFRYncTW` (Anaconda Courses)
**Sheet IDs:** see `context/google_docs.json` → `anaconda_tocs.sheets`
**Scraper:** `/tmp/scrape_anaconda_toc3.py` (Thinkific, `.accordion-item` selectors)
**Row data:** `/tmp/anaconda_toc_rows.json`

---

## Adapting for Other Partners

| LMS Platform | DOM Pattern |
|---|---|
| Thinkific | `.accordion-item` > `button.accordion-button` + `.course-curriculum__title` |
| LearnWorlds | TBD |
| Teachable | TBD |
| Custom | Inspect DOM on course page; look for chapter/lesson hierarchy |

If the partner's LMS requires auth to view curriculum: use the Chrome debug session with the user's logged-in profile (not the `/tmp/chrome-debug-session` profile which has no Google/LMS auth).
