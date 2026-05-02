# Platform Scrapers — Lake 2 Ingest

Two scrapers feed Lake 2 (`platform_courses` / `platform_creators`) with data from competing
platforms. Each scraper has an export adapter that writes a catalog-ingestible JSON file, then
calls `catalog platform-ingest` to load it. Use these when you need fresh Coursera or Udemy
data in the DB — e.g., before running `catalog platform-search`.

**Do not touch scraping logic in either project.** The export/sync layer is the only integration point.

## Shared Export Contract

JSON array, each record:

| Field | Type | Notes |
|---|---|---|
| `platform_id` | str | required |
| `title` | str | required |
| `url` | str | required |
| `platform` | str | required — `'coursera'` or `'udemy'` |
| `is_free` | bool | required |
| `avg_rating` | float\|null | |
| `num_reviews` | int\|null | |
| `enrollments` | int\|null | |
| `product_type` | str\|null | |
| `difficulty` | str\|null | |
| `skills` | str\|null | comma-separated |
| `partners` | str\|null | Coursera only |
| `instructors` | str\|null | Udemy only |
| `headline` | str\|null | Udemy only |
| `num_lectures` | int\|null | Udemy only |
| `duration_hours` | float\|null | Udemy only |
| `ufb` | bool\|null | Udemy only; always null at ingest — set post-ingest by `load_ufb.py` |

Ingest call (same for both platforms):
```bash
uv run --project ~/vibe/licensing-project/catalog catalog platform-ingest <file> <platform>
```

---

## Corsair — Coursera (`$BC/corsair-project`)

Scrapes Coursera's full catalog via GraphQL. Saves raw data to `src/corsair/courses.json`.
Export adapter maps `CourseraCourseSearchResult` → shared spec and ingests into Lake 2.

**Manual sync:**
```bash
uv run --project ~/Brian_Code/corsair-project corsair-sync
# or with custom output path:
uv run --project ~/Brian_Code/corsair-project corsair-sync --output /tmp/corsair_export.json
```

**Auto-sync after scrape** (opt-in):
```bash
# In corsair-project/.envrc, set:
export CORSAIR_AUTO_SYNC=1
# Then run the scraper normally — sync fires automatically at the end of main()
uv run --project ~/Brian_Code/corsair-project python -m corsair.search_courses
```
`CORSAIR_AUTO_SYNC` defaults to `0`. The hook is at the bottom of `search_courses.py:main()`.

**Key files:**
- `src/corsair/search_courses.py` — GraphQL scraper; writes `courses.json`
- `src/corsair/export.py` — `to_catalog_json(output_path)` — maps fields, validates, writes export file
- `src/corsair/sync_catalog.py` — `sync()` / `main()` — calls export then platform-ingest

**Field mapping:**

| Coursera field | platform_courses field |
|---|---|
| url path stripped of leading `/` | `platform_id` |
| `name` | `title` |
| `https://www.coursera.org` + url | `url` |
| `avgProductRating` | `avg_rating` |
| `numProductRatings` | `num_reviews` |
| `enrollments` | `enrollments` |
| `productType` | `product_type` |
| `productDifficultyLevel` | `difficulty` |
| `skills` (list → comma-sep) | `skills` |
| `partners` (list → comma-sep) | `partners` |
| hardcoded `False` | `is_free` |
| hardcoded `'coursera'` | `platform` |

---

## Menuhin — Udemy (`$BC/menuhin-project`)

_Stub — to be filled in by the Menuhin maintainer._

Scrapes Udemy's catalog. Export adapter maps Udemy API fields → shared spec and ingests into Lake 2.

**Manual sync:**
```bash
# TODO: fill in once menuhin-sync entry point is implemented
```

**Auto-sync after scrape** (opt-in):
```bash
# TODO: MENUHIN_AUTO_SYNC env var, same pattern as Corsair
```

**Key files:** _(to be documented)_

**Field mapping:** _(to be documented — see agreed spec in shared contract above)_

---

## edX (`$VIBE/licensing-project/platform/edx/`)

Scrapes edX's full course catalog via sitemap + per-page JSON-LD extraction. No API —
edX embeds a rich `Course` JSON-LD block on every course page with all key fields.

**Not integrated with Lake 2.** Output is a standalone `courses.json` used as a sourcing
signal (which orgs are publishing on edX, at what volume and topic). Run infrequently —
edX is a legacy library and the catalog changes slowly.

**Run:**
```bash
uv run --project ~/vibe/licensing-project/platform/edx edx-scrape \
  --output ~/vibe/licensing-project/platform/edx/courses.json
```

**Test (subset):**
```bash
uv run --project ~/vibe/licensing-project/platform/edx edx-scrape \
  --limit 20 --output /tmp/edx_test.json
```

**Resume after failure:** Re-run the same command. Progress is saved to
`courses.checkpoint.jsonl` after every course. Already-scraped URLs are skipped
automatically. Delete the checkpoint file for a clean re-scrape.

**Options:**
- `--concurrency` (default 8) — parallel requests
- `--delay` (default 0.5s) — pause per worker after each request
- `--limit N` — scrape only N pending URLs (0 = all)

**Key files:**
- `edx_scraper/sitemap.py` — fetches `https://www.edx.org/sitemap.xml`, extracts ~5,089 course URLs
- `edx_scraper/scrape.py` — async page fetcher + JSON-LD parser
- `edx_scraper/models.py` — `EdxCourse` Pydantic model
- `edx_scraper/cli.py` — Click entry point with checkpoint logic
- `courses.json` — last full scrape output (gitignored)
- `courses.checkpoint.jsonl` — incremental progress log (gitignored)

**Field mapping (JSON-LD → EdxCourse):**

| JSON-LD field | EdxCourse field |
|---|---|
| `courseCode` | `platform_id` |
| `name` | `title` |
| page URL | `url` |
| URL path segment `/learn/{subject}/` | `subject` |
| `provider[0].name` | `organization` |
| last segment of `provider[0].url` | `org_slug` |
| `educationalLevel` | `level` |
| `inLanguage` | `language` |
| `isAccessibleForFree` | `is_free` |
| `timeRequired` (ISO 8601) | `time_required` |
| `totalHistoricalEnrollment` | `enrollments` |
| `aggregateRating.ratingValue` | `avg_rating` |
| `aggregateRating.ratingCount` | `num_reviews` |
| `about[].name` (comma-sep) | `skills` |
| `datePublished` | `date_published` |
| `dateModified` | `date_modified` |
| sitemap `<lastmod>` | `sitemap_lastmod` |

**Last full scrape:** 2026-05-01 — 5,036 courses, 216 orgs. Top orgs: IBM (188),
Delft (165), Harvard (160), Google Cloud (119), Stanford (111), MIT (105).
