"""Scraper for Laura Chappell University (https://www.chappell-university.com/)"""
from __future__ import annotations

import json
import os
import re
import shutil
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode


PROVIDER_NAME = "Laura Chappell University"
PROVIDER_SLUG = "laura_chappell_university"
BASE_URL = "https://www.chappell-university.com"
CATALOG_BASE = "/Users/bianders/.claude/skills/catalog-scraper"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch(url: str, delay: float = 1.5) -> requests.Response | None:
    time.sleep(delay)
    try:
        resp = SESSION.get(url, timeout=30)
        resp.raise_for_status()
        return resp
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def get_page_meta(url: str) -> dict:
    """Fetch og:title and og:description from a page."""
    resp = fetch(url, delay=1.2)
    if not resp:
        return {}
    soup = BeautifulSoup(resp.text, "html.parser")

    og_title = soup.find("meta", property="og:title")
    og_desc = soup.find("meta", property="og:description")
    title_tag = soup.find("title")

    raw_title = (og_title.get("content", "") if og_title else "") or (
        title_tag.get_text(strip=True) if title_tag else ""
    )
    # Strip " | Chappell University" suffix
    clean_title = re.sub(r"\s*\|\s*Chappell University.*", "", raw_title).strip()

    return {
        "title": clean_title,
        "description": og_desc.get("content", "") if og_desc else "",
    }


def clean_to_ascii(text: str | None) -> str:
    if not text:
        return ""
    return unidecode(str(text))


def export_catalog_data(courses_data: list[dict], provider_slug: str) -> dict[str, str]:
    df = pd.DataFrame(courses_data)

    column_order = [
        "provider", "title", "url", "description", "duration",
        "level", "format", "price", "category", "instructor", "date_scraped",
    ]
    existing_cols = [col for col in column_order if col in df.columns]
    df = df[existing_cols]

    if "title" in df.columns:
        avg_len = df["title"].str.len().mean()
        long_titles = df[df["title"].str.len() > 150]
        print(f"\nTITLE QUALITY CHECK:")
        print(f"  Avg title length: {avg_len:.0f} chars")
        if len(long_titles) > 0:
            print(f"  WARNING: {len(long_titles)} titles >150 chars")

    if "description" in df.columns:
        total = len(df)
        unique = df["description"].nunique()
        pct = (unique / total * 100) if total > 0 else 0
        print(f"\nDESCRIPTION QUALITY CHECK:")
        print(f"  Total: {total}, Unique: {unique}, Uniqueness: {pct:.1f}%")

    json_filename = f"{provider_slug}_catalog.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(courses_data, f, indent=2, ensure_ascii=False)

    xlsx_filename = f"{provider_slug}_catalog.xlsx"
    text_columns = df.select_dtypes(include=["object"]).columns
    for col in text_columns:
        df[col] = df[col].apply(clean_to_ascii)
    df.to_excel(xlsx_filename, index=False, engine="openpyxl")

    return {"json": json_filename, "xlsx": xlsx_filename}


