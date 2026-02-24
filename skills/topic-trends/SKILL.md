---
name: google_trends_api
description: Query Google Trends data via pytrends (no auth required). Use when the user asks about search interest trends, topic momentum, rising topics, or wants to compare how popular different search terms are over time. Triggers include "Google Trends", "search interest", "which topic is trending", "compare interest in X vs Y", "rising queries for", or any request to chart or analyze keyword popularity over time.
---

# Topic Trends

Wraps the `pytrends` library to pull live Google Trends data. No API key required.

## Script

`scripts/trends.py` — run with `uv run --with pytrends python scripts/trends.py <command> [args]`

Three commands:

| Command | What it does |
|---------|-------------|
| `interest` | Weekly interest scores (0-100) for 1-5 terms |
| `related` | Top and rising related queries for one term |
| `compare` | Interest over time + 4-week average + identifies the leader |

## Usage

```bash
# Interest over time (default: last 12 months, worldwide)
uv run --with pytrends python scripts/trends.py interest "machine learning" "deep learning"

# With options
uv run --with pytrends python scripts/trends.py interest "python course" --timeframe "today 5-y" --geo "US"

# Related queries
uv run --with pytrends python scripts/trends.py related "python course"

# Compare momentum
uv run --with pytrends python scripts/trends.py compare "python course" "rust course" "go course"
```

## Parameters

- `--timeframe`: Any pytrends format — `"today 12-m"`, `"today 5-y"`, `"now 7-d"`, `"2023-01-01 2024-01-01"`. Default: `"today 12-m"`.
- `--geo`: Two-letter country code (`"US"`, `"GB"`) or region (`"US-CA"`). Default: worldwide.

## Output shapes

**interest / compare**
```json
{
  "terms": ["python course", "rust course"],
  "timeframe": "today 12-m",
  "geo": "",
  "data": [{"date": "2025-03-02", "python course": 36, "rust course": 1, "is_partial": false}],
  "comparison": {"averages_last_4_weeks": {"python course": 53.2, "rust course": 5.8}, "leader": "python course"}
}
```

**related**
```json
{
  "term": "python course",
  "top": [{"query": "python course free", "value": 100}],
  "rising": [{"query": "python uv tutorial", "value": 5400}]
}
```

`is_partial: true` marks the current incomplete week — exclude it from trend analysis.

## Interpretation notes

- Scores are relative (0-100), not absolute search volumes. A score of 50 means half the peak interest in the window.
- `compare` uses the last 4 complete weeks to determine `leader`, which captures recent momentum rather than historical average.
- Rate limits: Google Trends throttles aggressive scraping. Add `time.sleep(5)` between calls if running many queries in a loop.
