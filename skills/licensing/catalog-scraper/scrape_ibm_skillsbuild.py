from __future__ import annotations

import json
import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

PROVIDER = "IBM SkillsBuild"
BASE_URL = "https://skillsbuild.org"
DATE_SCRAPED = datetime.now().strftime("%Y-%m-%d")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}


def get_next_data(url: str) -> dict:
    time.sleep(0.8)
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script:
        return {}
    return json.loads(script.string)


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def clean_to_ascii(text: str | None) -> str:
    if not text:
        return ""
    return unidecode(str(text))


# -------------------------------------------------------------------------
# Catalog 1: College students - /college-students/course-catalog
# 68 individual badges with full metadata
# -------------------------------------------------------------------------

def scrape_college_students() -> list[dict]:
    print("\n[1/3] Scraping college-students catalog...")
    data = get_next_data(f"{BASE_URL}/college-students/course-catalog")
    badge_sections = (
        data.get("props", {})
        .get("pageProps", {})
        .get("page", {})
        .get("rebrandBadgePageFields", {})
        .get("badgeSection", [])
    )

    courses = []
    for section in badge_sections:
        category = section.get("badgeSectionTitle", "")
        for badge_wrapper in section.get("badges", []):
            nodes = (
                badge_wrapper.get("collegeStudentBadge", {}).get("nodes", [])
            )
            for node in nodes:
                fields = node.get("rebrandBadgeFields", {})
                course = {
                    "provider": PROVIDER,
                    "audience": "College students",
                    "title": node.get("title", ""),
                    "url": fields.get("link", ""),
                    "description": strip_html(fields.get("description", "")),
                    "duration": fields.get("duration", ""),
                    "level": "",
                    "format": "On-Demand",
                    "price": "Free",
                    "category": category,
                    "languages": fields.get("languages", ""),
                    "eligibility": fields.get("eligibility", ""),
                    "date_scraped": DATE_SCRAPED,
                }
                courses.append(course)

    print(f"  -> {len(courses)} courses found")
    return courses


# -------------------------------------------------------------------------
# Catalog 2: High school students - 18 topic pages
# Cards per topic (~43 total)
# -------------------------------------------------------------------------

STUDENT_TOPICS = [
    ("Technical skills", "artificial-intelligence"),
    ("Technical skills", "blockchain"),
    ("Technical skills", "cloud-computing"),
    ("Technical skills", "cybersecurity"),
    ("Technical skills", "data-science"),
    ("Technical skills", "emerging-tech-intro"),
    ("Technical skills", "enterprise-computing"),
    ("Technical skills", "it-support"),
    ("Technical skills", "quantum-computing"),
    ("Technical skills", "ux-design"),
    ("Technical skills", "web-development"),
    ("Workplace skills", "agile"),
    ("Workplace skills", "design-thinking"),
    ("Workplace skills", "job-readiness"),
    ("Workplace skills", "mindfulness"),
    ("Workplace skills", "professional-skills"),
    ("Expand your horizons", "principles-of-design"),
    ("Expand your horizons", "sustainability"),
]


def scrape_students() -> list[dict]:
    print("\n[2/3] Scraping high school students catalog (18 topic pages)...")
    courses = []

    for collection, slug in STUDENT_TOPICS:
        url = f"{BASE_URL}/students/course-catalog/{slug}"
        data = get_next_data(url)
        pp = data.get("props", {}).get("pageProps", {})
        topic = pp.get("studentCourseTopic", {})
        if not topic:
            print(f"  [WARN] No topic data for {slug}")
            continue

        topic_name = topic.get("name", slug.replace("-", " ").title())
        card_sections = (
            topic.get("studentCourseTopicFields", {}).get("cardGroupSection", [])
        )

        for section in card_sections:
            # Only include student-facing cards, not educator sections
            heading = section.get("heading", "")
            if "educator" in heading.lower():
                continue
            for card in section.get("cards", []):
                title = card.get("heading", "")
                href = card.get("href", "")
                eyebrow = card.get("eyebrow", "")
                duration = card.get("helperText2", "") or ""

                course = {
                    "provider": PROVIDER,
                    "audience": "High school students",
                    "title": title,
                    "url": href,
                    "description": "",
                    "duration": duration,
                    "level": "Beginner",
                    "format": "On-Demand",
                    "price": "Free",
                    "category": f"{collection} / {topic_name}",
                    "languages": "English",
                    "eligibility": "Registered learners",
                    "date_scraped": DATE_SCRAPED,
                }
                courses.append(course)

        print(f"  {slug}: {sum(len(s.get('cards', [])) for s in card_sections if 'educator' not in s.get('heading', '').lower())} cards")

    print(f"  -> {len(courses)} courses found")
    return courses


