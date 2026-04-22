---
name: firecrawl
description: Web scraping, crawling, and structured data extraction via self-hosted Firecrawl. ALWAYS use this skill when the user needs to scrape a URL, crawl a website, discover all URLs on a site (map), do a web search with full content retrieval, batch-scrape multiple URLs, or extract structured data from web pages using an LLM. Invoke before any curl/requests-based scraping attempt — Firecrawl handles JS rendering and anti-bot measures automatically.
---

Firecrawl is running at `http://172.16.0.4:3002`. All operations go through the CLI at `~/.claude/skills/firecrawl/scripts/fc.py`.

**Invoke pattern:** `uv run ~/.claude/skills/firecrawl/scripts/fc.py <verb> <args>`

All output is JSON to stdout. Errors go to stderr with a non-zero exit code.

## Quick reference

| Goal | Command |
|------|---------|
| Scrape one URL | `fc scrape <url>` |
| Scrape + extract structured data | `fc scrape <url> --prompt "..."` or `--schema '{...}'` |
| Crawl a site | `fc crawl <url> --limit 50` |
| List all URLs on a site | `fc map <url>` |
| Web search | `fc search "<query>"` |
| Web search + scrape results | `fc search "<query>" --scrape` |
| Scrape many URLs at once | `fc batch <url1> <url2> ...` |
| LLM extraction across URLs | `fc extract <url1> <url2> --prompt "..."` |
| Check async job | `fc status crawl|batch|extract <job-id>` |
| Cancel a crawl | `fc cancel <job-id>` |

Alias for brevity in your shell: `alias fc='uv run ~/.claude/skills/firecrawl/scripts/fc.py'`

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `FIRECRAWL_URL` | `http://172.16.0.4:3002` | Server base URL |
| `FIRECRAWL_API_KEY` | _(empty)_ | API key if auth is enabled |

## Verbs

### scrape
Fetches a single URL. Returns a JSON envelope containing the page content in the requested format.

```bash
# Plain markdown (default)
uv run ~/.claude/skills/firecrawl/scripts/fc.py scrape https://example.com

# HTML instead
uv run ~/.claude/skills/firecrawl/scripts/fc.py scrape https://example.com -f html

# LLM extraction — returns { data: { ... } } matching your schema
uv run ~/.claude/skills/firecrawl/scripts/fc.py scrape https://shop.example.com \
  --schema '{"type":"object","properties":{"price":{"type":"number"},"title":{"type":"string"}}}'

# Or just a prompt
uv run ~/.claude/skills/firecrawl/scripts/fc.py scrape https://example.com \
  --prompt "Extract the author, publish date, and main thesis"
```

Key options: `--format markdown|html|rawHtml|links|screenshot`, `--only-main/--no-only-main`, `--wait-for <ms>` (JS rendering delay), `--schema <json>`, `--prompt <text>`.

Access the content: `.data.markdown` or `.data.json` (when using LLM extraction).

### crawl
Recursively follows links from a start URL, scraping each page. Async — polls until complete by default.

```bash
# Crawl up to 100 pages
uv run ~/.claude/skills/firecrawl/scripts/fc.py crawl https://docs.example.com

# Only blog posts, max 3 levels deep
uv run ~/.claude/skills/firecrawl/scripts/fc.py crawl https://example.com \
  --include 'blog/.*' --depth 3 --limit 200

# Fire and forget — get job ID immediately
uv run ~/.claude/skills/firecrawl/scripts/fc.py crawl https://example.com --no-wait
```

Key options: `--limit N`, `--depth N`, `--include <regex>`, `--exclude <regex>`, `--wait/--no-wait`, `--poll-timeout <secs>`.

Results are in `.data[]` — each item has `.markdown`, `.url`, `.metadata`.

### map
Returns the full URL list from a site without scraping page content. Much faster than crawl when you only need URLs.

```bash
uv run ~/.claude/skills/firecrawl/scripts/fc.py map https://example.com

# Filter to pricing-related URLs
uv run ~/.claude/skills/firecrawl/scripts/fc.py map https://example.com --search pricing

# Pipe into batch scrape
uv run ~/.claude/skills/firecrawl/scripts/fc.py map https://example.com \
  | jq -r '.links[]' \
  | head -20 \
  | xargs uv run ~/.claude/skills/firecrawl/scripts/fc.py batch
```

Key options: `--limit N`, `--include <regex>`, `--exclude <regex>`, `--search <term>`.

URLs are in `.links[]`.

### search
Runs a web search and optionally scrapes the full content of each result.

