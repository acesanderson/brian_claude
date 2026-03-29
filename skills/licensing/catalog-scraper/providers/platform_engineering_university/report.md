# Platform Engineering University - Catalog Scraping Report

**Date**: 2026-02-24
**URL**: https://university.platformengineering.org/
**Total Courses**: 12

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
- Description: 100% complete
- Duration: 100% complete
- Level: 100% complete (inferred from slug)
- Price: 100% complete

## Courses by Category

- Certification: 4
- AI / Machine Learning: 2
- Platform Engineering: 1
- GitOps: 1
- Cloud: 1
- Kubernetes: 1
- Observability: 1
- Security: 1

## Courses by Level

- All Levels: 5
- Advanced: 3
- Beginner: 3
- Intermediate: 1

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

- **Platform Engineering Certified Practitioner**
  URL: https://university.platformengineering.org/platform-engineering-certified-practitioner
  Level: Intermediate | Category: Certification | Price: $1,800
  Description: Hands-on certification for DevOps, SREs, and engineering managers that covers key platform engineering principles and pr...
- **Platform Engineering Certified Leader (April)**
  URL: https://university.platformengineering.org/platform-engineering-certified-leader-april
  Level: Advanced | Category: Certification | Price: $2,000
  Description: Advanced certification for senior tech leaders to connect platform strategy to business value through ROI, governance, a...
- **Platform Engineering Certified Professional (March)**
  URL: https://university.platformengineering.org/platform-engineering-certified-professional-march
  Level: Advanced | Category: Certification | Price: $2,000
  Description: Instructor-led certification for senior engineers to design and scale platforms. Covers MVP delivery, golden paths, ROI ...
- **Platform Engineering Certified Architect (April)**
  URL: https://university.platformengineering.org/platform-engineering-certified-architect-april
  Level: Advanced | Category: Certification | Price: $2,000
  Description: Instructor-led, hands-on certification for architects, platform engineers, and DevSecOps leaders that teaches how to des...
- **AI in Platform Engineering**
  URL: https://university.platformengineering.org/ai-in-platform-engineering
  Level: All Levels | Category: AI / Machine Learning | Price: $950
  Description: Platform engineering now enables enterprise AI. This course teaches you to apply AI-native capabilities to supercharge t...

## Files

- JSON: `platform_engineering_university_catalog.json`
- XLSX: `platform_engineering_university_catalog.xlsx`
