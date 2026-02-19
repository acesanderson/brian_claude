# The Taggart Institute Catalog Scraping Report

**Date**: 2026-02-17
**URL**: https://taggartinstitute.org/courses
**Total Courses**: 6

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
- Title: 100% complete (avg length: 27 chars, 0 titles >150 chars)
- Description: 100% complete (100.0% unique)
- Duration: 100% complete
- Level: 100% complete
- Price: 100% complete

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
- **Practical Web Application Security and Testing** (Free (pay-what-you-wish: $5, $10, $15)) - Beginner - Michael Taggart
  https://taggartinstitute.org/p/pwst
  Entry-level course covering web application technologies, security considerations for development, and the web penetrati...
- **Creating With Git** (Free (pay-what-you-wish: $1, $5, $10)) - Beginner to Intermediate - Michael Taggart
  https://taggartinstitute.org/p/creating-with-git
  Teaches essential Git skills for managing projects and publishing documentation. Students learn to work confidently with...
- **Responsible Red Teaming** (Free (pay-what-you-wish: $1, $5, $10, $15)) - Intermediate to Advanced - Matt Kiely (HuskyHacks)
  https://taggartinstitute.org/p/responsible-red-teaming
  Addresses the ethical, legal, and tactical dimensions of responsible red team operations. Emphasizes how to emulate cybe...
- **Python for Defenders, Pt. 2** (Free (pay-what-you-wish: $1, $5, $10, $15)) - Intermediate - Michael Taggart
  https://taggartinstitute.org/p/python-for-defenders-pt2
  Teaches data analysis using Python and Jupyter for cybersecurity applications. Students learn to import, parse, and visu...
- **Vim For Everyone** (Free (pay-what-you-wish: $1, $5, $10)) - Beginner - Michael Taggart
  https://taggartinstitute.org/p/vim-for-everyone
  Teaches mastery of the Vim text editor. While most people simply want to exit Vim, those who master it gain access to po...

## Catalog Overview
- **Free courses**: 5 (pay-what-you-wish model, max $15)
- **Paid**: 1 ($29.99 digital book)
- **Categories**: Cybersecurity (web security, red teaming, Python defense), Developer Tools (Vim, Git), IT Infrastructure
- **Instructors**: Michael Taggart (primary), Matt Kiely/HuskyHacks (guest)
- **Formats**: On-demand video, written lectures, digital book
