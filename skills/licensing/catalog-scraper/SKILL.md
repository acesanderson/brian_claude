---
name: licensing:catalog-scraper
description: Scrape a single training provider's course catalog for LinkedIn Learning licensing evaluation. Part of the licensing toolkit — typically invoked as a subagent by the licensing skill. Use when asked to "scrape [provider]", "catalog [company]", "analyze [provider]'s training offerings", or when dispatched as a licensing:catalog-scraper-worker subagent. Accepts company name alone (discovers portal URLs first) or company name + URL (skips discovery). Handles single page, paginated, navigation-based catalogs and obstacles (email gates, CloudFront, lazy loading). Writes courses to DB via temp file + ingest pattern; produces report.md as the only file artifact.
---

# Course Catalog Scraper

## Prerequisites

- **uv** — the only required system dependency. Install: https://docs.astral.sh/uv/getting-started/installation/

Bundled scraper scripts (e.g. `scrape_ibm_training.py`) run via:
```bash
uv run --directory ~/.claude/skills/licensing/catalog-scraper python scrape_ibm_training.py
```

Generated scraper scripts (created in your working directory) must include uv inline script
metadata (see Phase 3) so they are self-contained and need no separate environment setup:
```bash
uv run scrape_{provider_slug}.py
```

## Input Parameters
- **Provider Name**: Name of the training platform (e.g., "HubSpot Academy")
- **URL**: Starting URL for the course catalog/listing page
- **Optional**: Credentials if provided (for email-gated content)

## Workflow

### Phase 0: Pre-Scrape Check (REQUIRED FIRST STEP)

**Objective**: Avoid duplicate work by checking if this provider is already in the DB.

1. **Check DB for existing provider**
   ```bash
   uv run --project ~/vibe/licensing-project/catalog catalog providers
   ```
   Look for the provider slug in the output. If the provider appears with `Scrape Status = complete`, confirm with the user before re-scraping.

2. **Determine the slug**
   The slug used for the temp file and the DB is computed by `slugify(provider_name)`:
   lowercase, replace non-alphanumeric runs with `-`, strip leading/trailing `-`.
   Example: `"Linux Foundation"` → `linux-foundation`.
   Use this slug consistently throughout the scrape.

### Phase 0.5: URL Discovery (run only when no URL is provided)

If the user gives a company name without a URL, discover the training portal(s) before scraping.

Use the brave-web-search skill CLI:
```bash
uv run --directory ~/.claude/skills/brave-web-search python conduit.py search "QUERY"
uv run --directory ~/.claude/skills/brave-web-search python conduit.py fetch "URL"
```

**Search queries to run** (for each company):
- `"{company}" academy courses`
- `"{company}" training certification`
- `"{company}" learning platform`

**Candidate URL patterns** (ranked by confidence):
- `high` — dedicated subdomain: `learn.company.com`, `academy.company.com`, `university.company.com`
- `medium` — main site section: `company.com/courses`, `company.com/training`, `company.com/learn`
- `medium` — third-party hosted (Skilljar, Thinkific, Teachable — note the platform)
- `low` — limited info or auth wall visible

**For each candidate**, fetch the URL to confirm it's a real course catalog (not a marketing page or login wall). Discard candidates with no visible course listings.

**Output**: a list of `(portal_label, url)` pairs. For example, Crowdstrike might yield:
- `("CrowdStrike University", "https://university.crowdstrike.com")`
- `("Falcon Training", "https://www.crowdstrike.com/falcon-training")`

If only one portal found → proceed linearly through Phases 1–6.
If multiple portals found → see **Multi-Portal Dispatch** below before starting Phase 1.

### Multi-Portal Dispatch

When Phase 0.5 finds **2+ distinct training portals** for a company, spawn one subagent per portal (per CLAUDE.md batch scraping rules). Do NOT process them sequentially in the main thread.

**Each subagent receives:**
- The company name and portal label
- The specific catalog URL
- Instructions to run Phases 1–3 (discovery, extraction, script) and return:
  - The extracted course list as a JSON array (printed to stdout)
  - A brief summary of: architecture type, obstacles, data quality, limitations

**Subagents do NOT write files.** All file I/O happens in the main session after consolidation.

**Main session after subagents complete:**
1. Merge all course arrays into one combined list (tag each course with its `portal` source if distinct)
2. Run Phase 4 (standardized output) on the combined data
3. Run Phase 5 (deliver results) and Phase 6 (Google Sheet) once, treating the combined data as the single provider artifact

