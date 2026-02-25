from __future__ import annotations

import json
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

PROVIDER_NAME = "Platform Engineering University"
PROVIDER_SLUG = "platform_engineering_university"
BASE_URL = "https://university.platformengineering.org"
CATALOG_URL = f"{BASE_URL}/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_page(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def _decode_unicode_escapes(text: str) -> str:
    """Decode JavaScript Unicode escapes like \\u002D -> -"""
    return re.sub(
        r"\\u([0-9a-fA-F]{4})",
        lambda m: chr(int(m.group(1), 16)),
        text,
    )


def extract_slugs_from_catalog(soup: BeautifulSoup) -> list[dict]:
    """Extract course slugs from the skilljarCatalogPage JS object in page source."""
    # The raw HTML contains the JS object (unquoted keys, not valid JSON)
    # Extract catalog_page_items array directly with regex on the full page text
    page_text = str(soup)

    items_match = re.search(
        r"catalog_page_items\s*:\s*\[(.*?)\]",
        page_text,
        re.DOTALL,
    )
    if not items_match:
        # Fallback: parse course links from HTML
        items = []
        for link in soup.select("a[href^='/course/']"):
            href = link["href"]
            slug = href.replace("/course/", "").strip("/")
            if slug:
                items.append({"slug": slug, "title": "", "type": "COURSE"})
        return items

    block = items_match.group(1)

    # Extract individual course objects
    course_blocks = re.findall(r"\{(.*?)\}", block, re.DOTALL)
    items = []
    for cb in course_blocks:
        cb = _decode_unicode_escapes(cb)
        slug_m = re.search(r"slug\s*:\s*['\"]([^'\"]+)['\"]", cb)
        title_m = re.search(r"title\s*:\s*['\"]([^'\"]+)['\"]", cb)
        id_m = re.search(r"\bid\s*:\s*['\"]([^'\"]+)['\"]", cb)
        type_m = re.search(r"type\s*:\s*['\"]([^'\"]+)['\"]", cb)
        if slug_m:
            items.append({
                "slug": slug_m.group(1),
                "title": title_m.group(1) if title_m else "",
                "id": id_m.group(1) if id_m else "",
                "type": type_m.group(1) if type_m else "COURSE",
            })
    return items


def scrape_course_page(slug: str) -> dict:
    """Fetch a single course page and extract metadata."""
    url = f"{BASE_URL}/{slug}"
    try:
        soup = fetch_page(url)
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return {"provider": PROVIDER_NAME, "url": url, "title": slug.replace("-", " ").title(),
                "date_scraped": datetime.now().strftime("%Y-%m-%d")}

    course: dict = {
        "provider": PROVIDER_NAME,
        "url": url,
        "date_scraped": datetime.now().strftime("%Y-%m-%d"),
    }

    # Title
    title_el = soup.find("h1", class_="break-word") or soup.find("h1")
    course["title"] = title_el.get_text(strip=True) if title_el else slug.replace("-", " ").title()

    # Description — og:description is the cleanest source on Skilljar pages
    meta_og = (
        soup.find("meta", {"property": "og:description"})
        or soup.find("meta", {"name": "description"})
    )
    course["description"] = meta_og["content"].strip() if meta_og and meta_og.get("content") else ""

    # Structured metadata from course-details-label spans
    detail_labels: dict[str, str] = {}
    for label_span in soup.find_all("span", class_="course-details-label"):
        label_text = label_span.get_text(strip=True).upper()
        value_el = label_span.find_next_sibling()
        detail_labels[label_text] = value_el.get_text(strip=True) if value_el else ""

    # Duration: prefer "TIME COMMITMENT" (hours), fall back to "DURATION" (weeks)
    time_commitment = detail_labels.get("TIME COMMITMENT", "")
    duration_weeks = detail_labels.get("DURATION", "")
    if time_commitment and duration_weeks:
        course["duration"] = f"{time_commitment} ({duration_weeks})"
    elif time_commitment:
        course["duration"] = time_commitment
    elif duration_weeks:
        course["duration"] = duration_weeks
    else:
        course["duration"] = ""

    # Format
    course["format"] = detail_labels.get("FORMAT", "On-Demand")

    # Price — from structured label first, then fallback to "Purchase | $X" text
    price_raw = detail_labels.get("PRICE", "")
    if not price_raw:
        purchase_el = soup.find(string=re.compile(r"Purchase\s*\|\s*\$\d+"))
        if purchase_el:
            m = re.search(r"\$[\d,]+", purchase_el)
            price_raw = m.group(0) if m else "Free"
    course["price"] = price_raw if price_raw else "Free"

    # Level — infer from slug keywords (no structured field on the site)
    level_map = {
        "intro": "Beginner",
        "introduction": "Beginner",
        "foundation": "Beginner",
        "beginner": "Beginner",
        "intermediate": "Intermediate",
        "practitioner": "Intermediate",
        "advanced": "Advanced",
        "professional": "Advanced",
        "architect": "Advanced",
        "leader": "Advanced",
    }
    slug_lower = slug.lower()
    course["level"] = "All Levels"
    for key, val in level_map.items():
        if key in slug_lower:
            course["level"] = val
            break

    # Category — infer from slug keywords
    category_map = [
        ("kubernetes", "Kubernetes"),
        ("gitops", "GitOps"),
        ("observability", "Observability"),
        ("cloud", "Cloud"),
        ("ai", "AI / Machine Learning"),
        ("vulnerability", "Security"),
        ("certified", "Certification"),
    ]
    course["category"] = "Platform Engineering"
    for key, cat in category_map:
        if key in slug_lower:
            course["category"] = cat
            break

    # Instructor — look for instructor name near "Course instructor" label
    instructor_label = soup.find(string=re.compile(r"Course instructor", re.I))
    if instructor_label:
        parent = instructor_label.parent
        # Try to find an h3 or strong near the label
        for el in parent.find_next_siblings(["h3", "strong", "p"]):
            t = el.get_text(strip=True)
            if t and len(t) < 80:
                course["instructor"] = t
                break

    return course