```bash
# Metadata only (fast)
uv run ~/.claude/skills/firecrawl/scripts/fc.py search "python async best practices" --limit 10

# Full content of each result
uv run ~/.claude/skills/firecrawl/scripts/fc.py search "firecrawl API docs" --scrape

# Google operators work
uv run ~/.claude/skills/firecrawl/scripts/fc.py search "site:github.com firecrawl" --scrape
```

Key options: `--limit N`, `--scrape/--no-scrape`, `--format <fmt>`.

Results are in `.data[]`, each with `.url`, `.title`, `.description`, and `.markdown` (if `--scrape`).

### batch
Scrapes multiple URLs in parallel as a single async job. More efficient than looping over `scrape`.

```bash
uv run ~/.claude/skills/firecrawl/scripts/fc.py batch \
  https://a.com https://b.com https://c.com

# From a file
uv run ~/.claude/skills/firecrawl/scripts/fc.py batch $(cat urls.txt)

# No wait — get job ID for later
uv run ~/.claude/skills/firecrawl/scripts/fc.py batch https://a.com https://b.com --no-wait
```

Key options: same as `scrape` minus per-URL options; `--wait/--no-wait`.

Results in `.data[]`, keyed by URL.

### extract
Uses Firecrawl's LLM pipeline to pull structured data from one or more URLs. Good for pulling consistent fields across many pages (product specs, author bios, pricing tables, etc.).

```bash
# Single URL, prompt-driven
uv run ~/.claude/skills/firecrawl/scripts/fc.py extract https://example.com/product \
  --prompt "get product name, price, and availability"

# Schema-driven across multiple pages
uv run ~/.claude/skills/firecrawl/scripts/fc.py extract \
  https://a.com/product https://b.com/product \
  --schema '{"type":"object","properties":{"name":{"type":"string"},"price":{"type":"number"}}}'
```

Key options: `--schema <json>`, `--prompt <text>`, `--system-prompt <text>`, `--wait/--no-wait`.

### status / cancel

```bash
# Check an async job
uv run ~/.claude/skills/firecrawl/scripts/fc.py status crawl <job-id>
uv run ~/.claude/skills/firecrawl/scripts/fc.py status batch <job-id>
uv run ~/.claude/skills/firecrawl/scripts/fc.py status extract <job-id>

# Cancel a running crawl
uv run ~/.claude/skills/firecrawl/scripts/fc.py cancel <job-id>
```

## Agentic patterns

**Extract markdown from a scrape:**
```bash
uv run ~/.claude/skills/firecrawl/scripts/fc.py scrape https://example.com \
  | jq -r '.data.markdown'
```

**Crawl docs, collect all markdown:**
```bash
uv run ~/.claude/skills/firecrawl/scripts/fc.py crawl https://docs.example.com --limit 50 \
  | jq '[.data[].markdown]'
```

**Map → filter → batch scrape:**
```bash
uv run ~/.claude/skills/firecrawl/scripts/fc.py map https://example.com \
  | jq -r '.links[] | select(contains("/blog/"))' \
  | xargs uv run ~/.claude/skills/firecrawl/scripts/fc.py batch
```

**Search and read top result:**
```bash
uv run ~/.claude/skills/firecrawl/scripts/fc.py search "firecrawl docs" --scrape --limit 1 \
  | jq -r '.data[0].markdown'
```

**Extract structured data into a variable:**
```bash
DATA=$(uv run ~/.claude/skills/firecrawl/scripts/fc.py extract https://example.com/pricing \
  --prompt "list all plan names and monthly prices as an array")
echo "$DATA" | jq '.data'
```

## Proxy / bot protection

The `--proxy` flag is available on `scrape`, `crawl`, and `batch`:

```bash
fc scrape <url> --proxy stealth
fc batch <url1> <url2> --proxy stealth
fc crawl <url> --proxy stealth
```

| Tier | Behavior |
|------|----------|
| `basic` | Default — direct request with Firecrawl's built-in headers |
| `stealth` | **TBD** — requires Oxylabs to be connected to the Firecrawl server at `172.16.0.4:3002`. The flag is wired and will be sent to the API, but requests will fall back to basic until Oxylabs is configured. |

Symptom of needing stealth: pages return "Vercel Security Checkpoint" or similar bot-wall HTML (~105 chars) instead of real content.

## Polling behavior

Async verbs (`crawl`, `batch`, `extract`) default to `--wait` mode: they post the job then poll `GET /v1/{verb}/{id}` every 2 seconds until the status is `completed`, `failed`, or `cancelled`. Use `--poll-timeout <secs>` (default 300) to adjust the ceiling. Pass `--no-wait` to return immediately with a `job_id`.

## Prerequisites

- `uv` — https://docs.astral.sh/uv/getting-started/installation/
- Firecrawl server running at `FIRECRAWL_URL` (default: `http://172.16.0.4:3002`)