### Phase 1: Discovery & Reconnaissance (5-10 minutes)

**Objective**: Understand the site architecture before attempting extraction.

1. **Initial Page Analysis**
   - Fetch the URL and examine the HTML structure
   - Use `uv run --directory ~/.claude/skills/brave-web-search python conduit.py fetch "url"` to understand page organization
   - Document findings: "This is a [single page / paginated / navigation-based] catalog"

2. **Data Source Detection** - Check for (in order of preference):
   - **JSON in hidden inputs** (like `<input id="archive-posts">`)
   - **JavaScript data variables** (search for `var courses =` or `window.__INITIAL_STATE__`)
   - **API endpoints** (inspect Network tab patterns, look for `/api/courses` or similar)
   - **Structured data** (Schema.org JSON-LD in `<script type="application/ld+json">`)
   - **Server-rendered HTML** (course cards, list items with consistent structure)

3. **Architecture Mapping**
   - **Single Page**: All courses on one page (simple extraction)
   - **Paginated**: Multiple pages with page numbers or "Next" buttons
   - **Infinite Scroll**: Lazy-loaded content (requires Selenium or API detection)
   - **Navigation-based**: Must visit topic/category pages first (like AMA)
   - **Search/Filter-based**: Courses behind search interface

4. **Obstacle Identification**
   - Email gates / signup walls
   - Authentication requirements
   - Rate limiting
   - CAPTCHA
   - JavaScript-heavy (content not in initial HTML)

5. **Field Mapping** - Identify available metadata:
   - Required: Title, URL
   - Preferred: Description (MUST be course-specific, NOT generic catalog text), Duration, Level, Price, Format
   - Optional: Instructor, Prerequisites, Learning Objectives, Reviews

   **CRITICAL - Field Separation**:
   - **Title**: Extract from the MOST SPECIFIC selector (e.g., `h2.course-title`, `.title`, `[data-title]`)
     - NEVER use parent element `.text` that includes child elements
     - Title should be SHORT (typically <100 chars, rarely >150)
     - Should NOT contain description text
   - **Description**: Extract from separate description element (e.g., `.description`, `p.summary`, `.excerpt`)
     - MUST be course-specific, NOT generic catalog text
     - Should be DIFFERENT from title

   **Common Mistake**: Using `.text` on a parent `<div>` or `<a>` that contains both title and description, causing them to concatenate. Always target the specific child element for each field.

### Phase 2: Extraction Strategy

Based on discovery, choose the appropriate approach:

#### Strategy A: JSON Extraction (Fastest)
If JSON data is embedded or API endpoint found:
```python
# Extract JSON from hidden input or API
# Parse and transform to standard format
# No need for complex scraping
```

#### Strategy B: Static HTML Scraping (Most Common)
If courses are server-rendered:
```python
# Use BeautifulSoup
# Find course card/list elements
# Extract metadata from consistent structure
# Handle pagination with requests loop
```

#### Strategy C: Browser Automation (Lazy Loading)
If content loads dynamically:
```python
# Use Selenium (note: requires setup)
# Scroll to trigger lazy loading
# Extract rendered content
# More resource-intensive
```

#### Strategy D: Navigation Crawl (Multi-level)
If courses organized by categories:
```python
# Get category/topic list first
# Visit each category page
# Extract courses from each
# Aggregate results
```

#### Strategy E: Manual Documentation (Blocked)
If email gate or auth required:
```python
# Document the obstacle
# Provide manual inspection findings
# Recommend obtaining credentials
# Note what's visible pre-auth
```

### Phase 3: Implementation

1. **Create Python Script** in working directory:
   - Name: `scrape_{provider_slug}.py`
   - **Start with uv inline script metadata** (see Required Dependencies section)
   - Include imports: requests, bs4, csv, json
   - Implement chosen strategy
   - Add error handling and rate limiting (sleep between requests)
   - Anchor file paths to `Path(__file__).parent`, not bare relative strings

2. **Extract Course Data**
   - Run scraper with: `uv run scrape_{provider_slug}.py`
   - Show progress (X of Y courses scraped)
   - Handle errors gracefully
   - Note any limitations encountered