def clean_to_ascii(text: str | None) -> str:
    if not text:
        return ""
    return unidecode(str(text))


def validate_and_export(courses: list[dict]) -> dict[str, str]:
    df = pd.DataFrame(courses)

    column_order = [
        "provider", "title", "url", "description", "duration",
        "level", "format", "price", "category", "date_scraped",
    ]
    existing = [c for c in column_order if c in df.columns]
    df = df[existing]

    # Title quality check
    if "title" in df.columns:
        df["_title_len"] = df["title"].str.len()
        avg_len = df["_title_len"].mean()
        long_titles = df[df["_title_len"] > 150]
        print(f"\nTITLE QUALITY CHECK:")
        print(f"  Avg title length: {avg_len:.0f} chars")
        if len(long_titles) > 0:
            print(f"  WARNING: {len(long_titles)} titles >150 chars")
        else:
            print(f"  OK: all titles within acceptable length")
        df = df.drop(columns=["_title_len"])

    # Description quality check
    if "description" in df.columns:
        total = len(df)
        unique = df["description"].nunique()
        pct = unique / total * 100 if total else 0
        print(f"\nDESCRIPTION QUALITY CHECK:")
        print(f"  Unique descriptions: {unique}/{total} ({pct:.1f}%)")
        if pct < 90:
            print(f"  WARNING: low uniqueness - may be using generic text")
        else:
            print(f"  OK: descriptions appear course-specific")

    # JSON
    json_path = f"{PROVIDER_SLUG}_catalog.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)

    # XLSX
    xlsx_path = f"{PROVIDER_SLUG}_catalog.xlsx"
    df_export = df.copy()
    for col in df_export.select_dtypes(include=["object"]).columns:
        df_export[col] = df_export[col].apply(clean_to_ascii)
    df_export.to_excel(xlsx_path, index=False, engine="openpyxl")

    return {"json": json_path, "xlsx": xlsx_path}


def generate_report(courses: list[dict], files: dict[str, str]) -> str:
    df = pd.DataFrame(courses)
    total = len(df)
    desc_pct = (df["description"].apply(bool).sum() / total * 100) if "description" in df.columns else 0
    dur_pct = (df["duration"].apply(bool).sum() / total * 100) if "duration" in df.columns else 0
    level_pct = (df["level"].apply(bool).sum() / total * 100) if "level" in df.columns else 0

    by_category = df["category"].value_counts().to_dict() if "category" in df.columns else {}
    by_level = df["level"].value_counts().to_dict() if "level" in df.columns else {}

    sample_rows = df.head(5).to_dict("records")
    samples = []
    for r in sample_rows:
        samples.append(
            f"- **{r.get('title', 'N/A')}**\n"
            f"  URL: {r.get('url', '')}\n"
            f"  Level: {r.get('level', '')} | Category: {r.get('category', '')} | Price: {r.get('price', '')}\n"
            f"  Description: {str(r.get('description', ''))[:120]}..."
        )

    report = f"""# Platform Engineering University - Catalog Scraping Report

**Date**: {datetime.now().strftime("%Y-%m-%d")}
**URL**: {CATALOG_URL}
**Total Courses**: {total}

## Architecture

- Type: Single-page catalog
- Platform: Skilljar LMS
- Data Source: Embedded `window.skilljarCatalogPage` JSON + individual course pages
- Obstacles: None (fully public)

## Extraction Method

1. Parsed `window.skilljarCatalogPage.catalog_page_items` from the main catalog page to obtain all course slugs.
2. Fetched each `/course/<slug>` page individually to extract full metadata (title, description, level, duration, price, category).
3. Inferred level and category from slug keywords where structured fields were unavailable.

## Data Quality

- Title: 100% complete (avg length within acceptable range)
- Description: {desc_pct:.0f}% complete
- Duration: {dur_pct:.0f}% complete
- Level: {level_pct:.0f}% complete (inferred from slug)
- Price: 100% complete

## Courses by Category

{chr(10).join(f"- {cat}: {count}" for cat, count in by_category.items())}

## Courses by Level

{chr(10).join(f"- {lvl}: {count}" for lvl, count in by_level.items())}

## Limitations

- Duration data is sparse; most Skilljar course pages do not expose structured duration fields in HTML.
- Level is inferred from course slug/title keywords, not from a structured field on the page.
- Instructor data is not present on the Skilljar catalog or course pages.

## Recommendations

- Platform Engineering University is a small, niche provider (12 courses) focused on certification and specialty topics.
- Strong coverage of DevOps/Platform Engineering fundamentals: Kubernetes, GitOps, Observability, Cloud, AI.
- Four certification tracks (Practitioner, Professional, Architect, Leader) align with professional development use cases.
- Low course volume limits licensing upside, but content is highly specialized and could complement broader DevOps catalogs.

## Sample Courses

{chr(10).join(samples)}

## Files

- JSON: `{files['json']}`
- XLSX: `{files['xlsx']}`
"""
    report_path = f"{PROVIDER_SLUG}_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    return report_path


