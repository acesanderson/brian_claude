from __future__ import annotations

import json
import time
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode


def clean_to_ascii(text: str | None) -> str:
    """Convert Unicode text to clean ASCII."""
    if not text:
        return ""
    return unidecode(str(text))


def scrape_checkpoint_training() -> list[dict]:
    """Scrape Check Point training catalog from embedded tables."""
    url = "https://www.checkpoint.com/services/training/"

    print(f"Fetching {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    time.sleep(1)

    soup = BeautifulSoup(response.content, "html.parser")

    courses = []

    # Find all tab panes (Quantum, CloudGuard, Harmony)
    tab_panes = soup.find_all("div", class_="tab-pane")

    for pane in tab_panes:
        # Determine category from the tab pane ID
        pane_id = pane.get("id", "")
        if "Quantum" in pane_id:
            category = "Quantum"
        elif "CloudGuard" in pane_id:
            category = "CloudGuard"
        elif "Harmony" in pane_id:
            category = "Harmony"
        else:
            category = "General"

        # Find the table with courses
        table = pane.find("table")
        if not table:
            continue

        # Find all course rows (skip header row)
        rows = table.find("tbody").find_all("tr") if table.find("tbody") else []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 6:
                continue

            # Extract course data from table cells
            title_cell = cells[0]
            duration_cell = cells[1]
            price_cell = cells[2]
            language_cell = cells[3]
            level_cell = cells[4]

            # Extract title and URL
            title_link = title_cell.find("a")
            if not title_link:
                continue

            title = title_link.get_text(strip=True)
            url = title_link.get("href", "")

            # Extract other metadata
            duration = duration_cell.get_text(strip=True)
            price = price_cell.get_text(strip=True)
            language = language_cell.get_text(strip=True)
            level = level_cell.get_text(strip=True)

            # Build course dict
            course = {
                "provider": "Check Point",
                "title": title,
                "url": url,
                "description": "",  # Not available on this page
                "duration": duration,
                "level": level,
                "format": "Self-Paced" if "Free" in price else "Instructor-Led",
                "price": price,
                "category": category,
                "language": language,
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            }

            courses.append(course)
            print(f"  ✓ {title} ({category})")

    return courses


def export_catalog_data(courses_data: list[dict], provider_slug: str) -> dict[str, str]:
    """Export to JSON and XLSX."""
    # Convert to DataFrame
    df = pd.DataFrame(courses_data)

    # Column order
    column_order = [
        "provider",
        "title",
        "url",
        "description",
        "duration",
        "level",
        "format",
        "price",
        "category",
        "language",
        "date_scraped",
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
        else:
            print(f"  ✓ All titles are appropriately concise\n")

        df = df.drop(columns=["title_length"])

    # VALIDATE DESCRIPTION QUALITY
    if "description" in df.columns:
        total_descs = len(df)
        non_empty = df[df["description"] != ""]
        unique_descs = df["description"].nunique()
        uniqueness_pct = (unique_descs / total_descs * 100) if total_descs > 0 else 0

        print(f"⚠️  DESCRIPTION QUALITY CHECK:")
        print(f"  Total courses: {total_descs}")
        print(f"  Non-empty descriptions: {len(non_empty)}")
        print(f"  Unique descriptions: {unique_descs}")
        print(f"  Uniqueness: {uniqueness_pct:.1f}%")

        if len(non_empty) > 0 and uniqueness_pct < 90:
            print(f"  ❌ WARNING: Low description uniqueness ({uniqueness_pct:.1f}%)")
            print(
                f"     This suggests generic catalog text instead of course-specific descriptions."
            )
            print(
                f"     Review the scraping logic to extract individual course descriptions.\n"
            )
        elif len(non_empty) == 0:
            print(f"  ℹ️  No descriptions available on landing page (acceptable)\n")
        else:
            print(f"  ✓ Description quality is good\n")

    # 1. JSON (preserve Unicode)
    json_filename = f"{provider_slug}_catalog.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(courses_data, f, indent=2, ensure_ascii=False)

    # 2. XLSX (Excel format - handles all text reliably)
    xlsx_filename = f"{provider_slug}_catalog.xlsx"
    # Apply ASCII cleaning to all text columns for cleaner output
    text_columns = df.select_dtypes(include=["object"]).columns
    for col in text_columns:
        df[col] = df[col].apply(clean_to_ascii)
    df.to_excel(xlsx_filename, index=False, engine="openpyxl")

    return {"json": json_filename, "xlsx": xlsx_filename}


def main():
    print("="*60)
    print("Check Point Training Catalog Scraper")
    print("="*60)

    # Scrape courses
    courses = scrape_checkpoint_training()

    print(f"\n✓ Scraped {len(courses)} courses")

    if not courses:
        print("\n❌ No courses found")
        return

    # Export data
    print("\nExporting data...")
    files = export_catalog_data(courses, "checkpoint")

    print(f"\n✓ JSON:   {files['json']}")
    print(f"✓ XLSX:   {files['xlsx']}")

    # Display sample
    print("\n" + "="*60)
    print("SAMPLE COURSES")
    print("="*60)
    for course in courses[:5]:
        print(f"\n{course['title']}")
        print(f"  Category: {course['category']}")
        print(f"  Duration: {course['duration']} | Level: {course['level']} | Price: {course['price']}")
        print(f"  URL: {course['url']}")


if __name__ == "__main__":
    main()
