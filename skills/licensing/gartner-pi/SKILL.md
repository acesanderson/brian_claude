---
name: gartner-pi
description: Query Gartner Peer Insights for market segments, product rankings, and product profiles. Used by licensing agents for competitive market intelligence. Trigger when asked to look up Gartner ratings, find top products in a market segment, or get a vendor's Gartner profile.
---

# gartner-pi

Scrapes Gartner Peer Insights for market intelligence. LLM agent use only.

## Prerequisites

- **uv** — https://docs.astral.sh/uv/getting-started/installation/
- Run once after install: `uv run --directory ~/.claude/skills/licensing/gartner-pi python -m playwright install chromium`

## Environment Variables

| Var | Required | Purpose |
|-----|----------|---------|
| `OXY_NAME` | Yes (all ops) | Oxylabs proxy username |
| `OXY_PASSWORD` | Yes (all ops) | Oxylabs proxy password |
| `BRAVE_API_KEY` | Yes (`product` only) | Brave Search API key |

## Commands

### List all market segments

```bash
uv run --directory ~/.claude/skills/licensing/gartner-pi python gartner.py segment-list
```

Returns `{"segments": [{"slug": "...", "name": "..."}], "cached": bool, "cached_at": "..."}` (~176 segments, cached 7 days)

### Get product rankings for a segment

```bash
uv run --directory ~/.claude/skills/licensing/gartner-pi python gartner.py segment <slug>
uv run --directory ~/.claude/skills/licensing/gartner-pi python gartner.py segment cloud-erp
```

Returns `{"slug": "...", "products": [{"rank": 1, "name": "...", "slug": "...", "rating": 4.3, "review_count": 1240}], ...}`

Note: segment pages may intermittently 403 (Gartner bot protection). The scraper retries 3 times. If all attempts fail, returns `{"error": "..."}` on stderr.

### Get a product's full profile

```bash
uv run --directory ~/.claude/skills/licensing/gartner-pi python gartner.py product "SAP S/4HANA"
```

Returns `{"name": "...", "slug": "...", "url": "...", "overall_rating": 4.3, "review_count": 1240, "description": "...", ...}`

### Force cache bypass

Add `--refresh` to any command:

```bash
uv run --directory ~/.claude/skills/licensing/gartner-pi python gartner.py segment-list --refresh
```

On refresh failure (3 retries exhausted), returns error on stderr — does NOT fall back to stale cache.

## Cache TTLs

| Operation | TTL | Cache file |
|-----------|-----|-----------|
| segment-list | 7 days | `cache/segment-list.json` |
| segment | 1 day | `cache/segment-{slug}.json` |
| product | 1 day | `cache/product-{slug}.json` |

## Error Format

All errors go to stderr with exit code 1:

```json
{"error": "No Gartner product page found for: Foo Bar"}
```

Success goes to stdout with exit code 0.
