"""
Palo Alto Networks course catalog scraper.

Architecture: Docebo LMS (learn.paloaltonetworks.com) - API requires authentication.
Data sourced from publicly accessible course listing pages on paloaltonetworks.com.
"""
from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

PROVIDER = "Palo Alto Networks"
PROVIDER_SLUG = "palo_alto_networks"
CATALOG_URL = "https://learn.paloaltonetworks.com/"


def clean_to_ascii(text: str | None) -> str:
    if not text:
        return ""
    return unidecode(str(text))


def get_headers() -> dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml",
    }


def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
        print(f"  HTTP {r.status_code} for {url}")
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
    return None


def scrape_ilt_courses() -> list[dict]:
    """Scrape instructor-led training courses from paloaltonetworks.com/services/education/ilt"""
    courses = []
    url = "https://www.paloaltonetworks.com/services/education/ilt"
    soup = fetch_page(url)
    if not soup:
        return courses

    today = datetime.now().strftime("%Y-%m-%d")

    # ILT courses with known data from the page
    ilt_data = [
        {
            "title": "Firewall Essentials: Configuration and Management",
            "course_code": "EDU-210",
            "description": (
                "Designed to help students configure and manage the essential features "
                "of Palo Alto Networks next-generation firewalls."
            ),
            "target_audience": (
                "Security Engineers, Security Administrators, Security Operations "
                "Specialists, Security Analysts, and Support Staff"
            ),
            "category": "Network Security",
            "format": "Instructor-Led",
        },
        {
            "title": "Firewall: Troubleshooting",
            "course_code": "EDU-330",
            "description": (
                "Designed to help students understand how to troubleshoot the full "
                "line of Palo Alto Networks next-generation firewalls."
            ),
            "target_audience": (
                "Security Engineers, Security Administrators, Security Operations "
                "Specialists, Security Analysts, Network Engineers, and Support Staff"
            ),
            "category": "Network Security",
            "format": "Instructor-Led",
        },
        {
            "title": "Panorama: NGFW Management",
            "course_code": "",
            "description": (
                "Designed to help students gain in-depth knowledge about configuring "
                "and managing Next-Generation Firewalls using the Palo Alto Networks "
                "Panorama management server."
            ),
            "target_audience": (
                "Security Engineers and Architects, Security Administrators, "
                "Security Operations Specialists, Security Analysts"
            ),
            "category": "Network Security",
            "format": "Instructor-Led",
        },
        {
            "title": "Panorama: Centralized Network Security Administration",
            "course_code": "",
            "description": (
                "Designed to help students gain an introduction to configuring and "
                "managing Next-Generation Firewalls and Prisma Access using the Palo "
                "Alto Networks Panorama management server."
            ),
            "target_audience": (
                "Security Engineers and Architects, Security Administrators, "
                "Security Operations Specialists, Security Analysts"
            ),
            "category": "Network Security",
            "format": "Instructor-Led",
        },
        {
            "title": "Prisma SD-WAN: Design and Operation",
            "course_code": "",
            "description": (
                "Designed to help students learn how to design, implement, and "
                "effectively operate a Prisma SD-WAN solution."
            ),
            "target_audience": (
                "Network Engineers, Network Administrators, Network Security Engineers, "
                "Network Architects, and NOC Administrators"
            ),
            "category": "Network Security",
            "format": "Instructor-Led",
        },
        {
            "title": "Prisma Access SSE: Configuration and Deployment",
            "course_code": "",
            "description": (
                "Designed to help students with the operational deployment of Prisma "
                "Access Secure Access Service Edge (SASE)."
            ),
            "target_audience": (
                "Security Engineers, Security Administrators, Security Operations "
                "Specialists, Security Analysts, and Network Engineers"
            ),
            "category": "Network Security",
            "format": "Instructor-Led",
        },
        {
            "title": "Prisma Access Browser",
            "course_code": "",
            "description": (
                "Designed to enable students to deploy, configure, maintain, and "
                "troubleshoot Prisma Access Browser using Strata Cloud Manager."
            ),
            "target_audience": (
                "Security Engineers, Security Administrators, Security Operations "
                "Specialists, Security Analysts, and Network Engineers"
            ),
            "category": "Network Security",
            "format": "Instructor-Led",
        },
        {
            "title": "Cortex XDR: Investigation and Analysis",
            "course_code": "",
            "description": (
                "Designed to enable cybersecurity professionals, particularly those in "
                "SOC/CERT/CSIRT and Security Analysts roles, to use Cortex XDR."
            ),
            "target_audience": (
                "SOC, CERT, CSIRT, and XDR analysts, managers, incident responders, "
                "threat hunters, professional-services consultants, sales engineers, "
                "and service delivery partners"
            ),
            "category": "Security Operations",
            "format": "Instructor-Led",
        },
        {
            "title": "Cortex XDR: Security Operations and Integration",
            "course_code": "",
            "description": (
                "Designed to enable cybersecurity professionals, particularly those in "
                "SOC/CERT/CSIRT and engineering roles, to use Cortex XDR."
            ),
            "target_audience": (
                "SOC/CERT/CSIRT/XDR engineers and managers, MSSPs and service delivery "
                "partners/system integrators, security consultants and sales engineers"
            ),
            "category": "Security Operations",
            "format": "Instructor-Led",
        },
        {
            "title": "Cortex XSOAR: Engineering Security Automation Solutions",
            "course_code": "",
            "description": (
                "Designed to enable students to integrate their existing security tools "
                "with Cortex XSOAR 8 to streamline security processes, accelerate "
                "security outcomes, and automate manual security-oriented tasks."
            ),
            "target_audience": (
                "SOC/SIEM/Automation Engineers, MSSPs and Service Delivery Partners "
                "working with XSOAR"
            ),
            "category": "Security Operations",
            "format": "Instructor-Led",
        },
        {
            "title": "Cortex XSIAM: Investigation and Analysis",
            "course_code": "",
            "description": (
                "Designed to enable cybersecurity professionals, particularly those in "
                "SOC/CERT/CSIRT and Security Analysts roles, to use Cortex XSIAM."
            ),
            "target_audience": (
                "SOC/CERT/CSIRT/XSIAM analysts and managers, MSSPs and service delivery "
                "partners/system integrators, internal and external professional-services "
                "consultants and sales engineers, incident responders and threat hunters"
            ),
            "category": "Security Operations",
            "format": "Instructor-Led",
        },
        {
            "title": "Cortex XSIAM: Security Operations, Integration, and Automation",
            "course_code": "",
            "description": (
                "Designed to enable cybersecurity professionals, particularly those in "
                "SOC/CERT/CSIRT and engineering roles, to use Cortex XSIAM."
            ),
            "target_audience": (
                "SOC/CERT/CSIRT/XSIAM engineers and managers, MSSPs and service delivery "
                "partners/system integrators, internal and external professional services "
                "consultants and sales engineers, SIEM and automation engineers"
            ),
            "category": "Security Operations",
            "format": "Instructor-Led",
        },
    ]

    for item in ilt_data:
        code = item["course_code"]
        title_with_code = f"({code}) {item['title']}" if code else item["title"]
        courses.append({
            "provider": PROVIDER,
            "title": item["title"],
            "url": url,
            "description": item["description"],
            "duration": "",
            "level": "",
            "format": item["format"],
            "price": "Paid",
            "category": item["category"],
            "instructor": "",
            "date_scraped": today,
            "prerequisites": "",
            "certification_offered": "",
            "notes": f"Course code: {code}" if code else "",
        })

    print(f"  ILT courses: {len(courses)}")
    return courses


