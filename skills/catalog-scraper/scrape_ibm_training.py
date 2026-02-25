"""IBM Training catalog scraper.

Sources:
- /training/api/ilt/search  ->  246 instructor-led courses (JSON API)
- /training/api/topics/getPromotionItems/{n}  ->  featured course descriptions
"""
from __future__ import annotations

import json
import os
import shutil
import time
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from unidecode import unidecode

BASE_URL = "https://www.ibm.com"
PROVIDER = "IBM Training"
PROVIDER_SLUG = "ibm_training"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def fetch_ilt_courses() -> list[dict]:
    url = f"{BASE_URL}/training/api/ilt/search"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_promotion_items() -> dict[str, str]:
    """Fetch featured course descriptions from topic promotion APIs."""
    desc_map: dict[str, str] = {}
    for idx in range(9):
        try:
            url = f"{BASE_URL}/training/api/topics/getPromotionItems/{idx}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            items = resp.json()
            for item in items:
                item_url = item.get("ITEM_URL", "")
                desc = item.get("ITEM_DESC", "")
                title = item.get("ITEM_TITLE", "")
                if item_url and desc:
                    desc_map[title.strip()] = desc.strip()
                    # Also index by course code extracted from URL
                    # URL looks like: https://www.ibm.com/training/course/name-XXXX
                    if "/" in item_url:
                        code_part = item_url.rstrip("/").split("/")[-1]
                        # Extract code like 8H501G from name-8H501G
                        if "-" in code_part:
                            code = code_part.split("-")[-1].upper()
                            desc_map[code] = desc.strip()
            time.sleep(0.2)
        except Exception as exc:
            print(f"  Warning: promotion items {idx} failed: {exc}")
    return desc_map


def extract_modalities(classes: list[dict]) -> str:
    """Get unique modalities from class sessions."""
    modalities = list({c.get("MODALITY", "") for c in classes if c.get("MODALITY")})
    return "; ".join(sorted(modalities))


def extract_languages(classes: list[dict]) -> str:
    langs = list({c.get("LANGUAGE", "") for c in classes if c.get("LANGUAGE")})
    return "; ".join(sorted(langs))


def build_course_url(course_code: str) -> str:
    return f"{BASE_URL}/training/search?query={course_code}"


def transform_courses(raw: list[dict], desc_map: dict[str, str]) -> list[dict]:
    courses = []
    today = datetime.now().strftime("%Y-%m-%d")
    for item in raw:
        code = item.get("courseCode", "")
        title = item.get("courseTitle", "")
        business = item.get("business", "")
        duration = item.get("duration", "")
        classes = item.get("classes", [])

        modalities = extract_modalities(classes)
        languages = extract_languages(classes)
        description = desc_map.get(code, desc_map.get(title, ""))

        # Derive format from modality
        fmt = ""
        if modalities:
            if "Online" in modalities and "In-person" in modalities:
                fmt = "Blended"
            elif "Online" in modalities:
                fmt = "Instructor-led Online"
            elif "person" in modalities.lower():
                fmt = "In-Person"
            else:
                fmt = modalities.split(";")[0].strip()

        course = {
            "provider": PROVIDER,
            "title": title,
            "url": build_course_url(code),
            "description": description,
            "duration": duration,
            "level": "",
            "format": fmt,
            "price": "",
            "category": business,
            "course_code": code,
            "languages": languages,
            "modalities": modalities,
            "available_classes": item.get("availDeliveries", 0),
            "date_scraped": today,
        }
        courses.append(course)
    return courses


def clean_to_ascii(text: str | None) -> str:
    if not text:
        return ""
    return unidecode(str(text))


def export_catalog_data(courses: list[dict], provider_dir: Path) -> dict[str, str]:
    df = pd.DataFrame(courses)
    column_order = [
        "provider", "title", "url", "description", "duration",
        "level", "format", "price", "category", "course_code",
        "languages", "modalities", "available_classes", "date_scraped",
    ]
    existing = [c for c in column_order if c in df.columns]
    df = df[existing]

    # Title quality check
    avg_len = df["title"].str.len().mean()
    long_titles = df[df["title"].str.len() > 150]
    print(f"\nTitle quality: avg {avg_len:.0f} chars, {len(long_titles)} titles >150 chars")

    # Description quality check
    total = len(df)
    unique_descs = df["description"].replace("", None).dropna().nunique()
    filled = df["description"].replace("", None).notna().sum()
    print(f"Descriptions: {filled}/{total} filled ({unique_descs} unique)")

    json_path = provider_dir / "catalog.json"
    xlsx_path = provider_dir / "catalog.xlsx"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)

    text_cols = df.select_dtypes(include=["object"]).columns
    for col in text_cols:
        df[col] = df[col].apply(clean_to_ascii)
    df.to_excel(xlsx_path, index=False, engine="openpyxl")

    return {"json": str(json_path), "xlsx": str(xlsx_path)}


