---
name: crossref_api
description: >
  Query the Crossref REST API for academic publisher intelligence. Use when the user wants to
  look up a publisher by name (total works, subject areas, publication volume over time), find
  the most-cited recent works for a DOI prefix, or compare publication volume between two
  publishers or two subject areas. No auth required. Reads CROSSREF_EMAIL env var for
  polite-pool access. Trigger phrases include "look up publisher", "how many works has
  [publisher] published", "most cited papers from [publisher/DOI prefix]",
  "compare [publisher A] vs [publisher B]", "compare publications in [subject A] vs [subject B]".
---

# Publisher Intel

Wraps the Crossref REST API (`https://api.crossref.org`). No dependencies beyond the standard library.

## Setup

Set `CROSSREF_EMAIL` for polite-pool access. Without it, Crossref rate-limits aggressively.

```bash
export CROSSREF_EMAIL=you@example.com
```

The script sends it as both a `mailto=` query param and in the `User-Agent` header.

## Script

`scripts/crossref.py` — run directly or import its functions.

## Four modes

### 1. Publisher profile by name

```bash
python crossref.py publisher "Elsevier"
python crossref.py publisher "Wiley"
```

Returns: Crossref member ID, DOI prefixes, total works, top subjects (sampled), year-by-year volume.

**Member name matching caveat**: Crossref member names don't always match common names. If a search returns no results or the wrong publisher:
- Try shorter/alternate names: "Springer" not "Springer Nature", "Taylor" not "Taylor & Francis"
- Check "Other matches" in the output — the first result may not be the intended publisher
- Large publishers often have multiple member entries (e.g., Elsevier has "Digital Commons-Elsevier" as a separate member)

### 2. Most-cited recent works for a DOI prefix

```bash
python crossref.py prefix 10.1016     # Elsevier
python crossref.py prefix 10.1038     # Nature
python crossref.py prefix 10.1007     # Springer
```

Returns top 10 works by citation count over the last 3 years, with authors, journal, DOI, subjects.

Use a DOI prefix (the part before the slash, e.g. `10.1016`). The publisher profile output lists prefixes.

### 3. Compare two publishers

```bash
python crossref.py compare-publishers "Elsevier" "Wiley"
```

Returns total works and a year-by-year table for both. Same name-matching caveats as mode 1.

### 4. Compare two subject areas

```bash
python crossref.py compare-subjects "machine learning" "deep learning"
python crossref.py compare-subjects "genomics" "proteomics"
```

Uses Crossref's free-text query (not a controlled vocabulary), so results reflect how often the term appears in metadata, not a strict subject taxonomy. Suitable for relative comparisons, not absolute counts.

## Importing functions directly

```python
from crossref import publisher_profile, prefix_top_cited, compare_publishers, compare_subjects

profile = publisher_profile("Elsevier")
# profile["total_works"], profile["volume_by_year"], profile["top_subjects"]

works = prefix_top_cited("10.1016", rows=5, years_back=2)
# works["works"][0]["title"], ["citations"], ["doi"], ["authors"]

cmp = compare_publishers("Elsevier", "Wiley")
cmp = compare_subjects("CRISPR", "RNA interference")
```

## API notes

- `volume_by_year` uses Crossref's `facet=published:*`. Years outside 1900–current are filtered (metadata errors are common in Crossref).
- Subject data comes from sampling 100 recent works; not all works have subject metadata, so `top_subjects` may be empty for some publishers.
- `compare-subjects` uses `filter=has-abstract:true` to reduce noise from non-substantive records.
- Citation counts (`is-referenced-by-count`) reflect citations registered in Crossref only, not all citations.