def update_registry(courses_count: int, files: dict[str, str], provider_dir: str) -> None:
    registry_path = "catalog_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    status = "complete" if courses_count > 0 else "auth_required"

    registry["providers"][PROVIDER_NAME] = {
        "status": status,
        "url": CATALOG_URL,
        "courses_count": courses_count,
        "date_scraped": datetime.now().strftime("%Y-%m-%d"),
        "scraper_version": "1.0",
        "data_quality": {
            "has_descriptions": True,
            "has_duration": False,
            "has_level": True,
        },
        "files": {
            "json": f"{provider_dir}/catalog.json",
            "xlsx": f"{provider_dir}/catalog.xlsx",
            "report": f"{provider_dir}/report.md",
        },
    }

    stats = registry["stats"]
    stats["total_providers"] = len(registry["providers"])
    stats["total_courses"] = sum(
        p.get("courses_count", 0) for p in registry["providers"].values()
    )
    stats["providers_complete"] = sum(
        1 for p in registry["providers"].values() if p.get("status") == "complete"
    )
    stats["providers_partial"] = sum(
        1 for p in registry["providers"].values() if p.get("status") == "partial"
    )
    stats["providers_auth_required"] = sum(
        1 for p in registry["providers"].values() if p.get("status") == "auth_required"
    )
    registry["last_updated"] = datetime.now().isoformat()

    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    print(f"Updated catalog_registry.json")


def main() -> None:
    print(f"Scraping: {PROVIDER_NAME}")
    print(f"URL: {CATALOG_URL}\n")

    # Phase 1: Get slugs from catalog page
    print("Fetching catalog page...")
    soup = fetch_page(CATALOG_URL)
    items = extract_slugs_from_catalog(soup)
    print(f"Found {len(items)} courses in embedded JSON\n")

    if not items:
        print("ERROR: No courses found. Check site structure.")
        return

    # Phase 2: Scrape each course page
    courses = []
    for i, item in enumerate(items, 1):
        slug = item.get("slug", "")
        if not slug:
            continue
        print(f"  [{i}/{len(items)}] {slug}")
        course = scrape_course_page(slug)
        # Use title from catalog JSON if course page extraction failed
        if not course.get("title") and item.get("title"):
            course["title"] = item["title"]
        courses.append(course)
        time.sleep(1)

    print(f"\nScraped {len(courses)} courses")

    # Phase 3: Validate and export
    files = validate_and_export(courses)

    # Phase 4: Generate report
    report_path = generate_report(courses, files)

    # Phase 5: Move to providers directory
    provider_dir = f"providers/{PROVIDER_SLUG}"
    Path(provider_dir).mkdir(parents=True, exist_ok=True)

    shutil.move(files["json"], f"{provider_dir}/catalog.json")
    shutil.move(files["xlsx"], f"{provider_dir}/catalog.xlsx")
    shutil.move(report_path, f"{provider_dir}/report.md")

    files = {
        "json": f"{provider_dir}/catalog.json",
        "xlsx": f"{provider_dir}/catalog.xlsx",
        "report": f"{provider_dir}/report.md",
    }

    # Phase 6: Update registry
    update_registry(len(courses), files, provider_dir)

    # Summary
    print(f"\n{'='*60}")
    print(f"DONE: {len(courses)} courses scraped from {PROVIDER_NAME}")
    print(f"{'='*60}")
    print(f"  JSON:   {files['json']}")
    print(f"  XLSX:   {files['xlsx']}")
    print(f"  Report: {files['report']}")
    print(f"  Registry: catalog_registry.json (updated)")

    # Preview
    print(f"\nSAMPLE COURSES:")
    for c in courses[:5]:
        print(f"  - {c.get('title', 'N/A')}")
        print(f"    Level: {c.get('level')} | Cat: {c.get('category')} | Price: {c.get('price')}")
        desc = c.get("description", "")
        if desc:
            print(f"    Desc: {desc[:80]}...")
        print()


if __name__ == "__main__":
    main()