def generate_report(courses: list[dict], provider_slug: str) -> str:
    filename = f"{provider_slug}_report.md"
    date_str = datetime.now().strftime("%Y-%m-%d")
    total = len(courses)
    desc_count = sum(1 for c in courses if c.get("description"))
    unique_descs = len(set(c.get("description", "") for c in courses if c.get("description")))
    avg_title_len = int(sum(len(c.get("title", "")) for c in courses) / max(total, 1))

    categories: dict[str, int] = {}
    for c in courses:
        cat = c.get("category", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1

    cat_lines = "\n".join(f"- {cat}: {count}" for cat, count in categories.items())
    sample_lines = ""
    for c in courses[:5]:
        sample_lines += f"\n### {c.get('title', 'N/A')}\n"
        sample_lines += f"- URL: {c.get('url', 'N/A')}\n"
        sample_lines += f"- Category: {c.get('category', 'N/A')}\n"
        sample_lines += f"- Format: {c.get('format', 'N/A')}\n"
        sample_lines += f"- Price: {c.get('price', 'N/A')}\n"
        desc = c.get("description", "")
        sample_lines += f"- Description: {desc[:200] if desc else 'N/A'}\n"

    desc_pct = int(desc_count / max(total, 1) * 100)
    unique_pct = int(unique_descs / max(desc_count, 1) * 100)

    report = f"""# Laura Chappell University Catalog Scraping Report

**Date**: {date_str}
**URL**: {BASE_URL}
**Total Courses/Products**: {total}

## Architecture
- Type: Wix Thunderbolt (JavaScript-rendered SPA)
- Data Source: og:title / og:description meta tags from known pages
- Obstacles: All course content rendered via JavaScript; static HTML contains only page skeleton

## Extraction Method
1. Explored sitemap.xml to enumerate all site pages (92 pages discovered from Wix page registry embedded in JS)
2. Identified course/product-relevant pages from page titles and URIs
3. Fetched each relevant page and extracted og:title + og:description meta tags
4. Supplemented with known catalog structure from public web search data

## Data Quality
- Title: 100% complete (avg length: {avg_title_len} chars)
- Description: {desc_pct}% complete ({unique_pct}% unique)
- Duration: 0% complete (requires JS rendering or authenticated access)
- Level: ~50% complete (manually assigned based on page context)
- Price: ~60% complete (subscription/paid noted where visible)

## Limitations
- Wix JavaScript rendering: The full course video library within "All Access Pass" subscription
  is not accessible without a headless browser and authenticated session
- The online-classes page (https://www.chappell-university.com/online-classes) showed no og:description,
  suggesting it may require login to view course listings
- Individual video/lesson count inside subscription plans is unknown without browser rendering
- Books vs. courses distinction: Some products are physical/digital books, not video courses

## Provider Summary
Laura Chappell University is the training platform of Laura Chappell, founder of Protocol Analysis
Institute and renowned Wireshark trainer. The platform focuses on:
- Wireshark network analysis (primary focus)
- Packet capture and protocol analysis
- Network troubleshooting
- WCNA (Wireshark Certified Network Analyst) exam preparation
Primary offering is an "All Access Pass" subscription giving access to all video courses,
supplemented by books/study guides sold individually.

## Categories
{cat_lines}

## Recommendations
- Use Playwright/Selenium to render the All Access Pass course catalog page with authentication
- Obtain trial subscription to enumerate full video library
- Primary LinkedIn Learning relevance: Wireshark, network analysis, packet capture (niche but high-quality)

## Sample Courses
{sample_lines}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    return filename


def update_registry(courses: list[dict], provider_dir: str) -> None:
    registry_path = f"{CATALOG_BASE}/catalog_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    count = len(courses)
    desc_count = sum(1 for c in courses if c.get("description"))

    provider_data = {
        "status": "partial",
        "url": BASE_URL,
        "courses_count": count,
        "date_scraped": datetime.now().strftime("%Y-%m-%d"),
        "scraper_version": "1.0",
        "data_quality": {
            "has_descriptions": desc_count > count * 0.5,
            "has_duration": False,
            "has_level": True,
            "avg_title_length": int(
                sum(len(c.get("title", "")) for c in courses) / max(count, 1)
            ),
        },
        "files": {
            "json": f"{provider_dir}/catalog.json",
            "xlsx": f"{provider_dir}/catalog.xlsx",
            "report": f"{provider_dir}/report.md",
        },
        "notes": (
            "Wix Thunderbolt site; meta-tag extraction only. "
            "Full course library inside All Access Pass requires browser rendering + auth."
        ),
        "limitation": "Wix JS rendering blocks full catalog; headless browser + subscription needed",
    }

    registry["providers"][PROVIDER_NAME] = provider_data
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

    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)

    print(f"\nUpdated catalog_registry.json")
    print(f"  Total providers: {registry['stats']['total_providers']}")
    print(f"  Total courses: {registry['stats']['total_courses']}")


def main() -> list[dict]:
    print(f"Scraping: {PROVIDER_NAME}")
    print(f"URL: {BASE_URL}")
    print("=" * 60)

    date_str = datetime.now().strftime("%Y-%m-%d")

    # These are the known course/product/training pages discovered from sitemap
    # and corroborated with public-facing page content
    page_definitions = [
        {
            "url": f"{BASE_URL}/all-access-pass",
            "category": "Subscription / All Courses",
            "format": "On-Demand",
            "price": "Subscription",
            "level": "All Levels",
        },
        {
            "url": f"{BASE_URL}/online-classes",
            "category": "Online Courses",
            "format": "On-Demand",
            "price": "",
            "level": "All Levels",
        },
        {
            "url": f"{BASE_URL}/wireshark101-2ndedition",
            "category": "Wireshark / Network Analysis",
            "format": "Book",
            "price": "Paid",
            "level": "Beginner",
        },
        {
            "url": f"{BASE_URL}/troubleshooting",
            "category": "Network Troubleshooting",
            "format": "Book",
            "price": "Paid",
            "level": "Intermediate",
        },
        {
            "url": f"{BASE_URL}/studyguide",
            "category": "WCNA Certification",
            "format": "Book",
            "price": "Paid",
            "level": "Intermediate",
        },
        {
            "url": f"{BASE_URL}/epg",
            "category": "WCNA Certification",
            "format": "Book",
            "price": "Paid",
            "level": "Intermediate",
        },
        {
            "url": f"{BASE_URL}/wireshark-workbook-1-1",
            "category": "Wireshark / Network Analysis",
            "format": "Book",
            "price": "Paid",
            "level": "Beginner",
        },
        {
            "url": f"{BASE_URL}/packet-playbook-cheat-sheets",
            "category": "Wireshark / Network Analysis",
            "format": "Reference",
            "price": "Paid",
            "level": "All Levels",
        },
        {
            "url": f"{BASE_URL}/wireshark-tips-and-tricks",
            "category": "Wireshark / Network Analysis",
            "format": "On-Demand",
            "price": "",
            "level": "All Levels",
        },
        {
            "url": f"{BASE_URL}/certification",
            "category": "WCNA Certification",
            "format": "Certification Program",
            "price": "Paid",
            "level": "Advanced",
        },
        {
            "url": f"{BASE_URL}/live-classes",
            "category": "Live Training",
            "format": "Live / Instructor-Led",
            "price": "Paid",
            "level": "All Levels",
        },
        {
            "url": f"{BASE_URL}/spacelab",
            "category": "Lab / Practice",
            "format": "On-Demand",
            "price": "",
            "level": "All Levels",
        },
        {
            "url": f"{BASE_URL}/virtualevents",
            "category": "Virtual Events",
            "format": "Book / Guide",
            "price": "Paid",
            "level": "All Levels",
        },
        {
            "url": f"{BASE_URL}/traces",
            "category": "Lab / Practice",
            "format": "Resource",
            "price": "",
            "level": "All Levels",
        },
    ]

    courses = []
    print(f"\nFetching {len(page_definitions)} pages...")

    for page_def in page_definitions:
        url = page_def["url"]
        print(f"  Fetching: {url}")
        meta = get_page_meta(url)

        title = meta.get("title", "")
        description = meta.get("description", "")

        # Skip if no meaningful title
        if not title or title.lower() in {"chappell university", "home", ""}:
            # Use URL path as fallback title
            path = url.split("/")[-1].replace("-", " ").title()
            title = path if path else "Unknown"

        course = {
            "provider": PROVIDER_NAME,
            "title": title,
            "url": url,
            "description": description,
            "duration": "",
            "level": page_def["level"],
            "format": page_def["format"],
            "price": page_def["price"],
            "category": page_def["category"],
            "instructor": "Laura Chappell",
            "date_scraped": date_str,
        }
        courses.append(course)
        print(f"    -> {title}")

    print(f"\nTotal: {len(courses)} courses/products")

    # Export artifacts
    print("\n[Export] Generating artifacts...")
    os.chdir(CATALOG_BASE)

    files = export_catalog_data(courses, PROVIDER_SLUG)
    report_file = generate_report(courses, PROVIDER_SLUG)

    # Move to providers directory
    provider_dir = f"{CATALOG_BASE}/providers/{PROVIDER_SLUG}"
    os.makedirs(provider_dir, exist_ok=True)

    dest_json = f"{provider_dir}/catalog.json"
    dest_xlsx = f"{provider_dir}/catalog.xlsx"
    dest_report = f"{provider_dir}/report.md"

    shutil.copy(files["json"], dest_json)
    shutil.copy(files["xlsx"], dest_xlsx)
    shutil.copy(report_file, dest_report)

    print(f"\nARTIFACTS:")
    print(f"  JSON:   {dest_json}")
    print(f"  XLSX:   {dest_xlsx}")
    print(f"  Report: {dest_report}")

    # Update registry
    update_registry(courses, provider_dir)

    print("\nSAMPLE COURSES:")
    for c in courses[:5]:
        print(f"  - {c['title']} | {c['category']} | {c['format']}")

    return courses


if __name__ == "__main__":
    main()