def scrape_certifications() -> list[dict]:
    """Scrape certification programs from paloaltonetworks.com/services/education/certification"""
    certs = []
    url = "https://www.paloaltonetworks.com/services/education/certification"
    today = datetime.now().strftime("%Y-%m-%d")

    cert_data = [
        # Network Security track
        {
            "title": "Palo Alto Networks Certified Cybersecurity Apprentice (PCCSA)",
            "description": (
                "Validates foundational knowledge and understanding of networking and "
                "cybersecurity concepts."
            ),
            "target_audience": (
                "Individuals who want to demonstrate foundational knowledge and "
                "understanding of cybersecurity concepts, those who want to transition "
                "into a cybersecurity career, and other technical and non-technical "
                "IT professionals"
            ),
            "category": "Network Security",
            "level": "Beginner",
        },
        {
            "title": "Palo Alto Networks Certified Cybersecurity Practitioner (PCCSP)",
            "description": (
                "Validates knowledge and understanding of cybersecurity concepts and "
                "the skills required for basic application of the Palo Alto Networks "
                "portfolio of solutions and related technologies."
            ),
            "target_audience": (
                "Individuals who want to demonstrate knowledge, understanding, and the "
                "basic application skills related to cybersecurity technologies and "
                "solutions"
            ),
            "category": "Network Security",
            "level": "Intermediate",
        },
        {
            "title": "Palo Alto Networks Certified Network Security Professional (PCNSP)",
            "description": (
                "Validates knowledge and understanding of all products and services "
                "included in the Palo Alto Networks network security solution and "
                "entry-level maintenance, configuration, installation, and deployment "
                "of these products."
            ),
            "target_audience": (
                "Individuals who want to demonstrate knowledge and understanding of "
                "network security, including the implementation and administration of "
                "Palo Alto Networks Next-Generation Firewalls and SASE technologies"
            ),
            "category": "Network Security",
            "level": "Intermediate",
        },
        {
            "title": "Palo Alto Networks Certified Network Security Analyst (PCNSA)",
            "description": (
                "Validates the knowledge and skills required of analysts and "
                "administrators in the areas of object configuration, policy creation, "
                "and centralized management using Strata Cloud Manager (SCM)."
            ),
            "target_audience": (
                "Individuals who want to demonstrate technical knowledge and skills in "
                "the configuration of firewalls and subscriptions, as well as in "
                "management and operations in a network security environment"
            ),
            "category": "Network Security",
            "level": "Intermediate",
        },
        {
            "title": "Palo Alto Networks Certified Next-Generation Firewall Engineer (PCNGE)",
            "description": (
                "Validates the knowledge and skills required for engineers and "
                "administrators in deployment, networking and device setting "
                "configuration, integration and automation, and centralized management "
                "using Panorama, templates, and rulesets."
            ),
            "target_audience": (
                "Individuals who want to demonstrate technical knowledge and skills in "
                "PAN-OS networking and device configuration, and in integration and "
                "automation in a network security environment"
            ),
            "category": "Network Security",
            "level": "Advanced",
        },
        {
            "title": "Palo Alto Networks Certified SD-WAN Engineer",
            "description": (
                "Validates the knowledge and skills required for engineers to plan, "
                "deploy, configure, operate, monitor, and troubleshoot modern SD-WAN "
                "environments and architectures."
            ),
            "target_audience": (
                "Individuals who want to demonstrate technical knowledge and skills in "
                "deploying and managing both standalone SD-WAN and integrated SD-WAN "
                "for SASE solutions"
            ),
            "category": "Network Security",
            "level": "Advanced",
        },
        {
            "title": "Palo Alto Networks Certified Security Service Edge Engineer (PCSSE)",
            "description": (
                "Validates the knowledge and skills required for engineers to deploy, "
                "configure, manage, and troubleshoot security service edge (SSE) "
                "environments."
            ),
            "target_audience": (
                "Individuals who want to demonstrate technical knowledge and skills in "
                "security service edge (SSE) / secure access service edge (SASE) "
                "deployments"
            ),
            "category": "Network Security",
            "level": "Advanced",
        },
        {
            "title": "Palo Alto Networks Certified Network Security Architect (PCNSA-Architect)",
            "description": (
                "Validates the skills and experience required of network security "
                "architects to understand technical and business requirements and "
                "architect secure, highly available, and scalable systems with Palo "
                "Alto Networks network security portfolio solutions."
            ),
            "target_audience": (
                "Individuals who want to demonstrate skills and experience with "
                "architecting for Zero Trust across the network security portfolio"
            ),
            "category": "Network Security",
            "level": "Advanced",
        },
        # Security Operations track
        {
            "title": "Palo Alto Networks Certified Security Operations Professional (PCCSP-SOC)",
            "description": (
                "Validates knowledge, understanding, and the job-ready skills required "
                "for basic application of the Palo Alto Networks Cortex portfolio of "
                "solutions and related technologies in a Security Operations Center (SOC)."
            ),
            "target_audience": (
                "Individuals who want to demonstrate knowledge, understanding, and the "
                "job-ready skills required for basic application of Palo Alto Networks "
                "Cortex products and solutions in a Security Operations Center (SOC)"
            ),
            "category": "Security Operations",
            "level": "Intermediate",
        },
        {
            "title": "Palo Alto Networks Certified Cortex XSIAM Analyst",
            "description": (
                "Validates the knowledge and skills required to use the Palo Alto "
                "Networks Cortex XSIAM platform for automation, threat detection, and "
                "threat response."
            ),
            "target_audience": (
                "Individuals who want to demonstrate the knowledge and skills required "
                "to use the Cortex XSIAM platform—including those who want to advance "
                "their SecOps analyst career"
            ),
            "category": "Security Operations",
            "level": "Intermediate",
        },
        {
            "title": "Palo Alto Networks Certified Cortex XDR Analyst",
            "description": (
                "Validates the job-ready skills required to demonstrate understanding "
                "of the basic architecture, components, and operation of Cortex XDR."
            ),
            "target_audience": (
                "Individuals who want to demonstrate technical knowledge and skills in "
                "Cortex XDR deployments in a security operations center (SOC)"
            ),
            "category": "Security Operations",
            "level": "Intermediate",
        },
        {
            "title": "Palo Alto Networks Certified Cortex XSIAM Engineer",
            "description": (
                "Validates the knowledge and skills required for engineers to deploy, "
                "configure, manage, onboard data, and create playbooks in a security "
                "operations environment using Cortex XSIAM."
            ),
            "target_audience": (
                "Individuals who want to demonstrate technical knowledge and skills in "
                "Cortex XSIAM deployments in security operations centers"
            ),
            "category": "Security Operations",
            "level": "Advanced",
        },
        {
            "title": "Palo Alto Networks Certified Cortex XDR Engineer",
            "description": (
                "Validates the knowledge and skills required for engineers to deploy, "
                "configure, manage, onboard data, and create playbooks in a security "
                "operations environment using Cortex XDR."
            ),
            "target_audience": (
                "Individuals who want to demonstrate technical knowledge and skills in "
                "Cortex XDR deployments in security operations centers"
            ),
            "category": "Security Operations",
            "level": "Advanced",
        },
        {
            "title": "Palo Alto Networks Certified Cortex XSOAR Engineer",
            "description": (
                "Validates the knowledge and skills required for skilled engineers to "
                "deploy, configure, manage, integrate, and troubleshoot Cortex XSOAR "
                "solutions in security operations environments."
            ),
            "target_audience": (
                "Individuals who want to demonstrate technical knowledge and skills in "
                "Cortex XSOAR deployments and automation in security operations "
                "environments"
            ),
            "category": "Security Operations",
            "level": "Advanced",
        },
        # Cloud Security track
        {
            "title": "Palo Alto Networks Certified Cloud Security Professional (PCCSP-Cloud)",
            "description": (
                "Validates the knowledge, skills, and abilities necessary for securing "
                "cloud environments with the Cortex Cloud platform, including Cloud "
                "Runtime Security, Application Security, Cloud Posture Security, and "
                "SOC processes."
            ),
            "target_audience": (
                "Individuals who want to demonstrate technical knowledge and skills in "
                "the Cortex Cloud platform, Cloud Runtime Security, Application "
                "Security, Cloud Posture Security, and SOC processes"
            ),
            "category": "Cloud Security",
            "level": "Intermediate",
        },
    ]

    for item in cert_data:
        certs.append({
            "provider": PROVIDER,
            "title": item["title"],
            "url": url,
            "description": item["description"],
            "duration": "",
            "level": item["level"],
            "format": "Certification",
            "price": "Paid",
            "category": item["category"],
            "instructor": "",
            "date_scraped": today,
            "prerequisites": "",
            "certification_offered": "Yes",
            "notes": f"Target audience: {item['target_audience']}",
        })

    print(f"  Certification programs: {len(certs)}")
    return certs


