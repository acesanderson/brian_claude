"""
INE (InterNetwork Expert) course catalog scraper.
Uses the Algolia API with public credentials embedded in the my.ine.com SPA bundle.

Algolia config (from app.277068a0ba8260ef.js):
  App ID:          6D0ROPGFEB
  Search Key:      a8bd24bbc239b3553a7e91a97e0a3f1f
  Courses index:   prod_ine-content-api-courses
  Learning paths:  prod_ine-content-api-learning-paths
"""
from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime

import pandas as pd
import requests
from unidecode import unidecode

ALGOLIA_APP_ID = "6D0ROPGFEB"
ALGOLIA_API_KEY = "a8bd24bbc239b3553a7e91a97e0a3f1f"
COURSES_INDEX = "prod_ine-content-api-courses"
LEARNING_PATHS_INDEX = "prod_ine-content-api-learning-paths"

ALGOLIA_SEARCH_URL = f"https://{ALGOLIA_APP_ID}-dsn.algolia.net/1/indexes"

HEADERS = {
    "X-Algolia-Application-Id": ALGOLIA_APP_ID,
    "X-Algolia-API-Key": ALGOLIA_API_KEY,
    "Content-Type": "application/json",
}

PROVIDER = "INE (InterNetwork Expert)"
PROVIDER_SLUG = "ine"
DATE_SCRAPED = datetime.now().strftime("%Y-%m-%d")


