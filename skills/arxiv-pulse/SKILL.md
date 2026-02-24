---
name: arxiv_api
description: "Query the arXiv API for academic paper intelligence. Use when the user asks to: search for papers on a topic (title, authors, abstract, published date, arXiv ID); count paper submission volume over time for a topic (monthly or quarterly trends); get recent papers from a specific arXiv category (cs.AI, cs.CL, stat.ML, etc.); or list recent papers by a named author. No auth required. Trigger phrases include 'find papers on X', 'how many arXiv papers on Y per month', 'recent papers in cs.CL', 'papers by [author]', 'arXiv search for', or any request to look up preprints or research publication trends."
---

# arXiv Pulse

Query the arXiv Atom/XML API at `export.arxiv.org/api/query`.

## Setup

```python
import sys
sys.path.insert(0, "/Users/bianders/.claude/skills/arxiv-pulse/scripts")
from arxiv import search_papers, get_volume_over_time, get_recent_papers, get_author_papers
```

Dependency: `httpx` (same as sec-filings skill).

## Core Functions

### Search papers by topic

```python
papers = search_papers("retrieval augmented generation", max_results=10)
# sort_by options: "relevance" (default), "submittedDate", "lastUpdatedDate"

for p in papers:
    print(p.id, p.title, p.published)
    print("Authors:", ", ".join(p.authors))
    print("Category:", p.category)
    print("URL:", p.url)
    print(p.abstract[:300])
```

### Publication volume over time

```python
# Monthly counts for the past 2 years (~72s due to 24 API calls at 3s each)
data = get_volume_over_time("retrieval augmented generation", months=24, granularity="month")
# Returns: [{"period": "2024-01", "count": 87}, ...]

# Quarterly for faster results (8 calls)
data = get_volume_over_time("diffusion models", months=24, granularity="quarter")
```

**Note:** This makes one API call per period. Warn the user upfront that 24-month monthly runs take ~72 seconds.

### Recent papers by category

```python
# Papers from the last 30 days in cs.CL
papers = get_recent_papers("cs.CL", days=30, max_results=50)
```

See `references/categories.md` for all category codes. For education/AI/CS use:
`cs.AI`, `cs.CL`, `cs.LG`, `cs.CV`, `cs.IR`, `cs.HC`, `cs.CY`, `cs.SE`, `stat.ML`

### Papers by author

```python
papers = get_author_papers("Yann LeCun", max_results=10)
# arXiv author search is fuzzy — verify matches against the returned results
```

## Paper Fields

```python
@dataclass
class Paper:
    id: str        # "2401.12345"
    title: str
    authors: list[str]
    abstract: str
    published: str  # "YYYY-MM-DD"
    category: str   # primary category, e.g. "cs.CL"
    url: str        # "https://arxiv.org/abs/2401.12345"
```

## Rate Limiting

The module enforces a 3-second minimum gap between requests (`_throttle()`). Never bypass this — arXiv blocks IPs that exceed the limit.

## Query Tips

- Multi-word phrases are auto-quoted: `search_papers("large language model")` → `all:"large language model"`
- For single-word or already-quoted inputs, quoting is skipped
- arXiv searches `all:` (title + abstract + author + other fields) by default
- `max_results` cap per request: 2000; total retrievable: 30,000

## References

- `references/categories.md` — full category code list with descriptions; read when the user asks about a specific domain or needs to pick a category