# -------------------------------------------------------------------------
# Catalog 3: Adult learners - 12 topic pages
# Featured resources and course cards
# -------------------------------------------------------------------------

ADULT_TOPICS = [
    ("Technical skills", "artificial-intelligence"),
    ("Technical skills", "customer-service-representative"),
    ("Technical skills", "cybersecurity-analyst"),
    ("Technical skills", "data-analyst"),
    ("Technical skills", "it-support-technician"),
    ("Technical skills", "project-manager"),
    ("Technical skills", "user-experience-design"),
    ("Technical skills", "web-developer"),
    ("Workplace skills", "technology-skills"),
    ("Workplace skills", "ways-of-working"),
    ("Workplace skills", "workforce-readiness"),
    ("Workplace skills", "sustainability"),
]


def scrape_adult_learners() -> list[dict]:
    print("\n[3/3] Scraping adult-learners catalog (12 topic pages)...")
    courses = []

    for collection, slug in ADULT_TOPICS:
        url = f"{BASE_URL}/adult-learners/explore-learning/{slug}"
        data = get_next_data(url)
        pp = data.get("props", {}).get("pageProps", {})
        lp = pp.get("learningPathway", {})
        if not lp:
            print(f"  [WARN] No learningPathway data for {slug}")
            continue

        topic_name = lp.get("name", slug.replace("-", " ").title())
        jsf = lp.get("jobSeekerLearningPathwayFields", {})
        new_design = lp.get("adultLearnersNewDesignFields", {})

        items_added = 0

        # Featured resources
        for res in jsf.get("featuredResources") or []:
            title = res.get("title", "") or res.get("heading", "")
            href = res.get("link", "") or res.get("href", "") or res.get("url", "")
            desc = strip_html(res.get("description", "") or res.get("copy", ""))
            if not title:
                continue
            course = {
                "provider": PROVIDER,
                "audience": "Adult learners",
                "title": title,
                "url": href,
                "description": desc,
                "duration": res.get("duration", "") or "",
                "level": "",
                "format": "On-Demand",
                "price": "Free",
                "category": f"{collection} / {topic_name}",
                "languages": "English",
                "eligibility": "Registered learners",
                "date_scraped": DATE_SCRAPED,
            }
            courses.append(course)
            items_added += 1

        # Course cards from new design
        cards = (new_design.get("adultLearnersCourses") or {}).get("cards") or []
        for card in cards:
            title = card.get("heading", "") or card.get("title", "")
            href = card.get("href", "") or card.get("link", "") or card.get("url", "")
            if not title:
                continue
            course = {
                "provider": PROVIDER,
                "audience": "Adult learners",
                "title": title,
                "url": href,
                "description": strip_html(card.get("copy", "") or ""),
                "duration": card.get("helperText2", "") or "",
                "level": "",
                "format": "On-Demand",
                "price": "Free",
                "category": f"{collection} / {topic_name}",
                "languages": "English",
                "eligibility": "Registered learners",
                "date_scraped": DATE_SCRAPED,
            }
            courses.append(course)
            items_added += 1

        print(f"  {slug}: {items_added} items")

    print(f"  -> {len(courses)} courses found")
    return courses


# -------------------------------------------------------------------------
# Export
# -------------------------------------------------------------------------

def export(courses: list[dict], provider_slug: str) -> dict[str, str]:
    df = pd.DataFrame(courses)

    column_order = [
        "provider", "audience", "title", "url", "description", "duration",
        "level", "format", "price", "category", "languages", "eligibility",
        "date_scraped",
    ]
    existing = [c for c in column_order if c in df.columns]
    df = df[existing]

    # Quality checks
    if "title" in df.columns:
        avg_len = df["title"].str.len().mean()
        long = df[df["title"].str.len() > 150]
        print(f"\nTitle quality: avg={avg_len:.0f} chars, {len(long)} titles >150 chars")

    if "description" in df.columns:
        total = len(df)
        unique = df["description"].nunique()
        pct = unique / total * 100 if total else 0
        print(f"Description quality: {unique}/{total} unique ({pct:.1f}%)")

    # JSON
    json_path = f"{provider_slug}_catalog.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)

    # XLSX
    xlsx_path = f"{provider_slug}_catalog.xlsx"
    df_ascii = df.copy()
    text_cols = df_ascii.select_dtypes(include=["object"]).columns
    for col in text_cols:
        df_ascii[col] = df_ascii[col].apply(clean_to_ascii)
    df_ascii.to_excel(xlsx_path, index=False, engine="openpyxl")

    print(f"\nJSON: {json_path}")
    print(f"XLSX: {xlsx_path}")
    return {"json": json_path, "xlsx": xlsx_path}


