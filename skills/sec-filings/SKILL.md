---
name: sec_edgar_api
description: Fetches annual and quarterly reports (10-K, 10-Q, 20-F) from SEC EDGAR using stock tickers.
---

# SEC Filings Skill

Fetch annual and quarterly reports (10-K, 10-Q, 20-F) from the SEC EDGAR database.

## Prerequisites

- **uv** — the only required system dependency. Install: https://docs.astral.sh/uv/getting-started/installation/

## Usage

Write a script that imports from the skill's `scripts/` directory, then run it with `uv`:

```bash
uv run --with httpx --with markdownify python your_script.py
```

In `your_script.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/sec-filings/scripts"))
from sec_filings import get_filings, get_latest_filing, FilingType
```

## Core Functions

### `get_latest_filing(ticker: str, filing_type: FilingType) -> Filing`
Returns the most recent filing of the specified type.

### `get_filings(ticker: str, filing_type: FilingType, limit: int = 5) -> list[Filing]`
Returns recent filings of the specified type.

### `Filing.get_content(page: int = 1) -> FilingContent`
Returns paginated filing content as markdown.

## Filing Types

| Type | Form | Description |
|------|------|-------------|
| `FilingType.ANNUAL` | 10-K | Annual report (US domestic) |
| `FilingType.ANNUAL_FOREIGN` | 20-F | Annual report (foreign issuers) |
| `FilingType.QUARTERLY` | 10-Q | Quarterly report (US domestic) |

## Critical: Recency

**Always default to the latest filing unless the user explicitly requests a specific period.**

**Before fetching any filing, read today's date from the `currentDate` value injected into the system context.** This tells you what filing periods are realistically available. For example:
- If today is February 2026, a company's FY2025 10-K may not yet be filed (typically filed Feb–April), so the latest available is likely FY2024.
- If today is August 2026, FY2025 10-K filings are almost certainly available.

Never guess or assume the current year from training data — use the injected `currentDate`.

LLM knowledge cutoffs make it easy to hallucinate outdated financials. The filing date returned by the API is always authoritative — use it, not memory:

```python
filing = get_latest_filing("AAPL", FilingType.ANNUAL)
print(f"Filing date: {filing.date}")  # Use this, not training data
```

When comparing periods, fetch both filings explicitly rather than relying on memory:

```python
filings = get_filings("AAPL", FilingType.QUARTERLY, limit=2)
q_current = filings[0]  # Most recent
q_previous = filings[1]  # Prior quarter
```

## Pagination

SEC filings are large (10-Ks often exceed 100,000 characters). Content is paginated at ~8000 characters per page.

```python
content = filing.get_content(page=1)
print(content.metadata)  # {'current_page': 1, 'total_pages': 15, ...}
print(content.table_of_contents)  # List of markdown headings with line numbers
print(content.text)  # Page content
```

### Navigation Strategy

1. **Start with page 1** to get the table of contents
2. **Use TOC headings** to estimate which page contains the section you need
3. **Jump to specific pages** rather than reading sequentially

Common 10-K sections:
- Business (Item 1)
- Risk Factors (Item 1A)
- MD&A (Item 7)
- Financial Statements (Item 8)

## Ticker Resolution

This skill requires stock tickers, not company names. If the user provides a company name:

1. Ask them to confirm the ticker
2. Or use web search to find the ticker first

If `get_latest_filing` raises `TickerNotFoundError`, inform the user:
- The ticker may be incorrect
- The company may not be publicly traded
- Foreign companies may use different exchanges (check ADR tickers)

## Error Handling

```python
from sec_filings import TickerNotFoundError, NoFilingsError

try:
    filing = get_latest_filing("INVALID", FilingType.ANNUAL)
except TickerNotFoundError:
    # Ticker not in SEC database - ask user to verify
except NoFilingsError:
    # Ticker valid but no filings of this type exist
```

## Dependencies

- `httpx`
- `markdownify`

Both are installed automatically by `uv` when you run your script with `--with httpx --with markdownify`. No manual installation needed.

## Example Workflow

User asks: "What were Duolingo's risk factors in their latest annual report?"

```python
# 0. Note today's date from the system context (currentDate) to reason about
#    which fiscal year is likely the most recent available before fetching.

# 1. Get the latest 10-K
filing = get_latest_filing("DUOL", FilingType.ANNUAL)
print(f"Using {filing.form} filed {filing.date}")

# 2. Get first page for TOC
content = filing.get_content(page=1)

# 3. Find "Risk Factors" in TOC, estimate page
# 4. Fetch that page range
# 5. Extract and summarize risk factors
```

Always state the filing date when presenting information to the user.


