---
name: catalog-scraper
description: Scrape and analyze course catalogs from training providers (HubSpot Academy, Salesforce Trailhead, Anaconda Learning, DataCamp, etc.) to evaluate content for potential LinkedIn Learning licensing. Generates standardized JSON, XLSX (Excel), and markdown reports. Use when user requests to scrape, analyze, or generate course catalogs from any training platform, including requests like "scrape [provider] course catalog", "generate course list from [URL]", "analyze [provider]'s training offerings", or "create catalog for [provider]". Handles various architectures (single page, paginated, navigation-based) and obstacles (email gates, CloudFront protection, lazy loading).
---

# Course Catalog Scraper

## Input Parameters
- **Provider Name**: Name of the training platform (e.g., "HubSpot Academy")
- **URL**: Starting URL for the course catalog/listing page
- **Optional**: Credentials if provided (for email-gated content)

## Workflow

### Phase 1: Discovery & Reconnaissance (5-10 minutes)

**Objective**: Understand the site architecture before attempting extraction.

1. **Initial Page Analysis**
   - Fetch the URL and examine the HTML structure
   - Use WebFetch to understand page organization and content type
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
   - Include imports: requests, bs4, csv, json
   - Implement chosen strategy
   - Add error handling and rate limiting (sleep between requests)

2. **Extract Course Data**
   - Run scraper
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

**Generate THREE artifacts** (all required, saved locally):

#### 1. JSON: `{provider_slug}_catalog.json`
Raw course data in JSON format for programmatic access

#### 2. XLSX: `{provider_slug}_catalog.xlsx`
Excel spreadsheet for analysis and comparison (more reliable than CSV for arbitrary text with commas, line breaks, quotes, etc.)

#### 3. Report: `{provider_slug}_report.md`
Detailed markdown report with analysis and recommendations

**Required columns** (consistent across all providers):
- `provider` - Provider name (e.g., "HubSpot Academy")
- `title` - Course title
- `url` - Direct link to course page
- `description` - Course description/summary
- `duration` - Hours, modules, or time commitment
- `level` - Beginner/Intermediate/Advanced/All Levels
- `format` - On-Demand/Live/Blended/Self-Paced
- `price` - Free/Paid/$XX (as displayed)
- `category` - Topic/subject area
- `instructor` - If available
- `date_scraped` - ISO format date (YYYY-MM-DD)

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

1. **Show Summary with all three artifacts**
   ```
   ✓ Scraped {X} courses from {Provider}

   ARTIFACTS GENERATED:
   ✓ JSON:   {provider_slug}_catalog.json
   ✓ XLSX:   {provider_slug}_catalog.xlsx
   ✓ Report: {provider_slug}_report.md
   ```

2. **Preview Data** - Display first 3-5 courses with key fields

3. **Provide Analysis** - Quick insights:
   - Course count by level/category
   - Price distribution
   - Format breakdown
   - Content gaps or strengths
   - LinkedIn Learning licensing perspective

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

Ensure `pandas`, `requests`, `bs4`, `unidecode`, and `openpyxl` (for Excel export) are in the project dependencies (already available in pyproject.toml).

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

**All files saved in current working directory:**
- `{provider_slug}_catalog.json` - Raw JSON data
- `{provider_slug}_catalog.xlsx` - Excel spreadsheet (tabular data)
- `{provider_slug}_report.md` - Detailed scraping report
- `scrape_{provider_slug}.py` - Python script (for repeatability)

## Success Criteria

**Minimum viable output** (MUST HAVE):
- ✓ JSON with at least: provider, title, url
- ✓ XLSX with at least: provider, title, url
- ✓ Markdown report documenting approach and limitations
- ✓ Working script for future updates

**Ideal output**:
- ✓ Complete metadata for all fields
- ✓ 100% of courses captured
- ✓ High data quality (>90% complete fields, >90% unique descriptions, avg title length <100 chars)
- ✓ Reproducible process
- ✓ Clean, well-formatted markdown report




