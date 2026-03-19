# Gartner Peer Insights Scraper — Design Spec

**Date:** 2026-03-18
**Location:** `~/.claude/skills/licensing/gartner-pi/`
**Consumer:** LLM agents only (not human CLI users)

---

## Purpose

Expose Gartner Peer Insights market intelligence to LLM agents in the licensing workflow. Three read-only operations: enumerate market segments, rank products within a segment, and fetch a full product profile.

---

## Architecture

Single Python script (`gartner.py`) with a subcommand CLI, TTL-based JSON file cache, and all browser/parsing logic self-contained. No cross-skill dependencies.

```
~/.claude/skills/licensing/gartner-pi/
├── gartner.py       # CLI entry point + all logic
├── pyproject.toml
├── uv.lock
├── SKILL.md
└── cache/           # auto-created; gitignored
```

---

## Operations

### `segment-list`

Fetches `https://www.gartner.com/reviews/home` via Playwright + Oxylabs. Extracts all `<a href="/reviews/market/{slug}">` links, deduplicated by slug. If fewer than 10 segments are found, treat as a parse failure and retry (same retry logic as 403). Returns slug + display name.

**Output:**
```json
{
  "segments": [
    {"slug": "cloud-erp", "name": "Cloud ERP"}
  ],
  "cached": false,
  "cached_at": "2026-03-18T10:00:00"
}
```

- `cached`: `true` if served from disk, `false` if fetched live this call
- `cached_at`: timestamp the cache file was written (present on both cached and live responses)

Cache key: `cache/segment-list.json`, TTL: 7 days.

---

### `segment <slug>`

Fetches `https://www.gartner.com/reviews/market/{slug}` via Playwright + Oxylabs. Extracts the ranked product list. Content validation: if no elements matching `[class*="rating"]` or containing a numeric rating pattern (e.g., `4.3`) adjacent to a review count are found in the parsed HTML, treat as a retriable fetch failure. Exact selector should be confirmed against a live fetch during implementation.

**Output:**
```json
{
  "slug": "cloud-erp",
  "products": [
    {"rank": 1, "name": "SAP S/4HANA", "slug": "sap-s-4hana", "rating": 4.3, "review_count": 1240}
  ],
  "cached": false,
  "cached_at": "2026-03-18T10:00:00"
}
```

Cache key: `cache/segment-{slug}.json`, TTL: 1 day.

---

### `product <name>`

Two-step lookup:

**Step 1 — slug resolution via Brave search:**
- Query: `site:gartner.com/reviews/product {name}`
- Scan results for URLs matching the pattern `gartner.com/reviews/product/{slug}`
- First matching URL wins; extract the slug
- If zero results match the pattern, return `{"error": "No Gartner product page found for: {name}"}` with exit code 1

**Step 2 — browser fetch:**
- Fetch `https://www.gartner.com/reviews/product/{slug}` via Playwright + Oxylabs
- Extract full profile. Content validation: if no element matching `[class*="rating"]` containing a numeric value is found, treat as retriable fetch failure. Exact selector confirmed during implementation.

**Output:**
```json
{
  "name": "SAP S/4HANA",
  "slug": "sap-s-4hana-1020798628",
  "url": "https://www.gartner.com/reviews/product/sap-s-4hana-1020798628",
  "overall_rating": 4.3,
  "review_count": 1240,
  "description": "...",
  "cached": false,
  "cached_at": "2026-03-18T10:00:00"
}
```

Cache key: `cache/product-{slug}.json` where `{slug}` is the **resolved Gartner slug** from step 1 (not the input name). This ensures two slightly different input names that resolve to the same product share one cache file and use the canonical identifier.

TTL: 1 day.

---

## Browser Fetch

Self-contained `_fetch_with_browser(url)` using Playwright sync API + `playwright-stealth` + Oxylabs residential proxy. No dependency on `brave-web-search` skill.

Key parameters proven to work against Gartner:
- `wait_until='load'` (not `networkidle` — Gartner loads tracking scripts indefinitely)
- `page.wait_for_timeout(4000)` after load
- `Stealth().apply_stealth_sync(page)` — must be applied to the page, not the context
- Oxylabs proxy: `http://pr.oxylabs.io:7777` with `customer-{OXY_NAME}` credentials

**Retry logic:** Retry on HTTP 403 OR on content validation failure (absent expected DOM elements — Gartner sometimes returns HTTP 200 with a CAPTCHA/challenge page). Up to 3 attempts with exponential backoff: wait 2s before attempt 2, 4s before attempt 3 (plus up to 1s random jitter each). All other errors are fatal immediately.

---

## Caching

Simple file-based cache in `cache/` directory (auto-created if absent):
- On read: check if file exists and `mtime > now - TTL`; return parsed JSON if fresh
- On miss: fetch, parse, write JSON with `cached_at` set to current UTC timestamp
- `--refresh` flag: bypass cache and fetch live. On fetch failure (after 3 retries), return error — do NOT fall back to stale cache, do NOT overwrite the existing cache file.

---

## Error Handling

All errors go to stderr as `{"error": "..."}` with exit code 1. Success always goes to stdout as JSON with exit code 0.

---

## Environment Variables

| Var | Required | Used for |
|-----|----------|----------|
| `OXY_NAME` | Yes (all ops) | Oxylabs proxy auth |
| `OXY_PASSWORD` | Yes (all ops) | Oxylabs proxy auth |
| `BRAVE_API_KEY` | Yes (`product` only) | Brave search API for slug resolution |

---

## Dependencies

```toml
dependencies = [
    "playwright>=1.44.0",
    "playwright-stealth>=2.0.0,<3.0.0",
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
]
```

`playwright-stealth` pinned to `<3.0.0` — the `Stealth().apply_stealth_sync(page)` API is confirmed working on `2.x`. Major version upgrades may break the call signature.

---

## Invocation

```bash
uv run --directory ~/.claude/skills/licensing/gartner-pi python gartner.py segment-list
uv run --directory ~/.claude/skills/licensing/gartner-pi python gartner.py segment cloud-erp
uv run --directory ~/.claude/skills/licensing/gartner-pi python gartner.py product "SAP S/4HANA"

# Force live fetch, do not use cache:
uv run --directory ~/.claude/skills/licensing/gartner-pi python gartner.py segment-list --refresh
```

---

## Out of Scope

- Writing or posting anything to Gartner
- Authentication / logged-in sessions
- Fetching individual reviews
- Any non-Gartner market intelligence source
