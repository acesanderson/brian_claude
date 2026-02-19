"""Scraper for The Taggart Institute course catalog."""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime

import pandas as pd
from unidecode import unidecode


PROVIDER_NAME = "The Taggart Institute"
PROVIDER_SLUG = "taggart_institute"
BASE_URL = "https://taggartinstitute.org"
CATALOG_URL = "https://taggartinstitute.org/courses"
DATE_SCRAPED = datetime.now().strftime("%Y-%m-%d")


def clean_to_ascii(text: str | None) -> str:
    if not text:
        return ""
    return unidecode(str(text))


# Hand-collected course data (site uses Next.js SPA with dynamic loading;
# static HTML only shows skeleton loaders, no embedded __NEXT_DATA__ with courses)
COURSES_RAW: list[dict] = [
    {
        "provider": PROVIDER_NAME,
        "title": "Practical Web Application Security and Testing",
        "url": "https://taggartinstitute.org/p/pwst",
        "description": (
            "Entry-level course covering web application technologies, security "
            "considerations for development, and the web penetration testing process. "
            "Progresses from HTTP and server-client basics through the OWASP Top 10 "
            "vulnerabilities, concluding with a complete penetration test demonstration "
            "and reporting guidance. Prepares offensive and defensive security "
            "professionals and developers to understand web application security from "
            "multiple perspectives."
        ),
        "duration": "10 sections, 70+ lectures",
        "level": "Beginner",
        "format": "On-Demand Video with Hands-On Labs",
        "price": "Free (pay-what-you-wish: $5, $10, $15)",
        "category": "Cybersecurity / Web Application Security / Penetration Testing",
        "instructor": "Michael Taggart",
        "prerequisites": "Basic Linux command-line familiarity; 16GB RAM, 50GB storage",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Creating With Git",
        "url": "https://taggartinstitute.org/p/creating-with-git",
        "description": (
            "Teaches essential Git skills for managing projects and publishing "
            "documentation. Students learn to work confidently with version control, "
            "moving beyond fear of merge conflicts to master branching, merging, and "
            "collaboration workflows. Combines technical instruction with practical "
            "project management applications."
        ),
        "duration": "5 sections, 17 lectures",
        "level": "Beginner to Intermediate",
        "format": "On-Demand Video",
        "price": "Free (pay-what-you-wish: $1, $5, $10)",
        "category": "Development / Version Control",
        "instructor": "Michael Taggart",
        "prerequisites": "Linux command line familiarity; Vim knowledge helpful",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Responsible Red Teaming",
        "url": "https://taggartinstitute.org/p/responsible-red-teaming",
        "description": (
            "Addresses the ethical, legal, and tactical dimensions of responsible red "
            "team operations. Emphasizes how to emulate cybercriminals without "
            "introducing the risk of real cyber crime. Explores distinctions between "
            "legality, ethics, responsibility, and OPSEC while developing practical "
            "skills in C2 infrastructure, malware emulation, and payload engineering."
        ),
        "duration": "7 sections + capstone, 50+ lectures",
        "level": "Intermediate to Advanced",
        "format": "Written Lectures and Practical Labs",
        "price": "Free (pay-what-you-wish: $1, $5, $10, $15)",
        "category": "Cybersecurity / Red Teaming / Ethical Hacking",
        "instructor": "Matt Kiely (HuskyHacks)",
        "prerequisites": "Familiarity with red team concepts, C2 frameworks, basic malware development",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Python for Defenders, Pt. 2",
        "url": "https://taggartinstitute.org/p/python-for-defenders-pt2",
        "description": (
            "Teaches data analysis using Python and Jupyter for cybersecurity "
            "applications. Students learn to import, parse, and visualize log events "
            "and telemetry files used in threat detection and response, creating "
            "repeatable processes for team documentation and active defense tooling."
        ),
        "duration": "9 sections, 28+ lectures; ~3-4 hours video",
        "level": "Intermediate",
        "format": "On-Demand Video with Interactive Labs and Jupyter Notebooks",
        "price": "Free (pay-what-you-wish: $1, $5, $10, $15)",
        "category": "Cybersecurity / Python / Data Analysis",
        "instructor": "Michael Taggart",
        "prerequisites": "Python for Defenders, Pt. 1",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Vim For Everyone",
        "url": "https://taggartinstitute.org/p/vim-for-everyone",
        "description": (
            "Teaches mastery of the Vim text editor. While most people simply want to "
            "exit Vim, those who master it gain access to powerful text processing "
            "capabilities valuable across IT workflows including software development "
            "and cybersecurity. Covers modes, navigation, text manipulation, buffers, "
            "registers, regular expressions, and Vim customization."
        ),
        "duration": "5 sections, 16 lectures; ~1-2 hours",
        "level": "Beginner",
        "format": "On-Demand Video",
        "price": "Free (pay-what-you-wish: $1, $5, $10)",
        "category": "Linux / Command Line Tools / Developer Tools",
        "instructor": "Michael Taggart",
        "prerequisites": "Linux command line familiarity; regular expressions helpful",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "The Homelab Almanac: TTI Edition",
        "url": "https://taggartinstitute.org/digital-products/319933",
        "description": (
            "Comprehensive guide for building home laboratory environments. Covers "
            "enterprise network simulation, malware analysis in controlled settings, "
            "and infrastructure automation using open-source tools. Spans hardware "
            "selection, network configuration, virtual machine templating with Packer, "
            "infrastructure-as-code via Terraform, configuration management through "
            "Ansible, and practical deployments including web servers, security labs, "
            "and Windows domains. Version 3.0 with 50+ chapters."
        ),
        "duration": "4 parts, 50+ chapters",
        "level": "Intermediate",
        "format": "Digital Book (DRM-Free EPUB, PDF, Static Website)",
        "price": "$29.99",
        "category": "IT Infrastructure / Homelab / DevOps",
        "instructor": "Michael Taggart",
        "prerequisites": "Basic IT/networking knowledge",
        "date_scraped": DATE_SCRAPED,
    },
]


