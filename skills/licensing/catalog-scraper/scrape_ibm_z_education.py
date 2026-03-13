"""
IBM Z Education course catalog scraper.
Source: https://www.ibm.com/products/z/education -> IBM Training platform

Strategy: IBM Training uses a Swiftype search API (POST /training/swiftype/searchresults).
Pagination is non-functional (always returns same ~100 results), so we search
multiple IBM Z-specific terms and deduplicate by URL.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from unidecode import unidecode


PROVIDER = "IBM Z Education"
PROVIDER_SLUG = "ibm_z_education"
BASE_URL = "https://www.ibm.com/products/z/education"
SEARCH_API = "https://www.ibm.com/training/swiftype/searchresults"

# IBM Z-specific search terms to maximize course coverage
SEARCH_TERMS = [
    "mainframe",
    "z/os",
    "COBOL",
    "CICS",
    "IMS",
    "RACF",
    "IBM Z",
    "LinuxONE",
    "z/VM",
    "DB2 z/OS",
    "JCL",
    "ISPF",
    "REXX",
    "z16",
    "MQ z/OS",
    "Db2 zOS",
    "zOS system",
    "z/OS security",
    "VSAM",
    "Assembler z/OS",
    "z/OSMF",
    "z/OS networking",
    "z/OS performance",
    "System z",
    "zDevOps",
    "z/OS storage",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.ibm.com/training/systems",
    "Origin": "https://www.ibm.com",
}


def search_ibm_training(term: str) -> list[dict]:
    payload = {
        "searchString": term,
        "enteredSearchString": term,
        "filters": {},
        "startIndex": 0,
        "resultsPerPage": 100,
        "page": 1,
        "tagCount": 0,
        "keystate": 1,
        "firstLoad": False,
        "learningType": False,
        "delivery": False,
        "category": False,
        "jobFamily": False,
        "skillLevel": False,
        "cost": False,
        "retired": False,
        "badgeType": False,
        "isCheck": False,
        "categorySearch": "",
        "entPublic": [],
        "entSelf": [],
    }
    try:
        resp = requests.post(SEARCH_API, json=payload, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["resultset"]["searchresults"].get("searchresultlist", [])
    except Exception as e:
        print(f"  Warning: search '{term}' failed: {e}")
        return []


def clean_title(raw_title: str) -> str:
    """Strip 'Course: ... - IBM Training - Global' boilerplate."""
    title = raw_title.strip()
    # Remove common suffixes
    for suffix in [" - IBM Training - Global", " - IBM Training"]:
        if title.endswith(suffix):
            title = title[: -len(suffix)]
    # Remove 'Course: ' prefix
    if title.startswith("Course: "):
        title = title[8:]
    return title.strip()


def parse_level(title: str, description: str) -> str:
    text = (title + " " + description).lower()
    if "advanced" in text:
        return "Advanced"
    if "intermediate" in text:
        return "Intermediate"
    if "basic" in text or "introduction" in text or "intro " in text or "fundamentals" in text:
        return "Beginner"
    return ""


def parse_format(result: dict) -> str:
    """Derive format from URL or known delivery codes in description."""
    url = result.get("url", "")
    desc = result.get("description", "").lower()
    if "instructor-led" in desc or "classroom" in desc:
        return "Instructor-Led"
    if "self-paced" in desc or "on-demand" in desc or "wbt" in desc.lower():
        return "Self-Paced"
    if "virtual" in desc:
        return "Virtual"
    return "On-Demand"


def parse_category(title: str, description: str) -> str:
    text = (title + " " + description).lower()
    if "cobol" in text:
        return "COBOL Programming"
    if "cics" in text:
        return "CICS"
    if "ims" in text and ("z/os" in text or "mainframe" in text):
        return "IMS"
    if "racf" in text or "security" in text:
        return "Security"
    if "db2" in text or "database" in text:
        return "Databases"
    if "devops" in text or "dependency based build" in text or "dbb" in text:
        return "DevOps"
    if "networking" in text or "tcp/ip" in text:
        return "Networking"
    if "storage" in text or "vsam" in text:
        return "Storage"
    if "linuxone" in text or "linux" in text:
        return "LinuxONE"
    if "performance" in text or "tuning" in text:
        return "Performance"
    if "java" in text:
        return "Java on Z"
    if "operations" in text or "operator" in text:
        return "Operations"
    if "system programmer" in text or "sysprog" in text:
        return "System Programming"
    if "z/osmf" in text or "osmf" in text:
        return "z/OSMF"
    if "rexx" in text or "jcl" in text or "ispf" in text:
        return "JCL/REXX/ISPF"
    if "z/vm" in text:
        return "z/VM"
    if "bootcamp" in text or "overview" in text or "introduction" in text:
        return "Foundation"
    if "mq" in text:
        return "MQ"
    return "IBM Z"


def collect_courses() -> list[dict]:
    all_results: dict[str, dict] = {}

    for i, term in enumerate(SEARCH_TERMS, 1):
        print(f"  [{i}/{len(SEARCH_TERMS)}] Searching: '{term}'")
        results = search_ibm_training(term)

        new_courses = 0
        for r in results:
            url = r.get("url", "")
            # Only keep IBM Training course/path pages
            if "/training/course/" not in url and "/training/path/" not in url:
                continue
            if url not in all_results:
                all_results[url] = r
                new_courses += 1

        print(f"    -> {new_courses} new courses (total unique: {len(all_results)})")
        time.sleep(0.5)

    return list(all_results.values())


def transform_course(raw: dict) -> dict:
    raw_title = raw.get("title", "")
    title = clean_title(raw_title)
    description = raw.get("description", "").strip()
    url = raw.get("url", "")

    # Derive format from URL path
    fmt = "On-Demand"
    if "/training/path/" in url:
        fmt = "Learning Path"

    level = parse_level(title, description)
    category = parse_category(title, description)

    return {
        "provider": PROVIDER,
        "title": title,
        "url": url,
        "description": description,
        "duration": "",
        "level": level,
        "format": fmt,
        "price": "",
        "category": category,
        "date_scraped": datetime.now().strftime("%Y-%m-%d"),
    }


def clean_to_ascii(text: str | None) -> str:
    if not text:
        return ""
    return unidecode(str(text))


def main() -> None:
    script_dir = Path(__file__).parent

    print(f"\n{'='*60}")
    print(f"IBM Z Education Course Catalog Scraper")
    print(f"{'='*60}")
    print(f"Source: {BASE_URL}")
    print(f"API: {SEARCH_API}")
    print(f"Terms: {len(SEARCH_TERMS)}")
    print()

    print("Phase 1: Collecting courses from search API...")
    raw_courses = collect_courses()
    print(f"\nTotal unique IBM Training courses found: {len(raw_courses)}")

    print("\nPhase 2: Transforming to standard format...")
    courses = [transform_course(r) for r in raw_courses]

    # Quality checks
    df = pd.DataFrame(courses)
    avg_title_len = df["title"].str.len().mean()
    long_titles = df[df["title"].str.len() > 150]
    unique_descs = df["description"].nunique()
    desc_pct = unique_descs / len(df) * 100 if len(df) > 0 else 0

    print(f"\nQuality check:")
    print(f"  Total courses: {len(courses)}")
    print(f"  Avg title length: {avg_title_len:.0f} chars")
    print(f"  Titles >150 chars: {len(long_titles)}")
    print(f"  Unique descriptions: {unique_descs} ({desc_pct:.0f}%)")

    # Save JSON
    json_path = script_dir / f"{PROVIDER_SLUG}_catalog.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)
    print(f"\nSaved JSON: {json_path}")

    # Save XLSX
    xlsx_path = script_dir / f"{PROVIDER_SLUG}_catalog.xlsx"
    df_xlsx = df.copy()
    for col in df_xlsx.select_dtypes(include=["object"]).columns:
        df_xlsx[col] = df_xlsx[col].apply(clean_to_ascii)
    df_xlsx.to_excel(xlsx_path, index=False, engine="openpyxl")
    print(f"Saved XLSX: {xlsx_path}")

    # Category breakdown
    cat_counts = df["category"].value_counts()
    level_counts = df["level"].value_counts()
    fmt_counts = df["format"].value_counts()

    print("\nCategory breakdown:")
    for cat, count in cat_counts.head(15).items():
        print(f"  {cat}: {count}")

    print("\nLevel breakdown:")
    for lvl, count in level_counts.items():
        print(f"  {lvl}: {count}")

    return courses, str(json_path), str(xlsx_path), cat_counts, level_counts, fmt_counts


if __name__ == "__main__":
    result = main()
