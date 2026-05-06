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
| Check async job | `fc status crawl\|batch\|extract <job-id>` |
| Cancel a crawl | `fc cancel <job-id>` |
| Screenshot a rendered page | `fc playwright screenshot <url> -o out.png` |
| Get JS-rendered HTML | `fc playwright content <url>` |
| Run arbitrary Playwright code | `fc playwright fn --code 'async function handler({page}) {...}'` |

Alias for brevity in your shell: `alias fc='uv run ~/.claude/skills/firecrawl/scripts/fc.py'`

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `FIRECRAWL_URL` | `http://172.16.0.4:3002` | Firecrawl server base URL |
| `FIRECRAWL_API_KEY` | _(empty)_ | API key if auth is enabled |
| `BROWSERLESS_URL` | `http://172.16.0.4:3003` | Browserless server base URL (for `playwright` verb) |
| `BROWSERLESS_TOKEN` | `headwater` | Auth token for browserless |

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

### agent
Natural-language browser automation. Describe a task in plain English; Firecrawl drives Playwright autonomously via LLM (routed through bywater on this instance). Async — polls until complete by default.

```bash
# Basic task across the web
uv run ~/.claude/skills/firecrawl/scripts/fc.py agent \
  "find all blog posts about vector databases on qdrant.tech"

# Constrain to specific URLs + structured output
uv run ~/.claude/skills/firecrawl/scripts/fc.py agent \
  "extract all product names and prices" \
  --urls https://shop.example.com/products \
  --schema '{"type":"array","items":{"type":"object","properties":{"name":{"type":"string"},"price":{"type":"number"}}}}'

# Fire and forget
uv run ~/.claude/skills/firecrawl/scripts/fc.py agent \
  "summarize the top HN story" --urls https://news.ycombinator.com --no-wait
```