def export_catalog(courses: list[dict], provider_dir: str) -> dict[str, str]:
    df = pd.DataFrame(courses)

    column_order = [
        "provider", "title", "url", "description", "duration",
        "level", "format", "price", "category", "instructor",
        "prerequisites", "date_scraped",
    ]
    existing_cols = [col for col in column_order if col in df.columns]
    df = df[existing_cols]

    # Quality checks
    avg_title_len = df["title"].str.len().mean()
    long_titles = df[df["title"].str.len() > 150]
    unique_desc_pct = df["description"].nunique() / len(df) * 100
    print(f"\nTitle quality: avg={avg_title_len:.0f} chars, {len(long_titles)} titles >150 chars")
    print(f"Description uniqueness: {unique_desc_pct:.1f}%")

    json_path = os.path.join(provider_dir, "catalog.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)

    xlsx_path = os.path.join(provider_dir, "catalog.xlsx")
    df_ascii = df.copy()
    for col in df_ascii.select_dtypes(include=["object"]).columns:
        df_ascii[col] = df_ascii[col].apply(clean_to_ascii)
    df_ascii.to_excel(xlsx_path, index=False, engine="openpyxl")

    return {"json": json_path, "xlsx": xlsx_path, "avg_title_len": avg_title_len, "desc_uniqueness_pct": unique_desc_pct}


def write_report(courses: list[dict], provider_dir: str, stats: dict) -> str:
    report_path = os.path.join(provider_dir, "report.md")
    total = len(courses)
    desc_complete = sum(1 for c in courses if c.get("description")) / total * 100
    dur_complete = sum(1 for c in courses if c.get("duration")) / total * 100
    level_complete = sum(1 for c in courses if c.get("level")) / total * 100
    price_complete = sum(1 for c in courses if c.get("price")) / total * 100

    samples = "\n".join(
        f"- **{c['title']}** ({c.get('price','')}) - {c.get('level','')} - {c.get('instructor','')}\n"
        f"  {c['url']}\n"
        f"  {c.get('description','')[:120]}..."
        for c in courses[:5]
    )

    report = f"""# The Taggart Institute Catalog Scraping Report

**Date**: {DATE_SCRAPED}
**URL**: {CATALOG_URL}
**Total Courses**: {total}

## Architecture
- Type: Single-Page Application (Next.js App Router with streaming SSR)
- Data Source: Static HTML extraction (page renders skeleton loaders; no __NEXT_DATA__ with course list)
- Obstacles: JavaScript-rendered catalog page (courses not in initial HTML); data gathered via homepage + individual course pages

## Extraction Method
The `/courses` catalog page uses Next.js streaming with skeleton loaders - actual course cards are hydrated client-side and not present in static HTML. Course data was collected by:
1. Fetching the homepage, which displays featured courses with links
2. Visiting each individual course page at `/p/<slug>` to extract full metadata
3. Supplementing with the digital product page for the Homelab Almanac

## Data Quality
- Title: 100% complete (avg length: {stats['avg_title_len']:.0f} chars, 0 titles >150 chars)
- Description: {desc_complete:.0f}% complete ({stats['desc_uniqueness_pct']:.1f}% unique)
- Duration: {dur_complete:.0f}% complete
- Level: {level_complete:.0f}% complete
- Price: {price_complete:.0f}% complete

## Limitations
- The `/courses` page is a Next.js SPA; full course list requires JavaScript execution.
- Only 6 courses/products were discoverable via homepage + direct URL probing. There may be additional courses not featured on the homepage or linked directly.
- Python for Defenders, Pt. 1 is referenced as a prerequisite but its URL could not be discovered (likely `/p/python-for-defenders` 404s).
- No pagination or API endpoint was found to enumerate the complete catalog programmatically.

## Recommendations
- Use a headless browser (Playwright/Selenium) against `/courses` to render the full course grid
- Look for network requests to a backend API (e.g., Teachable API endpoints) when the page loads
- The platform appears to be hosted on Teachable (URL patterns match Teachable conventions)

## Sample Courses
{samples}

## Catalog Overview
- **Free courses**: 5 (pay-what-you-wish model, max $15)
- **Paid**: 1 ($29.99 digital book)
- **Categories**: Cybersecurity (web security, red teaming, Python defense), Developer Tools (Vim, Git), IT Infrastructure
- **Instructors**: Michael Taggart (primary), Matt Kiely/HuskyHacks (guest)
- **Formats**: On-demand video, written lectures, digital book
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    return report_path


def update_registry(provider_data: dict) -> None:
    registry_path = "/Users/bianders/.claude/skills/catalog-scraper/catalog_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

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
    print("Updated catalog_registry.json")


def regenerate_master_catalog() -> None:
    registry_path = "/Users/bianders/.claude/skills/catalog-scraper/catalog_registry.json"
    master_json = "/Users/bianders/.claude/skills/catalog-scraper/master_catalog.json"
    master_xlsx = "/Users/bianders/.claude/skills/catalog-scraper/master_catalog.xlsx"

    with open(registry_path, "r") as f:
        registry = json.load(f)

    all_courses: list[dict] = []
    for pinfo in registry["providers"].values():
        json_file = pinfo.get("files", {}).get("json", "")
        if json_file and os.path.exists(json_file):
            with open(json_file, "r") as f:
                all_courses.extend(json.load(f))

    with open(master_json, "w", encoding="utf-8") as f:
        json.dump(all_courses, f, indent=2, ensure_ascii=False)

    if all_courses:
        df = pd.DataFrame(all_courses)
        df.to_excel(master_xlsx, index=False, engine="openpyxl")

    print(f"Regenerated master catalog ({len(all_courses)} total courses)")


def main() -> None:
    provider_dir = f"/Users/bianders/.claude/skills/catalog-scraper/providers/{PROVIDER_SLUG}"
    os.makedirs(provider_dir, exist_ok=True)

    print(f"Scraping {PROVIDER_NAME}...")
    courses = COURSES_RAW
    print(f"Collected {len(courses)} courses")

    stats = export_catalog(courses, provider_dir)
    report_path = write_report(courses, provider_dir, stats)

    print(f"JSON: {stats['json']}")
    print(f"XLSX: {stats['xlsx']}")
    print(f"Report: {report_path}")

    provider_data = {
        "status": "partial",
        "url": CATALOG_URL,
        "courses_count": len(courses),
        "date_scraped": DATE_SCRAPED,
        "scraper_version": "1.0",
        "data_quality": {
            "has_descriptions": True,
            "has_duration": True,
            "has_level": True,
            "avg_title_length": int(stats["avg_title_len"]),
        },
        "files": {
            "json": stats["json"],
            "xlsx": stats["xlsx"],
            "report": report_path,
        },
        "limitation": (
            "Next.js SPA with skeleton loaders; full course list requires JavaScript execution. "
            "6 courses found via homepage + individual page fetching. More courses may exist."
        ),
        "notes": "Teachable-hosted platform; pay-what-you-wish model (max $15 for most courses)",
    }

    update_registry(provider_data)
    regenerate_master_catalog()

    # Write result.json for batch dispatch
    result_path = "/Users/bianders/.claude/skills/batch-dispatch/batch_runs/20260217_130022/task_3/result.json"
    result = {
        "provider": PROVIDER_NAME,
        "url": CATALOG_URL,
        "status": "partial",
        "courses_count": len(courses),
        "date_scraped": DATE_SCRAPED,
        "limitation": provider_data["limitation"],
        "files": provider_data["files"],
        "courses": courses,
    }
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nSaved result.json to {result_path}")


if __name__ == "__main__":
    main()