3. **Validate Data Quality**
   - Check for missing critical fields
   - Verify URLs are valid
   - **Verify titles are concise** (flag any >150 characters - likely contains description text)
   - **Verify descriptions are course-specific** (not generic catalog text repeated for every course)
   - Count total courses found
   - Identify any data quality issues

   **Title Validation**:
   - Titles should be SHORT - typically 20-80 characters, rarely >150
   - If titles are very long (>150 chars), you're likely extracting parent element text that includes description
   - Review HTML structure and use more specific selectors (e.g., `h2.title` not `div.course-card`)

   **Description Validation**:
   - If you see the same description text appearing for multiple courses, this is WRONG
   - You must extract course-specific descriptions from:
     - Course card/tile text (separate from title)
     - Course detail page summaries
     - Meta descriptions
     - First paragraph of course content
     - Structured data (Schema.org)
   - If no course-specific description exists, leave the field empty rather than using generic text

### Phase 4: Standardized Output

After collecting all courses, write and ingest in this exact order:

**Step A — Write temp file** (use `slugify(provider_name)` for the slug):
```bash
# Temp file path — never write to partners/<slug>/catalog.json
/tmp/scrape_<slug>.json
```

Write the course list as a JSON array to this path.

**Step B — Ingest to DB**:
```bash
uv run --project ~/vibe/licensing-project/catalog \
  catalog ingest /tmp/scrape_<slug>.json --status complete
```
Use `--status partial` if the scrape was incomplete (hit a JS wall, auth gate, pagination limit, etc.).
Do NOT call `catalog ingest` if 0 courses were collected — skip to Step D instead.

**Step C — Delete temp file**:
```bash
rm -f /tmp/scrape_<slug>.json
```
If ingest failed (non-zero exit), leave the temp file for manual retry and note it in `report.md`.

**Step D — Write report.md**:
Write `partners/<slug>/report.md` with the following fields:
```
Provider:      <name>
Slug:          <slug>
Date scraped:  YYYY-MM-DD
Courses found: <N>
Scrape status: complete | partial | blocked | (failed — not ingested)
Portal URL:    <url>
Notes:         <any obstacles, partial scrape reasons, or empty>
```

**MUST NOT write:**
- `partners/<slug>/catalog.json` — no longer generated
- `partners/<slug>/catalog.xlsx` — eliminated; no replacement

### Format Normalization (REQUIRED)

The `format` field must use a canonical enum. Free-text format values break the
downstream classifier. Every scraper MUST call `normalize_format()` before writing
the format field. Never write a raw scraped string directly into `format`.

**Canonical enum values:**

| Value | Meaning |
|---|---|
| `self-paced` | Asynchronous on-demand video or text content |
| `instructor-led` | Synchronous live instruction (in-person or virtual) |
| `hands-on-lab` | Interactive lab requiring a platform environment (not ingestible) |
| `learning-path` | Ordered collection of courses — a container, not a course |
| `assessment` | Standalone exam, quiz, or proctored evaluation |
| `bundle` | Package of multiple courses sold or delivered together |
| `blended` | Mix of self-paced and live/in-person components |
| `unknown` | Format cannot be determined from available metadata |

**Copy this function into every generated scraper:**

```python
def normalize_format(raw: str) -> str:
    """Map raw scraped format strings to canonical enum values."""
    if not raw:
        return "unknown"
    v = raw.lower().strip()

    # Instructor-led / live / synchronous
    if any(x in v for x in [
        "instructor", "ilt", "vilt", "live", "webinar", "bootcamp",
        "cohort", "on-campus", "on campus", "in-person", "blended",
        "custom sow", "consulting",
    ]):
        # Blended is a distinct category
        if "blended" in v:
            return "blended"
        return "instructor-led"

    # Labs / interactive platform-dependent
    if any(x in v for x in ["lab", "sandbox", "interactive", "hands-on"]):
        return "hands-on-lab"

    # Containers (learning paths, bundles, certificate programs)
    if any(x in v for x in ["learning path", "bundle", "certificate program", "badge"]):
        return "learning-path" if "path" in v else "bundle"

    # Assessments / exams
    if any(x in v for x in [
        "assessment", "exam", "certification exam", "skillcred",
        "self-study + online exam", "self-paced exam",
    ]):
        return "assessment"

    # Self-paced / on-demand (most common — check last)
    if any(x in v for x in [
        "on-demand", "on demand", "self-paced", "self paced",
        "online", "tutorial", "e-learning", "elearning",
        "module", "crash course", "learning byte", "prep course",
        "recording", "video",
    ]):
        return "self-paced"

    return "unknown"
```

**Usage in scraper:**
```python
course = {
    "format": normalize_format(raw_format_string),
    # ... other fields
}
```

If the site provides no format signal, set `"format": "unknown"` — do not guess.