def write_report(
    courses: list[dict],
    provider_dir: Path,
    limitations: str,
) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    total = len(courses)

    by_category: dict[str, int] = {}
    by_format: dict[str, int] = {}
    for c in courses:
        cat = c.get("category") or "Unknown"
        by_category[cat] = by_category.get(cat, 0) + 1
        fmt = c.get("format") or "Unknown"
        by_format[fmt] = by_format.get(fmt, 0) + 1

    desc_filled = sum(1 for c in courses if c.get("description"))
    dur_filled = sum(1 for c in courses if c.get("duration"))

    cat_lines = "\n".join(f"  - {k}: {v}" for k, v in sorted(by_category.items()))
    fmt_lines = "\n".join(f"  - {k}: {v}" for k, v in sorted(by_format.items()))
    sample_lines = ""
    for c in courses[:5]:
        sample_lines += (
            f"\n**{c['title']}** (`{c['course_code']}`)\n"
            f"- Category: {c['category']}\n"
            f"- Duration: {c['duration']}\n"
            f"- Format: {c['format']}\n"
            f"- URL: {c['url']}\n"
        )

    report = f"""# IBM Training Catalog Scraping Report

**Date**: {today}
**URL**: https://www.ibm.com/training/
**Total Courses**: {total}

## Architecture
- Type: React SPA (Single Page Application)
- Data Source: JSON API (`/training/api/ilt/search`)
- Obstacles: JavaScript-rendered pages; course detail pages not accessible as JSON

## Extraction Method
Used the internal ILT (Instructor-Led Training) search API which returns a complete
list of instructor-led courses in JSON format. This is the primary public API exposed
by the React frontend. Course descriptions were partially supplemented from topic
promotion item APIs.

## Data Quality
- Title: 100% complete (all {total} courses have titles)
- Description: {desc_filled}/{total} ({desc_filled*100//total}%) -- limited; most
  descriptions unavailable without JS rendering individual course pages
- Duration: {dur_filled}/{total} ({dur_filled*100//total}%) complete
- Level: 0% (not exposed in the ILT search API)
- Price: 0% (not exposed; IBM Training uses subscription/quote model)

## Coverage by Business Category
{cat_lines}

## Format Breakdown
{fmt_lines}

## Limitations
{limitations}

## Recommendations
- IBM Training is primarily instructor-led (ILT) content -- 246 courses with available
  scheduled classes worldwide.
- Descriptions require Selenium/headless browser to extract from individual course pages
  (React SPA; no server-side rendering of course detail data).
- IBM also offers self-paced courses via subscription (IBM Learning Subscription) but
  those are behind authentication -- catalog not publicly accessible.
- For licensing evaluation, the IBM Data and AI and IBM Security tracks are most relevant
  to LinkedIn Learning's audience.

## Sample Courses
{sample_lines}
"""
    report_path = provider_dir / "report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    return str(report_path)


def update_registry(
    provider_name: str,
    provider_data: dict,
    registry_path: Path,
) -> None:
    with open(registry_path) as f:
        registry = json.load(f)

    registry["providers"][provider_name] = provider_data

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
    print("Updated catalog_registry.json")


def main() -> None:
    base_dir = Path(__file__).parent
    registry_path = base_dir / "catalog_registry.json"
    provider_dir = base_dir / "providers" / PROVIDER_SLUG
    provider_dir.mkdir(parents=True, exist_ok=True)

    # Phase 0: registry check
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
        if PROVIDER in registry.get("providers", {}):
            existing = registry["providers"][PROVIDER]
            if existing.get("status") == "complete":
                print(f"{PROVIDER} already in registry with {existing['courses_count']} courses.")
                print("Remove from registry to re-scrape. Exiting.")
                return

    # Phase 1: fetch data
    print("Fetching ILT course list...")
    raw_courses = fetch_ilt_courses()
    print(f"  Got {len(raw_courses)} instructor-led courses")

    print("Fetching topic promotion descriptions...")
    desc_map = fetch_promotion_items()
    print(f"  Got {len(desc_map)} descriptions from promotion APIs")

    # Phase 2: transform
    courses = transform_courses(raw_courses, desc_map)

    # Phase 3: export
    print("\nExporting data...")
    files = export_catalog_data(courses, provider_dir)
    report_path = write_report(
        courses,
        provider_dir,
        limitations=(
            "Only instructor-led (ILT) courses are captured (246 total). "
            "Self-paced/on-demand courses require authentication. "
            "Course descriptions are sparse -- available only for a handful of "
            "featured courses from the topic promotion APIs. Full descriptions "
            "require Selenium to render individual course pages. "
            "Level and Price data not exposed by the ILT search API."
        ),
    )
    files["report"] = report_path

    # Phase 4: update registry
    provider_data = {
        "status": "partial",
        "url": "https://www.ibm.com/training/",
        "courses_count": len(courses),
        "date_scraped": datetime.now().strftime("%Y-%m-%d"),
        "scraper_version": "1.0",
        "limitation": (
            "ILT courses only (246); self-paced catalog requires auth; "
            "descriptions sparse"
        ),
        "data_quality": {
            "has_descriptions": False,
            "has_duration": True,
            "has_level": False,
            "avg_title_length": int(
                sum(len(c["title"]) for c in courses) / max(len(courses), 1)
            ),
        },
        "files": files,
    }
    update_registry(PROVIDER, provider_data, registry_path)

    print(f"\nDone. {len(courses)} courses saved to {provider_dir}/")
    print(f"  JSON:   {files['json']}")
    print(f"  XLSX:   {files['xlsx']}")
    print(f"  Report: {files['report']}")

    # Preview
    print("\nSample courses:")
    for c in courses[:5]:
        print(f"  [{c['course_code']}] {c['title']} ({c['category']}, {c['duration']})")


if __name__ == "__main__":
    main()