# -------------------------------------------------------------------------
# Report
# -------------------------------------------------------------------------

def generate_report(courses: list[dict], provider_slug: str, files: dict) -> str:
    df = pd.DataFrame(courses)

    total = len(df)
    by_audience = df.groupby("audience").size().to_dict()
    by_category = df.groupby("category").size().sort_values(ascending=False).head(15).to_dict()
    desc_complete = (df["description"].str.len() > 0).sum() / total * 100 if total else 0
    dur_complete = (df["duration"].str.len() > 0).sum() / total * 100 if total else 0
    avg_title = df["title"].str.len().mean()

    samples = df.head(5)

    report = f"""# IBM SkillsBuild Catalog Scraping Report

**Date**: {DATE_SCRAPED}
**URL**: {BASE_URL}
**Total Courses/Resources**: {total}

## Architecture
- Type: Multi-page, Next.js SSG (static site generation)
- Data Source: JSON embedded in `__NEXT_DATA__` script tag on each page
- Obstacles: None - all data available without auth

## Catalog Structure
IBM SkillsBuild serves three audiences, each with separate catalog pages:

| Audience | Courses Found | Source |
|----------|--------------|--------|
"""
    for audience, count in sorted(by_audience.items()):
        report += f"| {audience} | {count} | __NEXT_DATA__ JSON |\n"

    report += f"""
**Total**: {total} courses/learning resources

## Extraction Method
- Strategy A: JSON extraction from Next.js `__NEXT_DATA__` embedded script
- No scraping/parsing of rendered HTML required
- College students: `rebrandBadgePageFields.badgeSection[].badges[].collegeStudentBadge.nodes[]`
- High school students: `studentCourseTopic.studentCourseTopicFields.cardGroupSection[].cards[]` (18 topic pages)
- Adult learners: `learningPathway.jobSeekerLearningPathwayFields.featuredResources[]` + `adultLearnersCourses.cards[]` (12 topic pages)

## Data Quality
- Title: 100% complete (avg length: {avg_title:.0f} chars)
- Description: {desc_complete:.0f}% complete (college-students catalog only; HS and adult learner cards lack descriptions)
- Duration: {dur_complete:.0f}% complete
- Level: college-students records have no level field; HS records default to Beginner
- Price: 100% Free

## Top Categories (College Students)
"""
    college_cats = df[df["audience"] == "College students"].groupby("category").size().sort_values(ascending=False).to_dict() if total else {}
    for cat, cnt in college_cats.items():
        report += f"- {cat}: {cnt} courses\n"

    report += f"""
## Limitations
- High school and adult-learner cards lack individual descriptions (they link to IBM YourLearning platform)
- Adult-learner pages are mostly thin landing pages; most content lives behind IBM YourLearning
- No level/difficulty metadata for college-students or adult-learner items
- Languages field only populated for college-students catalog

## Recommendations
- College-students catalog (68 courses) is highest quality for LinkedIn Learning licensing evaluation
- HS and adult-learner items are mostly channel/path links, not individual courses
- Consider focusing on the 68 college-student badges which have full metadata

## Sample Courses
"""
    for _, row in samples.iterrows():
        report += f"\n### {row['title']}\n"
        report += f"- **Audience**: {row['audience']}\n"
        report += f"- **Category**: {row['category']}\n"
        report += f"- **Duration**: {row['duration'] or 'N/A'}\n"
        report += f"- **URL**: {row['url']}\n"
        if row.get("description"):
            report += f"- **Description**: {row['description'][:200]}\n"

    report_path = f"{provider_slug}_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report: {report_path}")
    return report_path


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------

def main():
    provider_slug = "ibm_skillsbuild"

    college_courses = scrape_college_students()
    student_courses = scrape_students()
    adult_courses = scrape_adult_learners()

    all_courses = college_courses + student_courses + adult_courses
    print(f"\nTotal combined: {len(all_courses)} courses/resources")

    files = export(all_courses, provider_slug)
    report_path = generate_report(all_courses, provider_slug, files)
    files["report"] = report_path

    return all_courses, files


if __name__ == "__main__":
    main()