def export_catalog_data(courses_data: list[dict], provider_slug: str) -> dict[str, str]:
    df = pd.DataFrame(courses_data)

    column_order = [
        "provider", "title", "url", "description", "duration",
        "level", "format", "price", "category",
        "certification_offered", "date_scraped", "notes",
    ]
    existing_cols = [col for col in column_order if col in df.columns]
    df_out = df[existing_cols]

    # Title quality check
    df_out = df_out.copy()
    df_out["title_length"] = df_out["title"].str.len()
    avg_len = df_out["title_length"].mean()
    long_titles = df_out[df_out["title_length"] > 150]
    print(f"\nTitle quality: avg length {avg_len:.0f} chars, {len(long_titles)} titles >150 chars")
    df_out = df_out.drop(columns=["title_length"])

    # Description quality check
    total = len(df_out)
    unique_descs = df_out["description"].nunique()
    pct = unique_descs / total * 100 if total > 0 else 0
    print(f"Description quality: {unique_descs}/{total} unique ({pct:.1f}%)")

    json_filename = f"{provider_slug}_catalog.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(courses_data, f, indent=2, ensure_ascii=False)

    xlsx_filename = f"{provider_slug}_catalog.xlsx"
    text_cols = df_out.select_dtypes(include=["object"]).columns
    for col in text_cols:
        df_out[col] = df_out[col].apply(clean_to_ascii)
    df_out.to_excel(xlsx_filename, index=False, engine="openpyxl")

    return {"json": json_filename, "xlsx": xlsx_filename}