**Optional columns** (include if available):
- `prerequisites`
- `learning_objectives`
- `certification_offered`
- `rating`
- `enrollment_count`
- `language`
- `last_updated`

**Implementation Code Snippet:**
```python
import json
from datetime import datetime
import pandas as pd
from unidecode import unidecode

def clean_to_ascii(text: str | None) -> str:
    """Convert Unicode text to clean ASCII."""
    if not text:
        return ""
    # Use unidecode to convert Unicode to closest ASCII representation
    return unidecode(str(text))

def export_catalog_data(courses_data: list[dict], provider_slug: str) -> dict[str, str]:
    """Export to JSON and XLSX."""
    # Convert to DataFrame
    df = pd.DataFrame(courses_data)

    # Column order
    column_order = [
        "provider", "title", "url", "description", "duration",
        "level", "format", "price", "category", "learning_path",
        "date_scraped"
    ]
    existing_cols = [col for col in column_order if col in df.columns]
    df = df[existing_cols]

    # VALIDATE TITLE QUALITY
    if "title" in df.columns:
        df["title_length"] = df["title"].str.len()
        avg_title_length = df["title_length"].mean()
        long_titles = df[df["title_length"] > 150]

        print(f"\n⚠️  TITLE QUALITY CHECK:")
        print(f"  Average title length: {avg_title_length:.0f} characters")

        if len(long_titles) > 0:
            print(f"  ❌ WARNING: {len(long_titles)} titles are >150 characters")
            print(f"     Long titles suggest description text is bleeding into title field.")
            print(f"     Examples of long titles:")
            for idx, row in long_titles.head(3).iterrows():
                print(f"       - {row['title'][:100]}... ({row['title_length']} chars)")
            print(f"     Fix: Use more specific selector (e.g., 'h2.title' not 'div.card')\n")

        df = df.drop(columns=["title_length"])

    # VALIDATE DESCRIPTION QUALITY
    if "description" in df.columns:
        total_descs = len(df)
        unique_descs = df["description"].nunique()
        uniqueness_pct = (unique_descs / total_descs * 100) if total_descs > 0 else 0

        print(f"⚠️  DESCRIPTION QUALITY CHECK:")
        print(f"  Total courses: {total_descs}")
        print(f"  Unique descriptions: {unique_descs}")
        print(f"  Uniqueness: {uniqueness_pct:.1f}%")

        if uniqueness_pct < 90:
            print(f"  ❌ WARNING: Low description uniqueness ({uniqueness_pct:.1f}%)")
            print(f"     This suggests generic catalog text instead of course-specific descriptions.")
            print(f"     Review the scraping logic to extract individual course descriptions.\n")

    # 1. JSON (preserve Unicode)
    json_filename = f"{provider_slug}_catalog.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(courses_data, f, indent=2, ensure_ascii=False)

    # 2. XLSX (Excel format - handles all text reliably)
    xlsx_filename = f"{provider_slug}_catalog.xlsx"
    # Apply ASCII cleaning to all text columns for cleaner output
    text_columns = df.select_dtypes(include=['object']).columns
    for col in text_columns:
        df[col] = df[col].apply(clean_to_ascii)
    df.to_excel(xlsx_filename, index=False, engine='openpyxl')

    return {"json": json_filename, "xlsx": xlsx_filename}
```

**Generate Report: `{provider_slug}_report.md`**

Include:
```markdown
# {Provider Name} Catalog Scraping Report

**Date**: {date}
**URL**: {starting_url}
**Total Courses**: {count}

## Architecture
- Type: [Single Page / Paginated / Navigation-based / etc.]
- Data Source: [JSON / HTML / API / etc.]
- Obstacles: [None / Email gate / etc.]

## Extraction Method
[Description of strategy used]

## Data Quality
- Title: {X}% complete (avg length: {X} chars, {Y} titles >150 chars)
- Description: {X}% complete ({X}% unique - must be >90% for quality data)
- Duration: {X}% complete
- Level: {X}% complete
- Price: {X}% complete

**Title Quality Check**: If titles are >150 characters, description text is likely bleeding into title field. Review HTML selectors to extract title element specifically.

**Description Quality Check**: If description uniqueness is <90%, this indicates generic catalog text is being used instead of course-specific descriptions. This must be fixed.

## Limitations
[Any access restrictions, missing data, or issues encountered]

## Recommendations
[Suggestions for improving data collection, e.g., "Obtain credentials for full access"]

## Sample Courses
[List 3-5 example courses with full metadata]
```

### Phase 5: Deliver Results

