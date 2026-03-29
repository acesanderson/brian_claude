# Exa CLI — Design Document
_2026-03-18_

---

## 1. Goal

Add an `exa` CLI to the `web-search` skill that exposes Exa's four REST endpoints (`/search`, `/contents`, `/findSimilar`, `/answer`) as subcommands. The new CLI follows the identical structural conventions as the existing `conduit.py` / `fetch_tools.py` pair: async logic in a module, thin CLI entry point, JSON to stdout, errors to stderr, exit code 1 on failure.

---

## 2. Constraints and Non-Goals

**In scope:**
- `exa search`, `exa contents`, `exa similar`, `exa answer` subcommands
- `AsyncExa` from the `exa-py` SDK as the sole client — no raw `httpx` calls to Exa endpoints
- `EXA_API_KEY` read from environment; no key management logic
- Output: newline-terminated JSON to stdout; `{"error": "..."}` to stderr on failure, exit code 1
- `pyproject.toml` updated with `exa-py>=1.0.0` (pinned to major version)
- SKILL.md updated to document the new commands

**Not in scope — do not implement these:**
- `summary` content mode — excluded; adds an LLM call on Exa's end; Claude is the summarizer
- `type` parameter (`auto`/`fast`/`instant`/`deep`/`deep-reasoning`) — excluded; `auto` is always used
- Deep search (`type="deep"` or `type="deep-reasoning"`) — excluded; 5–60s latency is incompatible with inline CLI use
- `output_schema` structured extraction — excluded
- `subpages` crawling — excluded
- `extras.links` / `extras.imageLinks` — excluded
- `maxAgeHours` / `livecrawlTimeout` — excluded; Exa's cache defaults are acceptable
- `userLocation` — excluded
- `includeText` / `excludeText` string filters — excluded
- `--num-results` on `exa contents` — does not apply; contents takes explicit URLs
- `--api-key` CLI flag — env var only; no key management
- Pagination of Exa results — Exa returns all results in one response
- Caching or deduplication of results
- Rate-limit retry logic — Exa SDK handles internally
- Logging to file or `logging` module configuration
- Any change to `conduit.py`, `fetch_tools.py`, or Brave search behavior
- Interactive / streaming output modes
- Passing through SDK response fields not listed in the output shapes below: `requestId`, `costDollars`, `image`, `favicon`, `highlightScores`, `id` (Exa internal doc ID) — all are stripped before output

---

## 3. Interface Contracts

### CLI entry point: `exa.py`

```
uv run --directory ~/.claude/skills/web-search python exa.py <subcommand> [options]
```

**Subcommands and flags:**

```
exa search <query>
    [--num-results INT]          default: 10, range 1–100
    [--category STR]             company|people|research paper|news|tweet|personal site|financial report
    [--include-domains STR...]   one or more domains (nargs='+')
    [--exclude-domains STR...]   one or more domains (nargs='+')
    [--start-date YYYY-MM-DD]    maps to startPublishedDate
    [--end-date YYYY-MM-DD]      maps to endPublishedDate
    [--text]                     return full page text; mutually exclusive with --highlights
    [--highlights]               return highlights (this is also the default when neither flag is passed)
    [--max-chars INT]            default: 4000; applies to whichever content mode is active

exa contents <url> [<url>...]    (nargs='+', min 1)
    [--text]                     mutually exclusive with --highlights
    [--highlights]               default when neither flag is passed
    [--max-chars INT]            default: 4000

exa similar <url>
    [--num-results INT]          default: 10, range 1–100
    [--text]                     mutually exclusive with --highlights
    [--highlights]               default when neither flag is passed
    [--max-chars INT]            default: 4000
    [--start-date YYYY-MM-DD]
    [--end-date YYYY-MM-DD]

exa answer <question>
```

**Content mode rule:** When neither `--text` nor `--highlights` is passed, the implementation MUST request highlights from the Exa SDK with `max_characters=4000`. This is not a fallback — it is the explicit default. The `--highlights` flag exists only to allow the caller to be explicit; passing it is equivalent to passing nothing.

### Logic module: `exa_tools.py`