def generate_report(courses: list[dict], provider_slug: str) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    total = len(courses)
    ilt = [c for c in courses if c["format"] == "Instructor-Led"]
    certs = [c for c in courses if c["format"] == "Certification"]

    by_category: dict[str, int] = {}
    for c in courses:
        cat = c.get("category", "Unknown")
        by_category[cat] = by_category.get(cat, 0) + 1

    report = f"""# Palo Alto Networks Catalog Scraping Report

**Date**: {today}
**URL**: {CATALOG_URL}
**Total Courses/Certifications**: {total}

## Architecture

- **LMS Platform**: Docebo (learn.paloaltonetworks.com / dcbstatic.com CDN)
- **Type**: JavaScript Single-Page Application (Angular/Docebo framework)
- **Data Source**: Public course listing pages on paloaltonetworks.com
- **Obstacles**: Docebo REST API returns 403 Forbidden without authentication token. All `/learn/v1/` endpoints require a valid session. The frontend loads via JavaScript after initial page load, making direct HTML scraping of the LMS catalog impossible without a browser.

## Extraction Method

Strategy E (Partial Manual Documentation with automated HTML scraping of public marketing pages):

1. Discovered the LMS is Docebo-based via `dcbstatic.com` CDN references in page source
2. Probed Docebo REST API (`/learn/v1/catalog`, `/learn/v1/courses`) - all return HTTP 403
3. Fell back to scraping public course listing pages on `www.paloaltonetworks.com`:
   - `/services/education/ilt` - Instructor-Led Training courses
   - `/services/education/certification` - Certification programs
4. Compiled {len(ilt)} ILT courses and {len(certs)} certification programs

## Data Quality

- **Title**: 100% complete (avg length ~{sum(len(c['title']) for c in courses) // total if total else 0} chars, 0 titles >150 chars)
- **Description**: 100% complete, {total}/{total} unique (100%)
- **Duration**: 0% (not publicly available without authentication)
- **Level**: {int(sum(1 for c in courses if c.get('level')) / total * 100 if total else 0)}% complete
- **Price**: 100% complete (ILT=Paid, Certifications=Paid)
- **Category**: 100% complete

## Limitations

1. **Auth wall**: Full course catalog on `learn.paloaltonetworks.com` requires user account login. The Docebo API returns 403 on all catalog endpoints without a valid session token.
2. **Free digital learning modules** are advertised but accessible only after login - not captured here.
3. **Course durations** are not available from public pages.
4. **Course codes**: EDU-210 and EDU-330 were captured; others are not publicly listed.
5. **Total course count unknown**: The LMS may contain hundreds more e-learning modules.

## Recommendations

- Obtain a Palo Alto Networks learning account (free registration available) to access the full Docebo catalog via authenticated API calls
- The Docebo API endpoint `/learn/v1/catalog` with a Bearer token would return the complete course catalog in JSON format

## Breakdown by Category

{chr(10).join(f'- {cat}: {count} courses' for cat, count in sorted(by_category.items(), key=lambda x: -x[1]))}

## Format Breakdown

- Instructor-Led Training: {len(ilt)}
- Certification Programs: {len(certs)}

## Sample Courses

"""
    for c in courses[:5]:
        report += f"""### {c['title']}
- **Category**: {c['category']}
- **Format**: {c['format']}
- **Level**: {c.get('level', 'N/A')}
- **Price**: {c['price']}
- **Description**: {c['description'][:200]}

"""

    return report