1. **Ensure partner directory exists**
   ```python
   from pathlib import Path
   provider_dir = Path.home() / "licensing" / "partners" / provider_slug
   provider_dir.mkdir(parents=True, exist_ok=True)
   ```

2. **Show Summary**
   ```
   Scraped {X} courses from {Provider}

   ARTIFACTS:
   report.md:  ~/licensing/partners/{provider_slug}/report.md
   DB:         catalog database on Caruana ({N} courses ingested)
   ```

3. **Preview Data** — Display first 3-5 courses with key fields

4. **Provide Analysis** — Quick insights:
   - Course count by level/category
   - Format breakdown
   - Content gaps or strengths
   - LinkedIn Learning licensing perspective

### Phase 6: Publish Google Spreadsheet

**Always run this phase after Phase 5.** Every scrape produces a Google Sheet.

#### Sheet structure (single tab)

The sheet has two sections separated by a blank row:

**Section 1 — Text Summary** (licensing opportunity analysis):
Write as two-column rows: `[Label, Value]`. Include:
- Header block: Provider, Date, Academy URL, Total Courses, Coverage status
- Blank row
- "CATALOG BREAKDOWN" header row, then sub-sections:
  - By Level (row per level with count)
  - By Format (row per format with count)
  - By Category (row per category with count)
- Pricing summary (one row per pricing tier/note)
- Key Observations (one row per observation)
- Limitations (one row per limitation)
- Recommendations (one row per recommendation)

**Omit any file path references** (no mention of catalog.json, catalog.xlsx, report.md, etc.).

**Section 2 — Course Data Table**:
- One blank row separator after the summary
- Header row: all catalog columns (provider, title, url, description, duration, level, format, price, category, instructor, date_scraped, plus any optional columns that have data)
- One row per course

#### How to write the sheet

Use the `mcp__captain__create_google_sheets_spreadsheet` MCP tool to create the sheet:
- Title: `{Provider Name} — Course Catalog ({Month} {Year})`

Then use `mcp__captain__write_google_sheets_by_id` to write all rows in a single call starting at `A1`. Pass the full 2D array (summary rows + blank row + header row + data rows).

#### Register in google_docs.json

After publishing, add an entry to `~/licensing/context/google_docs.json` under `read_write_docs`:
```json
{
  "name": "{Provider Name} — Course Catalog ({Month} {Year})",
  "id": "{sheet_id}",
  "url": "{sheet_url}",
  "description": "{Provider} catalog: summary analysis + {N}-course structured data table. Generated {YYYY-MM-DD}.",
  "permissions": "read-write",
  "type": "spreadsheet"
}
```

### Phase 6.5: Update Catalog Index

**Always run this phase after Phase 6.** Every scrape adds one row to the master Catalog Index.

The Catalog Index is a single Google Sheet that tracks all scraped partners in one place.
It is registered in `~/licensing/context/google_docs.json` under `"catalog_index"` with
spreadsheet ID `12FAeMyt--aaakxOWp21f5_xpcQIN1cpBlE_CHlaIzGw`.

#### Step 1 — Read the partner's pipeline context

Before writing the row, check `~/licensing/partners/{slug}/notes.md` for:
- Current BD stage and POC
- One-sentence description of what the company does / why it's interesting

If no notes file exists, use what you know from the scrape.

#### Step 2 — Build the row

| Column | What to write |
|---|---|
| Partner | Display name (e.g. "CrowdStrike") |
| Catalog Sheet URL | The Google Sheet URL created in Phase 6 |
| Context | BD stage + POC + one-sentence company/content description |
| Courses | Total course count; add viability note if applicable (e.g. "82 (70 viable)") |
| Status | `complete`, `partial`, or `pending` — matches registry status |
| Date Scraped | ISO date (YYYY-MM-DD) |
| Notes | Key licensing observations: format, access limitations, standout content, risks |

**Context field format**: `{Stage} — {POC} BD. {One-sentence description of company/content.}`
Example: `Outreach — Brian BD; email to Amy Hughey 2026-03-09. CrowdStrike University; Falcon endpoint security platform.`

#### Step 3 — Append the row

```python
# Read Catalog Index sheet ID from google_docs.json
catalog_index_id = "12FAeMyt--aaakxOWp21f5_xpcQIN1cpBlE_CHlaIzGw"

# Use mcp__captain__write_google_sheets_by_id with mode="append"
# values: one row — [Partner, Catalog Sheet URL, Context, Courses, Status, Date Scraped, Notes]
```