All functions are `async def` and use `AsyncExa` from `exa_py`. The `Exa` (sync) class must not be used.

```python
async def exa_search(
    query: str,
    num_results: int = 10,
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_date: str | None = None,   # YYYY-MM-DD string, converted to ISO 8601 before SDK call
    end_date: str | None = None,     # YYYY-MM-DD string, converted to ISO 8601 before SDK call
    use_text: bool = False,          # True = text mode; False = highlights mode
    max_chars: int = 4000,
) -> dict[str, Any]: ...

async def exa_contents(
    urls: list[str],                 # min length 1, enforced by caller
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]: ...

async def exa_similar(
    url: str,
    num_results: int = 10,
    use_text: bool = False,
    max_chars: int = 4000,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]: ...

async def exa_answer(question: str) -> dict[str, Any]: ...
```

### Output shapes

**`exa_search` / `exa_similar` — highlights mode (default):**
```json
{
  "results": [
    {
      "title": "...",
      "url": "...",
      "published_date": "2023-11-16T01:36:32.547Z",
      "author": "Jane Smith",
      "highlights": ["excerpt one", "excerpt two"]
    }
  ]
}
```

**`exa_search` / `exa_similar` — text mode (`--text`):**
```json
{
  "results": [
    {
      "title": "...",
      "url": "...",
      "published_date": "2023-11-16T01:36:32.547Z",
      "author": "Jane Smith",
      "text": "full page content as markdown..."
    }
  ]
}
```

Rules:
- `highlights` key is present only in highlights mode; `text` key is present only in text mode. Never both.
- `published_date`: omit the key entirely if absent in SDK response (do not include as `null`)
- `author`: omit the key entirely if absent in SDK response (do not include as `null`)
- `title`: include as empty string `""` if absent

**`exa_contents` — highlights mode (default):**
```json
{
  "results": [
    {
      "url": "...",
      "title": "...",
      "highlights": ["excerpt one"]
    }
  ],
  "failed_urls": ["https://example.com/uncrawlable"]
}
```

**`exa_contents` — text mode:**
```json
{
  "results": [
    {
      "url": "...",
      "title": "...",
      "text": "full page content..."
    }
  ],
  "failed_urls": []
}
```

Rules:
- `failed_urls` key is ALWAYS present (empty list if all URLs succeeded)
- If ALL URLs fail: return `{"results": [], "failed_urls": [...]}` with exit 0, not exit 1. The caller decides whether empty results are an error.
- `highlights` / `text` mutual exclusion applies identically to search

**`exa_answer` success:**
```json
{
  "answer": "The current Fed funds rate is...",
  "citations": [
    {"url": "...", "title": "...", "published_date": "..."}
  ]
}
```

Rules:
- `citations`: always present as a list; may be empty
- `answer`: always a string; may be empty string — this is NOT an error (exit 0)
- `published_date` in citations: omit if absent, same rule as results

**All failure cases:**
```json
{"error": "..."}
```
Printed to stderr, exit code 1.

---

## 4. Acceptance Criteria

Tests that require a live `EXA_API_KEY` are marked **[integration]**. Tests that do not are marked **[unit]**.

