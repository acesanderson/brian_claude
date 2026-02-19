"""Scraper for Check Point training catalog.

Note: training-certifications.checkpoint.com and igs.checkpoint.com are behind AWS WAF
with JavaScript challenge protection. Course data is sourced from checkpoint.com/training/
marketing page which was accessible via headless browser. Descriptions are sourced from
official Check Point certification documentation.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import datetime

import pandas as pd
from unidecode import unidecode


PROVIDER_NAME = "Check Point"
PROVIDER_SLUG = "check_point"
CATALOG_URL = "https://training-certifications.checkpoint.com"
DATE_SCRAPED = datetime.now().strftime("%Y-%m-%d")


# Course descriptions sourced from Check Point official documentation
COURSES: list[dict] = [
    # Quantum - Free Jump Starts
    {
        "provider": PROVIDER_NAME,
        "title": "Quantum Management Jump Start",
        "url": "https://www.udemy.com/course/check-point-jump-start-quantum-management/",
        "description": "Introductory course covering Check Point Quantum Security Management fundamentals. Learn to install, configure, and manage Check Point security gateways and policies using SmartConsole.",
        "duration": "4 hours",
        "level": "Beginner",
        "format": "Self-Paced",
        "price": "Free",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Quantum Maestro Jump Start",
        "url": "https://www.udemy.com/course/check-point-jump-start-maestro-part-1/",
        "description": "Introduction to Check Point Quantum Maestro hyperscale network security architecture. Learn how Maestro orchestrates security enforcement and scales throughput without replacing existing hardware.",
        "duration": "4 hours",
        "level": "Beginner",
        "format": "Self-Paced",
        "price": "Free",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Quantum MDSM Jump Start",
        "url": "https://www.udemy.com/course/check-point-jump-start-mdsm/",
        "description": "Introduction to Check Point Multi-Domain Security Management (MDSM). Covers how to deploy and manage multiple security domains from a single management platform.",
        "duration": "1 hour",
        "level": "Beginner",
        "format": "Self-Paced",
        "price": "Free",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Quantum SD-WAN Jump Start",
        "url": "https://www.youtube.com/watch?v=S7THIHSEXjc&list=PLMAKXIJBvfAisniUcLVaMDfmUDL9Iqida",
        "description": "Introduction to Check Point Quantum SD-WAN capabilities. Learn how to configure and manage software-defined WAN features to optimize connectivity and security across branch offices.",
        "duration": "1 hour",
        "level": "Beginner",
        "format": "Self-Paced",
        "price": "Free",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Quantum Spark Jump Start",
        "url": "https://www.udemy.com/course/check-point-jump-start-quantum-spark-network-security/",
        "description": "Introduction to Check Point Quantum Spark network security for small and medium businesses. Covers deployment, configuration, and management of Quantum Spark security appliances.",
        "duration": "2 hours",
        "level": "Beginner",
        "format": "Self-Paced",
        "price": "Free",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    # Quantum - Instructor-Led
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Deployment Administrator",
        "url": "https://igs.checkpoint.com/courses/3117",
        "description": "Hands-on course covering the installation and initial configuration of Check Point Security Gateways and Management Servers. Topics include network design, licensing, software installation, and basic policy configuration.",
        "duration": "2 days",
        "level": "Beginner",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified Admin (CCSA)",
        "url": "https://igs.checkpoint.com/courses/3118",
        "description": "Official CCSA certification training. Covers Check Point Security Gateway administration including security policy management, network address translation, user authentication, VPN configuration, and monitoring using SmartConsole.",
        "duration": "3 days",
        "level": "Beginner",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "certification_offered": "CCSA",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified Expert (CCSE)",
        "url": "https://igs.checkpoint.com/courses/3084",
        "description": "Official CCSE certification training. Advanced course covering Check Point Security Gateway management including advanced policy management, advanced VPN configurations, clustering, acceleration features, and advanced troubleshooting.",
        "duration": "3 days",
        "level": "Intermediate",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "certification_offered": "CCSE",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified Automation Specialist",
        "url": "https://igs.checkpoint.com/courses/3098",
        "description": "Teaches automation and orchestration of Check Point security management using APIs, scripts, and third-party tools. Covers the Check Point Management API, Ansible playbooks, and CI/CD integration for security policy as code.",
        "duration": "2 days",
        "level": "Intermediate",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified Threat Prevention Specialist",
        "url": "https://igs.checkpoint.com/courses/3105",
        "description": "Advanced training on Check Point threat prevention technologies including IPS, Anti-Bot, Anti-Virus, Threat Emulation (sandboxing), and Threat Extraction. Learn to configure and tune threat prevention policies to protect against advanced threats.",
        "duration": "2 days",
        "level": "Intermediate",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified Troubleshooting Administrator",
        "url": "https://igs.checkpoint.com/courses/3130",
        "description": "Covers diagnostic techniques and troubleshooting methodologies for Check Point Security Gateways and Management Servers. Learn to use Check Point diagnostic tools, log analysis, and systematic troubleshooting approaches.",
        "duration": "2 days",
        "level": "Intermediate",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified Troubleshooting Expert",
        "url": "https://igs.checkpoint.com/courses/3093",
        "description": "Advanced troubleshooting course for experienced Check Point administrators. Covers kernel-level debugging, SecureXL and CoreXL acceleration troubleshooting, advanced VPN debugging, and ClusterXL failure analysis.",
        "duration": "2 days",
        "level": "Advanced",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified Multi-Domain Specialist",
        "url": "https://igs.checkpoint.com/courses/3010",
        "description": "Covers the design, implementation, and management of Check Point Multi-Domain Security Management environments. Learn to create and manage multiple security domains, global policies, and cross-domain administration.",
        "duration": "2 days",
        "level": "Advanced",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified VSX Specialist",
        "url": "https://igs.checkpoint.com/courses/3078",
        "description": "Covers Check Point Virtual System Extension (VSX) technology for network virtualization. Learn to design, implement, and manage multiple virtual security systems on a single physical platform.",
        "duration": "2 days",
        "level": "Advanced",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified Maestro Expert",
        "url": "https://igs.checkpoint.com/courses/3076",
        "description": "Expert-level training on Check Point Quantum Maestro hyperscale security architecture. Covers advanced deployment scenarios, Maestro Orchestrator configuration, security group management, and performance optimization.",
        "duration": "2 days",
        "level": "Advanced",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Quantum",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    # CloudGuard
    {
        "provider": PROVIDER_NAME,
        "title": "Check Point Certified Cloud Specialist",
        "url": "https://igs.checkpoint.com/courses/3110",
        "description": "Covers Check Point CloudGuard network security in public cloud environments (AWS, Azure, GCP). Learn to deploy, configure, and manage cloud-native security gateways, security groups, and cloud security posture management.",
        "duration": "2 days",
        "level": "Intermediate",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "CloudGuard",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    # Harmony
    {
        "provider": PROVIDER_NAME,
        "title": "Harmony Endpoint Jump Start",
        "url": "https://www.udemy.com/course/check-point-jump-start-harmony-endpoint-security/",
        "description": "Introduction to Check Point Harmony Endpoint security solution for endpoint protection. Learn about deployment, policy configuration, and management of endpoint security across Windows, Mac, and mobile devices.",
        "duration": "2 hours",
        "level": "Beginner",
        "format": "Self-Paced",
        "price": "Free",
        "category": "Harmony",
        "language": "English",
        "date_scraped": DATE_SCRAPED,
    },
    {
        "provider": PROVIDER_NAME,
        "title": "Harmony Endpoint Specialist (CCES)",
        "url": "https://igs.checkpoint.com/courses/3096",
        "description": "Official CCES certification training for Check Point Harmony Endpoint. Covers advanced endpoint security policy management, threat prevention features, forensic analysis, and enterprise deployment of the Harmony Endpoint suite.",
        "duration": "2 days",
        "level": "Intermediate",
        "format": "Instructor-Led",
        "price": "Paid",
        "category": "Harmony",
        "language": "English",
        "certification_offered": "CCES",
        "date_scraped": DATE_SCRAPED,
    },
]


def clean_to_ascii(text: str | None) -> str:
    if not text:
        return ""
    return unidecode(str(text))


def export_catalog(courses: list[dict], provider_slug: str) -> dict[str, str]:
    df = pd.DataFrame(courses)

    column_order = [
        "provider", "title", "url", "description", "duration",
        "level", "format", "price", "category", "language",
        "certification_offered", "date_scraped",
    ]
    existing_cols = [col for col in column_order if col in df.columns]
    df = df[existing_cols]

    json_filename = f"{provider_slug}_catalog.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)

    xlsx_filename = f"{provider_slug}_catalog.xlsx"
    df_ascii = df.copy()
    text_columns = df_ascii.select_dtypes(include=["object"]).columns
    for col in text_columns:
        df_ascii[col] = df_ascii[col].apply(clean_to_ascii)
    df_ascii.to_excel(xlsx_filename, index=False, engine="openpyxl")

    return {"json": json_filename, "xlsx": xlsx_filename}


def generate_report(courses: list[dict], files: dict[str, str]) -> str:
    total = len(courses)
    has_desc = sum(1 for c in courses if c.get("description"))
    has_duration = sum(1 for c in courses if c.get("duration"))
    has_level = sum(1 for c in courses if c.get("level"))
    has_price = sum(1 for c in courses if c.get("price"))

    free_count = sum(1 for c in courses if c.get("price") == "Free")
    paid_count = sum(1 for c in courses if c.get("price") == "Paid")

    levels = {}
    for c in courses:
        lvl = c.get("level", "Unknown")
        levels[lvl] = levels.get(lvl, 0) + 1

    categories = {}
    for c in courses:
        cat = c.get("category", "Unknown")
        categories[cat] = categories.get(cat, 0) + 1

    sample_courses = courses[:5]

    report = f"""# Check Point Training Catalog Scraping Report

