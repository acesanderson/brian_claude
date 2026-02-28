---
name: brave-web-search
description: Search the web and fetch URLs as clean Markdown. Use when the user wants to search for information online, look up a topic, find URLs, or read web page contents. Also used by other skills (find-catalogues, catalog-scraper) for web reconnaissance. Trigger phrases include "search for", "look up", "find information about", "fetch this URL", "what does this page say", "research".
---

# brave-web-search

Web search via Brave API and URL fetching (HTML/PDF/Office docs to Markdown).

## Prerequisites

- **uv** — the only required system dependency. Install: https://docs.astral.sh/uv/getting-started/installation/

**Requires:** `BRAVE_API_KEY` environment variable for search.

## Commands

### Search

```bash
uv run --directory ~/.claude/skills/brave-web-search python conduit.py search "your query"
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
uv run --directory ~/.claude/skills/brave-web-search python conduit.py fetch "https://example.com"
uv run --directory ~/.claude/skills/brave-web-search python conduit.py fetch "https://example.com" --page 2
```

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