Use `mcp__captain__write_google_sheets_by_id` with `mode="append"`.

#### Step 4 — Log to manifest.md

```
- YYYY-MM-DD | updated | Content Licensing — Catalog Index | Added {Partner} row ({N} courses, {status}, {date})
```

#### Check for existing row first

Before appending, check whether the partner already has a row in the index
(use `mcp__captain__read_google_sheets_by_id` and scan the Partner column).
If a row exists, note it in the summary — do not create a duplicate.

## Required Dependencies

All scrapers must include these imports:
```python
from __future__ import annotations

import json
import re
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode
```

Every generated scraper script **must** begin with uv inline script metadata so it is
self-contained and runnable on any machine with only `uv` installed:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "beautifulsoup4",
#   "openpyxl",
#   "pandas",
#   "requests",
#   "unidecode",
# ]
# ///
```

Run with: `uv run scrape_{provider_slug}.py`

Bundled scripts in `~/.claude/skills/licensing/catalog-scraper/` use the skill's own `pyproject.toml`
and run with: `uv run --directory ~/.claude/skills/licensing/catalog-scraper python scrape_{provider_slug}.py`

## Best Practices

1. **Be Respectful**
   - Add delays between requests (1-2 seconds)
   - Respect robots.txt
   - Don't overwhelm servers
   - Use appropriate User-Agent

2. **Handle Failures Gracefully**
   - Log errors but continue scraping
   - Partial data is better than no data
   - Document what couldn't be accessed

3. **Validate URLs**
   - Test a sample course URL before full scrape
   - Ensure URL construction is correct
   - Handle edge cases (trailing slashes, query params)

4. **Be Transparent**
   - Document limitations clearly
   - Note what requires manual review
   - Explain data quality issues

5. **Extract Fields Separately and Precisely**
   - **NEVER use parent element `.text`** - it concatenates all child text
   - **Target specific child elements** for each field:
     ```python
     # WRONG - concatenates title + description
     title = card.text

     # RIGHT - extract each field separately
     title = card.find("h2", class_="title").text.strip()
     description = card.find("p", class_="description").text.strip()
     ```
   - **Validate title length**: Should be <150 chars; if longer, you're extracting too much
   - **Ensure field uniqueness**: Each course should have distinct title AND description

6. **Extract Course-Specific Descriptions**
   - NEVER use generic catalog/provider descriptions that apply to all courses
   - Always look for course-specific text (what THIS course teaches/covers)
   - Check course cards, detail pages, meta tags, and structured data
   - If multiple courses share identical descriptions, you're extracting the wrong element
   - Empty description is better than wrong/generic description

## Common Patterns by Provider Type

### Corporate Training Platforms (HubSpot, Salesforce)
- Often have clean, structured course pages
- Usually server-rendered HTML
- May have free/gated content distinction
- Often well-organized by topic

### Tech/Developer Platforms (Anaconda, Pluralsight)
- May use JavaScript frameworks (React, etc.)
- Often have JSON data available
- Detailed technical metadata
- Strong categorization

### Professional Development (AMA, PMI)
- Mixed content types (courses, events, certifications)
- Often behind paywalls
- May require membership to view full catalog
- Less consistent structure

## Error Recovery

If scraping fails:
1. Document what was attempted
2. Provide what data IS available (even if incomplete)
3. Suggest alternative approaches
4. Offer to retry with modified strategy

## Output Location

**Primary output directory: `$HOME/licensing/`**

Files are placed at:
- `partners/<slug>/report.md` — the only persistent file artifact
- `/tmp/scrape_<slug>.json` — temp file, deleted after successful ingest
- `scrape_{provider_slug}.py` — always written to **cwd**, deleted after scrape

The `partners/<slug>/catalog.json` and `partners/<slug>/catalog.xlsx` files are NOT
written by new scrapes. Existing files in those locations are legacy artifacts frozen
for the classifier — do not delete or overwrite them.

## Success Criteria

**Minimum viable output** (MUST HAVE):
- report.md written with all required fields (Provider, Slug, Date scraped, Courses found, Scrape status, Portal URL, Notes)
- Courses ingested to DB (`catalog ingest --status complete|partial` exit 0)
- No `/tmp/scrape_<slug>.json` remaining after successful ingest

**Ideal output**:
- Complete metadata for all courses (title, url, description, format, level, duration, category)
- 100% of courses captured
- High data quality (>90% unique descriptions, avg title length <100 chars)
- Reproducible scraper script (`scrape_{slug}.py`)