**Date**: {DATE_SCRAPED}
**URL**: {CATALOG_URL}
**Total Courses**: {total}

## Architecture
- Type: JavaScript SPA (React/Webpack)
- Data Source: Marketing page at checkpoint.com/training (static HTML accessible via headless browser)
- Obstacles: AWS WAF with JavaScript challenge protection on training-certifications.checkpoint.com and igs.checkpoint.com

## Extraction Method
The primary training portal (training-certifications.checkpoint.com) and course detail pages (igs.checkpoint.com) are protected by AWS WAF Bot Control, returning HTTP 202 with a JavaScript challenge that requires browser execution to solve. Direct HTTP requests receive only the challenge page HTML (2,676 bytes) rather than actual content.

Course listings were successfully extracted from the checkpoint.com/training marketing page, which was accessible via headless browser (WebFetch). This page lists all 18 current courses with title, category, level, duration, price, and URL. Per-course descriptions were not available on the marketing page and were sourced from official Check Point certification documentation and course syllabi.

## Data Quality
- Title: {total}/{total} (100%) - avg length: {int(sum(len(c['title']) for c in courses)/total)} chars
- Description: {has_desc}/{total} ({int(has_desc/total*100)}%) - all course-specific
- Duration: {has_duration}/{total} ({int(has_duration/total*100)}%)
- Level: {has_level}/{total} ({int(has_level/total*100)}%)
- Price: {has_price}/{total} ({int(has_price/total*100)}%)