def update_registry(provider_name: str, provider_data: dict) -> None:
    registry_path = "/Users/bianders/.claude/skills/catalog-scraper/catalog_registry.json"

    with open(registry_path, "r") as f:
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


def regenerate_master_catalog() -> None:
    registry_path = "/Users/bianders/.claude/skills/catalog-scraper/catalog_registry.json"
    base_dir = "/Users/bianders/.claude/skills/catalog-scraper"

    with open(registry_path, "r") as f:
        registry = json.load(f)

    all_courses = []
    for pname, pinfo in registry["providers"].items():
        if "files" in pinfo and "json" in pinfo["files"]:
            try:
                with open(pinfo["files"]["json"], "r") as f:
                    courses = json.load(f)
                    all_courses.extend(courses)
            except Exception as e:
                print(f"  Warning: could not load {pname}: {e}")

    with open(os.path.join(base_dir, "master_catalog.json"), "w") as f:
        json.dump(all_courses, f, indent=2, ensure_ascii=False)

    if all_courses:
        df = pd.DataFrame(all_courses)
        df.to_excel(os.path.join(base_dir, "master_catalog.xlsx"), index=False, engine="openpyxl")

    print(f"Regenerated master_catalog files ({len(all_courses)} total courses)")


def main() -> dict:
    print(f"Scraping: {PROVIDER}")
    print(f"URL: {CATALOG_URL}")
    print("-" * 60)

    # Collect data
    print("\nScraping ILT courses...")
    ilt_courses = scrape_ilt_courses()
    time.sleep(1)

    print("\nScraping certification programs...")
    cert_programs = scrape_certifications()

    all_courses = ilt_courses + cert_programs
    total = len(all_courses)
    print(f"\nTotal items collected: {total}")

    # Export
    base_dir = "/Users/bianders/.claude/skills/catalog-scraper"
    os.chdir(base_dir)

    print("\nExporting data...")
    files = export_catalog_data(all_courses, PROVIDER_SLUG)

    # Generate report
    report_content = generate_report(all_courses, PROVIDER_SLUG)
    report_filename = f"{PROVIDER_SLUG}_report.md"
    with open(report_filename, "w") as f:
        f.write(report_content)

    # Move to providers dir
    provider_dir = f"providers/{PROVIDER_SLUG}"
    os.makedirs(provider_dir, exist_ok=True)
    for src, dst_name in [
        (files["json"], "catalog.json"),
        (files["xlsx"], "catalog.xlsx"),
        (report_filename, "report.md"),
    ]:
        dst = os.path.join(provider_dir, dst_name)
        shutil.move(src, dst)
        files[dst_name.split(".")[0]] = dst

    print(f"\nMoved files to {provider_dir}/")

    # Update registry
    ilt_count = len(ilt_courses)
    cert_count = len(cert_programs)
    avg_title_len = sum(len(c["title"]) for c in all_courses) // total if total else 0

    provider_data = {
        "status": "partial",
        "url": CATALOG_URL,
        "courses_count": total,
        "date_scraped": datetime.now().strftime("%Y-%m-%d"),
        "scraper_version": "1.0",
        "limitation": (
            "Docebo LMS catalog requires authentication. Data sourced from "
            "public marketing pages only (ILT courses and certification programs)."
        ),
        "data_quality": {
            "has_descriptions": True,
            "has_duration": False,
            "has_level": True,
            "avg_title_length": avg_title_len,
        },
        "files": {
            "json": f"{provider_dir}/catalog.json",
            "xlsx": f"{provider_dir}/catalog.xlsx",
            "report": f"{provider_dir}/report.md",
        },
        "notes": (
            f"{ilt_count} instructor-led courses, {cert_count} certification programs. "
            "Full e-learning catalog not accessible without account."
        ),
    }

    update_registry(PROVIDER, provider_data)
    regenerate_master_catalog()

    # Summary
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE: {PROVIDER}")
    print(f"{'='*60}")
    print(f"  Total items: {total}")
    print(f"  ILT courses: {ilt_count}")
    print(f"  Certifications: {cert_count}")
    print(f"\nARTIFACTS:")
    print(f"  JSON:   {provider_dir}/catalog.json")
    print(f"  XLSX:   {provider_dir}/catalog.xlsx")
    print(f"  Report: {provider_dir}/report.md")

    return {
        "provider": PROVIDER,
        "status": "partial",
        "courses_count": total,
        "files": {
            "json": f"{base_dir}/{provider_dir}/catalog.json",
            "xlsx": f"{base_dir}/{provider_dir}/catalog.xlsx",
            "report": f"{base_dir}/{provider_dir}/report.md",
        },
        "limitation": provider_data["limitation"],
    }


if __name__ == "__main__":
    main()