- **[integration]** `python exa.py search "papers on RLHF and calibration" --category "research paper"` exits 0, stdout is valid JSON, the JSON has a `results` key that is a list, and every item in the list has `url` (string) and `highlights` (list of strings). The `text` key must not appear on any result.
- **[integration]** `python exa.py search "test query" --text` exits 0, every result has a `text` key (string), and no result has a `highlights` key.
- **[integration]** `python exa.py search "test query" --num-results 3` exits 0 and `len(results) <= 3`.
- **[integration]** `python exa.py contents https://arxiv.org/abs/2307.06435` exits 0, `results[0].url == "https://arxiv.org/abs/2307.06435"`, and `failed_urls` key is present.
- **[integration]** `python exa.py similar https://arxiv.org/abs/2307.06435 --num-results 5` exits 0 and `len(results) <= 5`.
- **[integration]** `python exa.py answer "What is 2+2?"` exits 0, `answer` key is a string, `citations` key is a list.
- **[unit]** `EXA_API_KEY` unset: any subcommand exits 1 and stderr is valid JSON matching `{"error": "Missing EXA_API_KEY environment variable"}`.
- **[unit]** `--category blorp` exits 1, stderr contains `{"error": "Invalid category: blorp..."}`, no network call is made.
- **[unit]** `--start-date 2024-13-01` exits 1, stderr contains `{"error": "Invalid date format..."}`, no network call is made.
- **[unit]** `--start-date 2024-06-01 --end-date 2024-01-01` exits 1 (start after end), no network call is made.
- **[unit]** `--text --highlights` exits 1, stderr contains `{"error": "--text and --highlights are mutually exclusive"}`.
- **[unit]** `--num-results 0` and `--num-results 101` both exit 1 with error on stderr.
- **[unit]** `python exa.py similar not-a-url` exits 1 with error on stderr.
- **[unit]** `exa.py` contains no import of `fetch_tools` (statically verifiable with `grep`).
- **[unit]** `uv run --directory ~/.claude/skills/web-search python exa.py --help` exits 0 (confirms package installation resolves).

---

## 5. Error Handling / Failure Modes

| Failure | Detection point | Output |
|---|---|---|
| `EXA_API_KEY` not set | top of each `exa_tools` function, before `AsyncExa` instantiation | `{"error": "Missing EXA_API_KEY environment variable"}` → stderr, exit 1 |
| `exa-py` not installed / ImportError | top of `exa.py`, in a `try/except ImportError` block | `{"error": "exa-py not installed. Run: uv sync --directory ~/.claude/skills/web-search"}` → stderr, exit 1 |
| Invalid `--category` | `exa.py` arg validation, before tool call | `{"error": "Invalid category: <val>. Must be one of: company, people, ..."}` → stderr, exit 1 |
| Invalid date format | `exa.py` arg validation, before tool call | `{"error": "Invalid date format: <val>. Expected YYYY-MM-DD"}` → stderr, exit 1 |
| `--start-date` after `--end-date` | `exa.py` arg validation, before tool call | `{"error": "start-date must be before or equal to end-date"}` → stderr, exit 1 |
| `--text` and `--highlights` both passed | `exa.py` arg validation | `{"error": "--text and --highlights are mutually exclusive"}` → stderr, exit 1 |
| `--num-results` out of range | `exa.py` arg validation | `{"error": "--num-results must be between 1 and 100"}` → stderr, exit 1 |
| `exa similar` given a non-URL string | `exa.py` arg validation | `{"error": "Invalid URL: must start with http:// or https://"}` → stderr, exit 1 |
| Exa API 401 Unauthorized | `exa_tools`, catch SDK auth exception | `{"error": "Exa authentication failed. Check EXA_API_KEY."}` → stderr, exit 1 |
| Exa API other HTTP error (4xx/5xx) | `exa_tools`, catch SDK HTTP exception | `{"error": "Exa API error <status>: <message>"}` → stderr, exit 1 |
| Network timeout | `exa_tools`, catch `TimeoutError` / SDK timeout | `{"error": "Request timed out calling Exa <endpoint>"}` → stderr, exit 1 |
| No network connectivity | `exa_tools`, catch `ConnectionError` / `OSError` | `{"error": "Network error calling Exa <endpoint>: <msg>"}` → stderr, exit 1 |
| Empty result set from search/similar | not an error | `{"results": []}` → stdout, exit 0 |
| All URLs fail in `exa contents` | not an error | `{"results": [], "failed_urls": [...]}` → stdout, exit 0 |
| `exa answer` returns empty string | not an error | `{"answer": "", "citations": [...]}` → stdout, exit 0 |
| Duplicate URLs in `exa contents` | `exa.py` arg validation — deduplicate before calling tool; do not error | deduped list passed to `exa_contents` |

---

## 6. Code Example (Conventions to Follow)