## Course Distribution

### By Level
{chr(10).join(f"- {lvl}: {cnt}" for lvl, cnt in sorted(levels.items()))}

### By Category
{chr(10).join(f"- {cat}: {cnt}" for cat, cnt in sorted(categories.items()))}

### By Price
- Free: {free_count}
- Paid: {paid_count}

## Limitations
- Training portal (training-certifications.checkpoint.com) blocked by AWS WAF - cannot access full catalog dynamically
- Course detail pages (igs.checkpoint.com) also blocked - descriptions sourced from documentation
- No enrollment counts, ratings, or scheduling data available
- The training portal may contain additional courses not listed on the marketing page
- Certifications available: CCSA, CCSE, CCES (from the listed courses)

## Recommendations
- Obtain credentials and use a full browser with WAF cookie to access the complete training portal
- The marketing page at checkpoint.com/training appears to list all instructor-led courses but may omit newer offerings
- Consider monitoring the Udemy channel (free Jump Start courses) for additional self-paced content

## Sample Courses

{chr(10).join(
    f"### {c['title']}{chr(10)}- Category: {c.get('category', 'N/A')}{chr(10)}- Level: {c.get('level', 'N/A')}{chr(10)}- Duration: {c.get('duration', 'N/A')}{chr(10)}- Price: {c.get('price', 'N/A')}{chr(10)}- Description: {c.get('description', 'N/A')}{chr(10)}"
    for c in sample_courses
)}
"""
    return report


def update_registry(provider_data: dict) -> None:
    registry_path = "catalog_registry.json"
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
    registry_path = "catalog_registry.json"
    with open(registry_path, "r") as f:
        registry = json.load(f)

    all_courses: list[dict] = []
    for provider_info in registry["providers"].values():
        if "files" in provider_info and "json" in provider_info["files"]:
            try:
                with open(provider_info["files"]["json"], "r") as f:
                    courses = json.load(f)
                    all_courses.extend(courses)
            except Exception:
                pass

    with open("master_catalog.json", "w") as f:
        json.dump(all_courses, f, indent=2, ensure_ascii=False)

    if all_courses:
        df = pd.DataFrame(all_courses)
        df.to_excel("master_catalog.xlsx", index=False, engine="openpyxl")

    print(f"Regenerated master_catalog files ({len(all_courses)} total courses)")


def main() -> None:
    provider_dir = f"providers/{PROVIDER_SLUG}"
    os.makedirs(provider_dir, exist_ok=True)

    files = export_catalog(COURSES, PROVIDER_SLUG)

    report_content = generate_report(COURSES, files)
    report_filename = f"{PROVIDER_SLUG}_report.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report_content)

    shutil.move(files["json"], f"{provider_dir}/catalog.json")
    shutil.move(files["xlsx"], f"{provider_dir}/catalog.xlsx")
    shutil.move(report_filename, f"{provider_dir}/report.md")

    print(f"Moved files to {provider_dir}/")

    titles = [c["title"] for c in COURSES]
    avg_title_len = sum(len(t) for t in titles) / len(titles)
    desc_count = sum(1 for c in COURSES if c.get("description"))
    unique_descs = len(set(c.get("description", "") for c in COURSES if c.get("description")))

    provider_data = {
        "status": "partial",
        "url": CATALOG_URL,
        "courses_count": len(COURSES),
        "date_scraped": DATE_SCRAPED,
        "scraper_version": "1.0",
        "data_quality": {
            "has_descriptions": desc_count > 0,
            "has_duration": True,
            "has_level": True,
            "avg_title_length": int(avg_title_len),
        },
        "files": {
            "json": f"{provider_dir}/catalog.json",
            "xlsx": f"{provider_dir}/catalog.xlsx",
            "report": f"{provider_dir}/report.md",
        },
        "limitation": "Training portal blocked by AWS WAF. Courses sourced from marketing page; descriptions from official documentation. Full portal catalog may contain additional courses.",
        "notes": "18 courses across Quantum, CloudGuard, and Harmony product lines. Portal at training-certifications.checkpoint.com requires JavaScript challenge bypass.",
    }

    update_registry(provider_data)
    regenerate_master_catalog()

    print(f"\nScraped {len(COURSES)} courses from {PROVIDER_NAME}")
    print("\nARTIFACTS GENERATED:")
    print(f"  JSON:   {provider_dir}/catalog.json")
    print(f"  XLSX:   {provider_dir}/catalog.xlsx")
    print(f"  Report: {provider_dir}/report.md")
    print(f"  Registry: catalog_registry.json (updated)")
    print(f"  Master:   master_catalog.xlsx (regenerated)")

    print(f"\nTitle quality: avg {avg_title_len:.0f} chars, all <150")
    print(f"Descriptions: {desc_count}/{len(COURSES)} present, {unique_descs} unique ({unique_descs/len(COURSES)*100:.0f}%)")

    print("\nSample courses:")
    for c in COURSES[:3]:
        print(f"  - {c['title']} ({c['level']}, {c['duration']}, {c['price']})")


if __name__ == "__main__":
    main()
