---
name: openalex_api
description: >
  Query the OpenAlex API for academic research intelligence. Use when the user asks to:
  search for papers or publications on a topic and see how volume has grown over time;
  look up a university or research institution's output (paper count, citations, h-index,
  top research fields); or find which academic fields are trending / growing fastest by
  publication volume. Trigger phrases include "how many papers on X", "publication trends
  for Y", "research output of [university]", "what fields are trending in academia",
  "fastest growing research areas", or any request to analyze scholarly publication data.
  No API key required. Set OPENALEX_EMAIL env var for polite-pool access (recommended).
---

# Research Pulse

Wraps the OpenAlex API (https://api.openalex.org) for three research intelligence tasks.

## Setup

```python
import sys
sys.path.insert(0, "/Users/bianders/.claude/skills/research-pulse/scripts")
from openalex import search_works, institution_profile, trending_topics
```

No API key needed. Set `OPENALEX_EMAIL` in the environment to use the polite pool
(avoids rate limiting; OpenAlex requests it for courtesy).

## Core Functions

### `search_works(query, years_back=5, max_results=200) -> WorkSearchResult`

Search works by keyword/topic. Returns publication volume over time and top papers.

```python
result = search_works("large language models", years_back=3)
print(result.total_count)       # total matching works
print(result.by_year)           # {"2022": 3400, "2023": 18000, "2024": 52000, ...}
for w in result.top_works[:5]:
    print(f"[{w.year}] {w.title} — {w.cited_by_count:,} cites")
```

`WorkSearchResult` fields: `query`, `total_count`, `by_year` (sorted dict), `top_works`.
`Work` fields: `id`, `title`, `year`, `cited_by_count`, `doi`, `primary_topic`.

Pagination: cursor-based internally; `max_results` caps the works list.

### `institution_profile(name) -> InstitutionProfile`

Look up a university or research org by name. Matches the first OpenAlex search result.

```python
prof = institution_profile("Stanford University")
print(prof.works_count, prof.cited_by_count, prof.h_index)
print(prof.top_fields[:5])     # top research topics by paper count
print(prof.works_by_year)      # {"2020": 8200, "2021": 9100, ...}
```

`InstitutionProfile` fields: `id`, `name`, `country`, `works_count`, `cited_by_count`,
`h_index`, `top_fields` (list of topic names), `works_by_year`.

Raises `ValueError` if no institution matches.

### `trending_topics(top_n=20, recent_years=2, baseline_years=2, min_recent_count=500) -> list[TrendingTopic]`

Return the academic fields growing fastest by publication volume. Compares a recent
window against the prior baseline window of equal length. Sorted by `growth_pct` desc.

```python
topics = trending_topics(top_n=15)
for t in topics:
    print(f"{t.name}: +{t.growth_pct:.0f}%  ({t.recent_count:,} recent papers)")
```

`TrendingTopic` fields: `id`, `name`, `recent_count`, `baseline_count`, `growth_pct`.

Only topics present in **both** windows with `>= min_recent_count` recent publications
are included (noise filter). The top 200 topics per window are compared; niche topics
may not appear.

## API Notes

- Base URL: `https://api.openalex.org`
- Cursor pagination: pass `cursor=*` initially; use `meta.next_cursor` for subsequent pages
- `group_by=publication_year` and `group_by=primary_topic.id` aggregate without full pagination
- Filter syntax: `filter=field:value,field2:value2` (AND); `field:val1|val2` (OR)
- `sort=cited_by_count:desc`, `sort=publication_year:desc`
- Standard `per_page` max: 200
