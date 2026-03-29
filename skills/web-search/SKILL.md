---
name: web-search
description: Search the web and fetch URLs as clean Markdown. Use when the user wants to search for information online, look up a topic, find URLs, or read web page contents. Also used by other skills (find-catalogues, catalog-scraper) for web reconnaissance. Trigger phrases include "search for", "look up", "find information about", "fetch this URL", "what does this page say", "research".
---

# web-search

Web search via Brave API and URL fetching (HTML/PDF/Office docs to Markdown). Also provides Exa neural/semantic search, content extraction, similarity search, and grounded Q&A.

## Prerequisites

- **uv** — the only required system dependency. Install: https://docs.astral.sh/uv/getting-started/installation/

**Requires:** `BRAVE_API_KEY` for Brave search. `EXA_API_KEY` for all Exa commands.

**Optional (proxy):** `OXY_NAME` and `OXY_PASSWORD` — needed only when using `--proxy`.

## Commands

### Search

```bash
uv run --directory ~/.claude/skills/web-search python conduit.py search "your query"
```

**stdout (JSON):**
```json
{
  "result": "[1] Title: ...\n    URL: ...\n    Snippet: ...\n---\n[2] ...",
  "next_step_hint": "Use fetch to see full page content."
}
```

Returns top 5 results.

### Fetch URL

```bash
uv run --directory ~/.claude/skills/web-search python conduit.py fetch "https://example.com"
uv run --directory ~/.claude/skills/web-search python conduit.py fetch "https://example.com" --page 2
uv run --directory ~/.claude/skills/web-search python conduit.py fetch "https://example.com" --proxy
uv run --directory ~/.claude/skills/web-search python conduit.py fetch "https://example.com" --browser
```

- `--proxy`: routes plain HTTP fetch through Oxylabs residential proxy. Requires `OXY_NAME` and `OXY_PASSWORD`.
- `--browser`: uses Playwright + Oxylabs + stealth for JS-rendered/heavily bot-protected pages (e.g. Gartner). Requires `OXY_NAME` and `OXY_PASSWORD`. Slower (~15s), use only when needed.

**stdout (JSON):**
```json
{
  "metadata": {
    "url": "https://example.com",
    "current_page": 1,
    "total_pages": 3,
    "total_characters": 24000,
    "is_truncated": true
  },
  "table_of_contents": [{"text": "## Section", "line": 12}],
  "content": "..."
}
```

Supports HTML, PDF, DOCX, PPTX, XLSX.

## Notes

- Errors go to stderr as `{"error": "..."}` with exit code 1
- If `is_truncated` is `true`, continue reading with `--page N`

---

## Choosing between Brave and Exa search

`conduit.py search` uses Brave's keyword/BM25 index — best when you know the exact terms,
title, or phrasing. `exa.py search` uses a neural embedding index — best when your query
describes a concept or argument and the relevant documents may not use your exact words.
Use `exa.py answer` for direct factual questions that need a current, cited answer rather
than a document list.

---

## Exa

Semantic search via Exa's neural index. Requires `EXA_API_KEY` env var.

### Commands

**Search** — semantic/neural web search:
```bash
uv run --directory ~/.claude/skills/web-search python exa.py search "your query"
uv run --directory ~/.claude/skills/web-search python exa.py search "arxiv papers on RLHF" --category "research paper" --num-results 5
uv run --directory ~/.claude/skills/web-search python exa.py search "recent AI news" --start-date 2025-01-01 --text
```

**Contents** — fetch full content from known URLs:
```bash
uv run --directory ~/.claude/skills/web-search python exa.py contents https://arxiv.org/abs/2307.06435
uv run --directory ~/.claude/skills/web-search python exa.py contents https://url1.com https://url2.com --text
```

**Similar** — find pages semantically similar to a seed URL:
```bash
uv run --directory ~/.claude/skills/web-search python exa.py similar https://arxiv.org/abs/2307.06435 --num-results 10
```

> Seed URL must point to a page with substantive text content. Homepages of JS-heavy
> apps and thin landing pages have no usable embedding — use a specific article, paper,
> or post URL instead.

**Answer** — grounded Q&A with citations:
```bash
uv run --directory ~/.claude/skills/web-search python exa.py answer "What is the current Fed funds rate?"
```

### Flags

| Flag | Applies to | Default | Description |
|---|---|---|---|
| `--highlights` | search, contents, similar | yes (default) | Token-efficient excerpts |
| `--text` | search, contents, similar | no | Full page markdown |
| `--max-chars INT` | search, contents, similar | 4000 | Cap on content length |
| `--num-results INT` | search, similar | 10 | Results count (1-100) |
| `--category STR` | search | — | Content type filter |
| `--start-date YYYY-MM-DD` | search, similar | — | Published after |
| `--end-date YYYY-MM-DD` | search, similar | — | Published before |
| `--include-domains` | search | — | Allowlist domains |
| `--exclude-domains` | search | — | Blocklist domains |

Valid categories: `company`, `financial report`, `news`, `people`, `personal site`, `research paper`, `tweet`

### Output

All commands print JSON to stdout on success. Errors go to stderr as `{"error": "..."}` with exit code 1.