```python
# exa.py — entry point pattern
from __future__ import annotations

import argparse
import asyncio
import json
import sys

try:
    from exa_tools import exa_search
except ImportError:
    print(
        json.dumps({"error": "exa-py not installed. Run: uv sync --directory ~/.claude/skills/web-search"}),
        file=sys.stderr,
    )
    sys.exit(1)


VALID_CATEGORIES = {
    "company", "people", "research paper", "news",
    "tweet", "personal site", "financial report",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Exa semantic search CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    search_p = sub.add_parser("search")
    search_p.add_argument("query")
    search_p.add_argument("--num-results", type=int, default=10)
    search_p.add_argument("--category", default=None)
    search_p.add_argument("--text", action="store_true", default=False)
    search_p.add_argument("--highlights", action="store_true", default=False)
    search_p.add_argument("--max-chars", type=int, default=4000)

    args = parser.parse_args()

    # All validation before any network call
    if args.command == "search":
        if args.text and args.highlights:
            _fail("--text and --highlights are mutually exclusive")
        if args.category and args.category not in VALID_CATEGORIES:
            _fail(f"Invalid category: {args.category}. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}")
        if not 1 <= args.num_results <= 100:
            _fail("--num-results must be between 1 and 100")
        result = asyncio.run(exa_search(args.query, num_results=args.num_results, use_text=args.text))

    if "error" in result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result))


def _fail(message: str) -> None:
    print(json.dumps({"error": message}), file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
```

```python
# exa_tools.py — logic pattern
from __future__ import annotations

import os
from typing import Any

from exa_py import AsyncExa  # AsyncExa, not Exa — never use the sync client


async def exa_search(
    query: str,
    num_results: int = 10,
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return {"error": "Missing EXA_API_KEY environment variable"}

    async with AsyncExa(api_key=api_key) as client:
        contents = {"text": {"max_characters": max_chars}} if use_text else {"highlights": {"max_characters": max_chars}}
        response = await client.search(query, num_results=num_results, contents=contents)

    return {"results": [_shape_result(r, use_text) for r in response.results]}


def _shape_result(r: Any, use_text: bool) -> dict[str, Any]:
    """Strip SDK fields not in the output contract; omit null optional fields."""
    out: dict[str, Any] = {"title": r.title or "", "url": r.url}
    if r.published_date:
        out["published_date"] = r.published_date
    if r.author:
        out["author"] = r.author
    if use_text:
        out["text"] = r.text or ""
    else:
        out["highlights"] = r.highlights or []
    return out
```

---

## 7. Domain Language

These are the exact nouns the implementation is allowed to use. Do not invent synonyms.

| Term | Meaning |
|---|---|
| **query** | The natural language string passed to `/search` or `/answer` |
| **result** | A single item returned by `/search` or `/findSimilar`; always has `url` and `title` |
| **highlights** | Token-efficient key excerpts extracted by Exa from a page, relevant to the query |
| **text** | Full page content returned as markdown |
| **citation** | A source object returned by `/answer`: `{url, title, published_date?}` |
| **category** | An Exa content-type filter string (e.g. `"research paper"`, `"news"`) |
| **start_date / end_date** | YYYY-MM-DD strings bounding `publishedDate` on results (converted to ISO 8601 before SDK call) |
| **answer** | The synthesized response string from `/answer`; may be empty |
| **failed_urls** | List of URL strings that `exa_contents` could not retrieve; always present in `exa contents` output |

**Prohibited synonyms:** do not use `document`, `article`, `item`, `hit`, `match`, `link`, `webpage`, `source` (except inside `citation`), `snippet` (use `highlights`), `summary` (reserved, not implemented).

---

## 8. Invalid State Transitions

All of the following must raise an error in `exa.py` before any network call is made. None may be silently ignored or defaulted around.

- `--text` and `--highlights` both present → error
- `--num-results` < 1 or > 100 → error
- `--start-date` after `--end-date` (chronologically) → error
- `--start-date` or `--end-date` not matching `YYYY-MM-DD` regex `^\d{4}-\d{2}-\d{2}$` → error (do not attempt `datetime.strptime` and catch — validate format first, then parse)
- `--category` not in `VALID_CATEGORIES` → error
- `exa contents` called with zero URL arguments → error (argparse `nargs='+'` enforces; document it)
- `exa similar` called with a string not starting with `http://` or `https://` → error
- `EXA_API_KEY` env var absent → error returned from tool function (not raised as exception)