Key options: `--urls URL` (repeatable), `--schema JSON`, `--model spark-1-mini|spark-1-pro`, `--strict` (don't follow links), `--wait/--no-wait`.

Results are at `.data`. Uses `/v2/agent` endpoint.

### browser
Interact with a live browser session from a prior `fc scrape`. The session preserves cookies and localStorage across calls — the right tool for authenticated scraping. Sync — returns immediately.

```bash
# Step 1: scrape a page to open a browser session
SESSION=$(uv run ~/.claude/skills/firecrawl/scripts/fc.py scrape https://example.com/login \
  | jq -r '.data.metadata.scrapeId')

# Step 2: interact with the session using natural language
uv run ~/.claude/skills/firecrawl/scripts/fc.py browser $SESSION \
  --prompt "fill the email field with user@example.com and click Sign In"

# Or use Playwright code directly
uv run ~/.claude/skills/firecrawl/scripts/fc.py browser $SESSION \
  --code "await page.fill('#password', 's3cr3t'); await page.click('[type=submit]')" \
  --language node

# Step 3: close the session when done
uv run ~/.claude/skills/firecrawl/scripts/fc.py browser $SESSION --close
```

Key options: `--prompt TEXT` or `--code CODE` (mutually exclusive), `--language node|python|bash` (code mode only), `--timeout SECS` (1–300), `--close`.

Uses `/v2/scrape/{sessionId}/interact` endpoint.

### playwright
Direct Playwright automation via the self-hosted **browserless** service at `http://172.16.0.4:3003`. Three subcommands. Requires browserless running as a separate Docker service on caruana (see "Infrastructure" below).

```bash
# Screenshot — save to file
uv run ~/.claude/skills/firecrawl/scripts/fc.py playwright screenshot https://example.com -o page.png

# Screenshot — full page
uv run ~/.claude/skills/firecrawl/scripts/fc.py playwright screenshot https://example.com \
  --full-page --type jpeg -o full.jpg

# Rendered HTML after JS execution
uv run ~/.claude/skills/firecrawl/scripts/fc.py playwright content https://example.com \
  | jq -r '.html'

# Arbitrary Playwright code — auth flow example
uv run ~/.claude/skills/firecrawl/scripts/fc.py playwright fn --code 'async function handler({page}) {
  await page.goto("https://example.com/login");
  await page.fill("#email", "user@example.com");
  await page.fill("#password", "secret");
  await page.click("[type=submit]");
  await page.waitForNavigation();
  return { url: page.url(), title: await page.title() };
}'

# Run from a file
uv run ~/.claude/skills/firecrawl/scripts/fc.py playwright fn --code-file auth_flow.js
```

The `fn` subcommand is the key tool for authenticated scraping: load a page, interact with it across multiple steps, return whatever you need as JSON.

### status / cancel

```bash
# Check an async job
uv run ~/.claude/skills/firecrawl/scripts/fc.py status crawl <job-id>
uv run ~/.claude/skills/firecrawl/scripts/fc.py status batch <job-id>
uv run ~/.claude/skills/firecrawl/scripts/fc.py status extract <job-id>
uv run ~/.claude/skills/firecrawl/scripts/fc.py status agent <job-id>

# Cancel a running job
uv run ~/.claude/skills/firecrawl/scripts/fc.py cancel <job-id>               # crawl (default)
uv run ~/.claude/skills/firecrawl/scripts/fc.py cancel <job-id> --type agent  # agent
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
| `stealth` | Routes through Oxylabs residential proxy. Requires `PROXY_SERVER`, `PROXY_USERNAME`, and `PROXY_PASSWORD` set in the server's `.env` **and** a `PLAYWRIGHT_MICROSERVICE_URL` pointing to a running Playwright container. Without the Playwright service, stealth fails with `SCRAPE_RETRY_LIMIT / document_antibot` even on unprotected sites. |

**Server `.env` for Oxylabs:**
```
PROXY_SERVER=pr.oxylabs.io:7777
PROXY_USERNAME=customer-YOURNAME   # note: must include "customer-" prefix
PROXY_PASSWORD=yourpassword
PLAYWRIGHT_MICROSERVICE_URL=http://<playwright-host>:<port>
```

Symptom of needing stealth: pages return "Vercel Security Checkpoint" or similar bot-wall HTML (~105 chars) instead of real content.

Symptom of misconfigured proxy: `stealth` returns `SCRAPE_RETRY_LIMIT / document_antibot` on a page with no bot protection — the proxy is returning an auth error and Firecrawl misreads it as a bot wall. Check the `customer-` prefix on `PROXY_USERNAME` and verify credentials.

## Polling behavior

Async verbs (`crawl`, `batch`, `extract`) default to `--wait` mode: they post the job then poll `GET /v1/{verb}/{id}` every 2 seconds until the status is `completed`, `failed`, or `cancelled`. Use `--poll-timeout <secs>` (default 300) to adjust the ceiling. Pass `--no-wait` to return immediately with a `job_id`.

## Prerequisites

- `uv` — https://docs.astral.sh/uv/getting-started/installation/
- Firecrawl server running at `FIRECRAWL_URL` (default: `http://172.16.0.4:3002`)

## Infrastructure

### Browserless

Browserless is a separate Docker service on caruana, independent of the firecrawl stack.

**docker-compose:** `~/services/browserless/docker-compose.yml`
**Port:** 3003 (mapped to internal 3000)
**Token:** `headwater`

To manage:
```bash
ssh caruana "cd ~/services/browserless && docker compose up -d"
ssh caruana "cd ~/services/browserless && docker compose logs -f"
ssh caruana "docker compose -f ~/services/browserless/docker-compose.yml restart"
```

Health check: `curl "http://172.16.0.4:3003/pressure?token=headwater"`

**Important:** Browserless is NOT connected to firecrawl's `PLAYWRIGHT_MICROSERVICE_URL`. Firecrawl uses its own `playwright-service-ts` sidecar for that. Browserless is used only by `fc playwright`.

## Self-hosted limitations

`scrape`, `crawl`, `batch`, `search`, `map`, and `extract` all work on this instance (Playwright wired in via Docker Compose).

The following v2 verbs are **cloud-only** — the CLI commands exist and hit the right endpoints, but the self-hosted server will return 500:

| Feature | Blocker | Details |
|---------|---------|---------|
| `agent` verb | `EXTRACT_V3_BETA_URL` not set | Proxies to Firecrawl's proprietary cloud extract service (`/internal/extracts`). Not substitutable with a local LLM. |
| `browser` verb | Supabase not configured | Session lookup (`supabaseGetScrapeById`) requires Supabase to retrieve live browser state by scrapeId. |
| `scrape --action` | Fire Engine not enabled | `actions[]` requires Firecrawl's proprietary Fire Engine scraping layer (`SCRAPE_ACTIONS_NOT_SUPPORTED`). |

To use `agent` you would need access to Firecrawl's cloud (`EXTRACT_V3_BETA_URL` + `AGENT_INTEROP_SECRET`). To use `browser` you would need Supabase wired into the self-hosted deployment. Neither is easily self-hostable with the current firecrawl codebase.