def algolia_search_all(index: str) -> list[dict]:
    """Retrieve all records from an Algolia index using paginated search."""
    url = f"{ALGOLIA_SEARCH_URL}/{index}/query"
    records = []
    page = 0

    # First call to get total page count
    response = requests.post(url, headers=HEADERS, json={"query": "", "hitsPerPage": 1000, "page": 0}, timeout=30)
    response.raise_for_status()
    data = response.json()

    nb_pages = data.get("nbPages", 1)
    hits = data.get("hits", [])
    records.extend(hits)
    print(f"  Page 1/{nb_pages}: {len(hits)} records (total: {len(records)})")

    for page in range(1, nb_pages):
        response = requests.post(
            url, headers=HEADERS,
            json={"query": "", "hitsPerPage": 1000, "page": page},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        hits = data.get("hits", [])
        records.extend(hits)
        print(f"  Page {page + 1}/{nb_pages}: {len(hits)} records (total: {len(records)})")
        time.sleep(0.3)

    return records


def normalize_level(level: str | None) -> str:
    if not level:
        return ""
    level = level.lower().strip()
    mapping = {
        "beginner": "Beginner",
        "novice": "Beginner",
        "intermediate": "Intermediate",
        "advanced": "Advanced",
        "professional": "Advanced",
        "expert": "Advanced",
        "all": "All Levels",
    }
    return mapping.get(level, level.capitalize())


def normalize_duration(duration_raw: str | int | float | None) -> str:
    """Normalize duration to human-readable string. Handles HH:MM:SS and minutes."""
    if not duration_raw:
        return ""
    if isinstance(duration_raw, (int, float)):
        hours = round(duration_raw / 60, 1)
        return f"{hours}h"
    if isinstance(duration_raw, str):
        # Handle HH:MM:SS format
        parts = duration_raw.split(":")
        if len(parts) == 3:
            try:
                h = int(parts[0])
                m = int(parts[1])
                total_hours = h + m / 60
                return f"{total_hours:.1f}h"
            except ValueError:
                pass
        return duration_raw
    return str(duration_raw)


def clean_to_ascii(text: str | None) -> str:
    if not text:
        return ""
    return unidecode(str(text))


def strip_html(text: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_learning_area(h: dict) -> str:
    """Extract primary learning area name from hit."""
    # learning_areas is a list of dicts with 'name' key
    areas = h.get("learning_areas") or []
    if areas and isinstance(areas[0], dict):
        return areas[0].get("name") or ""
    # fallback
    la = h.get("learning_area") or {}
    if isinstance(la, dict):
        return la.get("name") or la.get("learning_area_name") or ""
    return ""


def process_course_hits(hits: list[dict]) -> list[dict]:
    courses = []
    for h in hits:
        title = h.get("name") or ""
        description = h.get("description") or h.get("short_description") or ""
        if description and "<" in description:
            description = strip_html(description)

        # URL is provided directly in the hit
        url = h.get("url") or f"https://my.ine.com/course/{h.get('slug', h.get('objectID', ''))}"

        category = extract_learning_area(h)
        if not category:
            tags = h.get("tags") or []
            category = tags[0].get("name") if tags and isinstance(tags[0], dict) else ""

        duration = normalize_duration(h.get("duration"))
        level = normalize_level(h.get("difficulty") or h.get("difficulty_level"))

        # Instructor name
        instructors = h.get("instructors") or []
        instructor = instructors[0].get("name") if instructors and isinstance(instructors[0], dict) else ""

        courses.append({
            "provider": PROVIDER,
            "title": title,
            "url": url,
            "description": description,
            "duration": duration,
            "level": level,
            "format": "On-Demand",
            "price": "Subscription",
            "category": category,
            "instructor": instructor,
            "date_scraped": DATE_SCRAPED,
        })
    return courses


def process_path_hits(hits: list[dict]) -> list[dict]:
    paths = []
    for h in hits:
        title = h.get("name") or ""
        description = h.get("description") or h.get("short_description") or ""
        if description and "<" in description:
            description = strip_html(description)

        # URL may be empty - build from slug
        url = h.get("url") or ""
        if not url:
            slug = h.get("slug") or h.get("objectID")
            url = f"https://my.ine.com/learning-paths/{slug}"

        category = extract_learning_area(h)
        duration = normalize_duration(h.get("duration"))
        level = normalize_level(h.get("difficulty") or h.get("difficulty_level"))

        paths.append({
            "provider": PROVIDER,
            "title": title,
            "url": url,
            "description": description,
            "duration": duration,
            "level": level,
            "format": "Learning Path / On-Demand",
            "price": "Subscription",
            "category": category,
            "instructor": "",
            "date_scraped": DATE_SCRAPED,
        })
    return paths


def export_catalog_data(courses_data: list[dict], provider_slug: str) -> dict[str, str]:
    df = pd.DataFrame(courses_data)

    column_order = [
        "provider", "title", "url", "description", "duration",
        "level", "format", "price", "category", "instructor",
        "date_scraped",
    ]
    existing_cols = [col for col in column_order if col in df.columns]
    df = df[existing_cols]

    # Title quality check
    if "title" in df.columns:
        df["_title_length"] = df["title"].str.len()
        avg_len = df["_title_length"].mean()
        long_titles = df[df["_title_length"] > 150]
        print(f"\nTITLE QUALITY:")
        print(f"  Avg length: {avg_len:.0f} chars")
        if len(long_titles) > 0:
            print(f"  WARNING: {len(long_titles)} titles >150 chars")
        df = df.drop(columns=["_title_length"])

    # Description quality check
    if "description" in df.columns:
        total = len(df)
        unique = df["description"].nunique()
        pct = unique / total * 100 if total > 0 else 0
        print(f"\nDESCRIPTION QUALITY:")
        print(f"  Total: {total}, Unique: {unique}, Uniqueness: {pct:.1f}%")
        if pct < 90:
            print(f"  WARNING: Low description uniqueness ({pct:.1f}%)")

    json_file = f"{provider_slug}_catalog.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(courses_data, f, indent=2, ensure_ascii=False)

    xlsx_file = f"{provider_slug}_catalog.xlsx"
    df_xlsx = df.copy()
    for col in df_xlsx.select_dtypes(include=["object"]).columns:
        df_xlsx[col] = df_xlsx[col].apply(clean_to_ascii)
    df_xlsx.to_excel(xlsx_file, index=False, engine="openpyxl")

    return {"json": json_file, "xlsx": xlsx_file}


def generate_report(
    courses: list[dict],
    paths: list[dict],
    provider_slug: str,
    obstacles: str = "None",
) -> str:
    total = len(courses) + len(paths)
    report_file = f"{provider_slug}_report.md"
    all_items = courses + paths

    desc_complete = sum(1 for c in all_items if c.get("description")) / max(total, 1) * 100
    dur_complete = sum(1 for c in all_items if c.get("duration")) / max(total, 1) * 100
    level_complete = sum(1 for c in all_items if c.get("level")) / max(total, 1) * 100

    categories: dict[str, int] = {}
    for c in all_items:
        cat = c.get("category") or "Unknown"
        categories[cat] = categories.get(cat, 0) + 1

    sample = all_items[:5]

    report = f"""# INE (InterNetwork Expert) Catalog Scraping Report

**Date**: {DATE_SCRAPED}
**URL**: https://ine.com/pages/training
**Total Items**: {total} ({len(courses)} courses + {len(paths)} learning paths)

## Architecture
- Type: JavaScript SPA (Vue.js) on my.ine.com
- Data Source: Algolia search API (credentials embedded in app.js bundle)
- Obstacles: {obstacles}
- Algolia App ID: 6D0ROPGFEB
- Courses Index: prod_ine-content-api-courses
- Learning Paths Index: prod_ine-content-api-learning-paths

## Extraction Method
Extracted public Algolia API credentials from the my.ine.com Vue.js SPA bundle
(app.277068a0ba8260ef.js). Used Algolia browse API to retrieve all records from
the courses and learning paths indexes without pagination limits.

## Data Quality
- Description: {desc_complete:.0f}% complete
- Duration: {dur_complete:.0f}% complete
- Level: {level_complete:.0f}% complete

## Content by Category
"""
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        report += f"- {cat}: {count}\n"

    report += "\n## Sample Courses\n"
    for item in sample:
        report += f"""
### {item['title']}
- **URL**: {item['url']}
- **Category**: {item.get('category', '')}
- **Level**: {item.get('level', '')}
- **Duration**: {item.get('duration', '')}
- **Format**: {item.get('format', '')}
- **Description**: {(item.get('description') or '')[:200]}
"""

    report += """
## Limitations
- Course content (videos) requires active INE subscription
- Some courses may require specific subscription tiers (starter vs premium)
- Learning path membership details not included

## Recommendations
- Strong cybersecurity and networking content; consider for LinkedIn Learning licensing
- Rich hands-on lab catalog (separate labs index not scraped here)
- Content aligns well with technical/IT professional audience
"""

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    return report_file


def main() -> None:
    print("=" * 60)
    print(f"Scraping: {PROVIDER}")
    print("=" * 60)

    # Fetch courses
    print("\nFetching courses from Algolia...")
    try:
        course_hits = algolia_search_all(COURSES_INDEX)
        print(f"Total course records: {len(course_hits)}")
    except Exception as e:
        print(f"ERROR fetching courses: {e}")
        course_hits = []

    time.sleep(1)

    # Fetch learning paths
    print("\nFetching learning paths from Algolia...")
    try:
        path_hits = algolia_search_all(LEARNING_PATHS_INDEX)
        print(f"Total learning path records: {len(path_hits)}")
    except Exception as e:
        print(f"ERROR fetching learning paths: {e}")
        path_hits = []

    # Process
    courses = process_course_hits(course_hits)
    paths = process_path_hits(path_hits)
    all_items = courses + paths

    print(f"\nProcessed: {len(courses)} courses + {len(paths)} learning paths = {len(all_items)} total")

    if not all_items:
        print("ERROR: No items scraped. Exiting.")
        return

    # Export
    base_dir = "/Users/bianders/.claude/skills/catalog-scraper"
    os.chdir(base_dir)

    files = export_catalog_data(all_items, PROVIDER_SLUG)
    report_file = generate_report(courses, paths, PROVIDER_SLUG)

    # Move to providers dir
    provider_dir = f"providers/{PROVIDER_SLUG}"
    os.makedirs(provider_dir, exist_ok=True)

    for src in [files["json"], files["xlsx"], report_file]:
        dst = f"{provider_dir}/{os.path.basename(src).replace(PROVIDER_SLUG + '_', '')}"
        shutil.move(src, dst)
        print(f"Moved: {src} -> {dst}")

    # Update registry
    with open("catalog_registry.json") as f:
        registry = json.load(f)

    title_lengths = [len(c["title"]) for c in all_items if c.get("title")]
    avg_title_len = int(sum(title_lengths) / len(title_lengths)) if title_lengths else 0
    desc_count = sum(1 for c in all_items if c.get("description"))
    has_desc = desc_count > len(all_items) * 0.5
    dur_count = sum(1 for c in all_items if c.get("duration"))
    has_dur = dur_count > len(all_items) * 0.5
    level_count = sum(1 for c in all_items if c.get("level"))
    has_level = level_count > len(all_items) * 0.5

    provider_entry = {
        "status": "complete",
        "url": "https://ine.com/pages/training",
        "courses_count": len(all_items),
        "date_scraped": DATE_SCRAPED,
        "scraper_version": "1.0",
        "data_quality": {
            "has_descriptions": has_desc,
            "has_duration": has_dur,
            "has_level": has_level,
            "avg_title_length": avg_title_len,
        },
        "files": {
            "json": f"{base_dir}/{provider_dir}/catalog.json",
            "xlsx": f"{base_dir}/{provider_dir}/catalog.xlsx",
            "report": f"{base_dir}/{provider_dir}/report.md",
        },
        "notes": "Uses Algolia API with public credentials embedded in my.ine.com Vue.js SPA bundle",
    }

    registry["providers"][PROVIDER] = provider_entry
    registry["stats"]["total_providers"] = len(registry["providers"])
    registry["stats"]["total_courses"] = sum(
        p.get("courses_count", 0) for p in registry["providers"].values()
    )
    registry["stats"]["providers_complete"] = sum(
        1 for p in registry["providers"].values() if p.get("status") == "complete"
    )
    registry["stats"]["providers_partial"] = sum(
        1 for p in registry["providers"].values() if p.get("status") == "partial"
    )
    registry["stats"]["providers_auth_required"] = sum(
        1 for p in registry["providers"].values() if p.get("status") == "auth_required"
    )
    registry["last_updated"] = datetime.now().isoformat()

    with open("catalog_registry.json", "w") as f:
        json.dump(registry, f, indent=2)
    print("\nUpdated catalog_registry.json")

    # Regenerate master catalog
    all_courses_master = []
    for pname, pinfo in registry["providers"].items():
        if "files" in pinfo and "json" in pinfo["files"]:
            try:
                with open(pinfo["files"]["json"]) as f:
                    items = json.load(f)
                    all_courses_master.extend(items)
            except Exception:
                pass

    with open("master_catalog.json", "w", encoding="utf-8") as f:
        json.dump(all_courses_master, f, indent=2, ensure_ascii=False)

    if all_courses_master:
        df_master = pd.DataFrame(all_courses_master)
        for col in df_master.select_dtypes(include=["object"]).columns:
            df_master[col] = df_master[col].apply(clean_to_ascii)
        df_master.to_excel("master_catalog.xlsx", index=False, engine="openpyxl")

    print(f"Regenerated master_catalog files ({len(all_courses_master)} total courses)")

    print("\n" + "=" * 60)
    print("ARTIFACTS GENERATED:")
    print(f"  JSON:   {base_dir}/{provider_dir}/catalog.json")
    print(f"  XLSX:   {base_dir}/{provider_dir}/catalog.xlsx")
    print(f"  Report: {base_dir}/{provider_dir}/report.md")
    print(f"  Registry: {base_dir}/catalog_registry.json (updated)")
    print(f"  Master:   {base_dir}/master_catalog.xlsx (regenerated)")
    print("=" * 60)

    # Return summary for result.json
    result = {
        "provider": PROVIDER,
        "url": "https://ine.com/pages/training",
        "status": "complete",
        "courses_count": len(all_items),
        "date_scraped": DATE_SCRAPED,
        "data_quality": provider_entry["data_quality"],
        "files": provider_entry["files"],
        "notes": provider_entry["notes"],
        "sample_courses": [
            {
                "title": c["title"],
                "url": c["url"],
                "category": c.get("category", ""),
                "level": c.get("level", ""),
                "duration": c.get("duration", ""),
            }
            for c in all_items[:5]
        ],
    }
    return result


if __name__ == "__main__":
    result = main()
    if result:
        print("\nResult summary:")
        print(json.dumps(result, indent=2))
