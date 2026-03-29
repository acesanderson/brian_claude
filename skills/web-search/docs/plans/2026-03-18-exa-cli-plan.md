# Exa CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `exa.py` and `exa_tools.py` to the `web-search` skill, exposing Exa's `/search`, `/contents`, `/findSimilar`, and `/answer` endpoints as a CLI with the same structural conventions as `conduit.py` / `fetch_tools.py`.

**Architecture:** `exa.py` is a thin CLI entry point (argparse, validation, dispatch, JSON output). `exa_tools.py` is the async logic module using `AsyncExa` from the `exa-py` SDK. Unit tests exercise argument validation without any network calls; integration tests exercise live Exa endpoints and are skipped if `EXA_API_KEY` is not set.

**Tech Stack:** Python 3.12, `exa-py>=1.0.0` (AsyncExa), `pytest>=8.0`, `uv` for dependency management and test running.

**Design doc:** `docs/plans/2026-03-18-exa-cli-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `exa_tools.py` | Create | Async logic: `exa_search`, `exa_contents`, `exa_similar`, `exa_answer`, `_shape_result` |
| `exa.py` | Create | CLI entry: argparse, validation, dispatch, JSON I/O |
| `tests/__init__.py` | Create | Empty — makes `tests/` a package |
| `tests/conftest.py` | Create | `run_exa()` helper used by all test files |
| `tests/test_unit.py` | Create | Unit tests (no network): AC-U1 through AC-U9 |
| `tests/test_integration.py` | Create | Integration tests (live API): AC-I1 through AC-I6 |
| `pyproject.toml` | Modify | Add `exa-py>=1.0.0`, `pytest>=8.0`, `pytest-asyncio>=0.23` |
| `SKILL.md` | Modify | Update name, add Exa command documentation |

All paths are relative to `~/.claude/skills/web-search/`.

---

## Task 1: Add Dependencies and Test Infrastructure

No acceptance criterion — this is pure setup that unblocks everything else.

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Update pyproject.toml**

```toml
[project]
name = "websearch"
version = "0.2.0"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27.0",
    "markdownify>=0.13.0",
    "markitdown>=0.0.1a2",
    "readabilipy>=0.2.0",
    "playwright>=1.44.0",
    "playwright-stealth>=2.0.0",
    "exa-py>=1.0.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Sync dependencies**

```bash
uv sync --directory ~/.claude/skills/web-search
```

Expected: resolves and installs `exa-py` and its dependencies with no errors.

- [ ] **Step 3: Create `tests/__init__.py`**

Empty file. Exact content: _(empty)_

- [ ] **Step 4: Create `tests/conftest.py`**

```python
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).parent.parent


def run_exa(
    *args: str,
    unset_keys: list[str] | None = None,
    set_keys: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | None, dict[str, Any] | None]:
    """Run exa.py via subprocess.

    Returns (returncode, stdout_parsed, stderr_parsed).
    stdout_parsed / stderr_parsed are None if the stream was empty.
    """
    env = os.environ.copy()
    for key in (unset_keys or []):
        env.pop(key, None)
    env.update(set_keys or {})

    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "exa.py"), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    stdout = json.loads(result.stdout) if result.stdout.strip() else None
    stderr = json.loads(result.stderr) if result.stderr.strip() else None
    return result.returncode, stdout, stderr
```

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add pyproject.toml tests/__init__.py tests/conftest.py
git commit -m "chore: add exa-py dep and test infrastructure"
```

---

## Task 2: Scaffold `exa_tools.py` and `exa.py`

**Fulfills:** AC-U9 (`--help` exits 0) via TDD. Also verifies AC-U8 (no `fetch_tools` import) as a static check — no red phase needed since the constraint is structural.

**Files:**
- Create: `exa_tools.py`
- Create: `exa.py`
- Create: `tests/test_unit.py` (initial)

- [ ] **Step 1: Write the failing test for AC-U9**

Create `tests/test_unit.py`:

```python
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from conftest import run_exa

SKILL_DIR = Path(__file__).parent.parent


# ── AC-U9 ─────────────────────────────────────────────────────────────────────

def test_help_exits_zero():
    """AC-U9: uv run ... python exa.py --help exits 0."""
    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "exa.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


# ── AC-U8 ─────────────────────────────────────────────────────────────────────

def test_no_fetch_tools_import():
    """AC-U8: exa.py must not import fetch_tools."""
    exa_source = (SKILL_DIR / "exa.py").read_text()
    assert "fetch_tools" not in exa_source
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_help_exits_zero -v
```

Expected: `FAILED` — `exa.py` does not exist yet; `FileNotFoundError` or subprocess non-zero exit.

- [ ] **Step 3: Create `exa_tools.py` stub**

```python
from __future__ import annotations

import os
from typing import Any


async def exa_search(
    query: str,
    num_results: int = 10,
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    return {"results": []}


async def exa_contents(
    urls: list[str],
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    return {"results": [], "failed_urls": []}


async def exa_similar(
    url: str,
    num_results: int = 10,
    use_text: bool = False,
    max_chars: int = 4000,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    return {"results": []}


async def exa_answer(question: str) -> dict[str, Any]:
    return {"answer": "", "citations": []}
```

- [ ] **Step 4: Create `exa.py` scaffold**

```python
from __future__ import annotations

import argparse
import asyncio
import json
import sys

try:
    from exa_tools import exa_answer, exa_contents, exa_search, exa_similar
except ImportError:
    print(
        json.dumps(
            {"error": "exa-py not installed. Run: uv sync --directory ~/.claude/skills/web-search"}
        ),
        file=sys.stderr,
    )
    sys.exit(1)

VALID_CATEGORIES = {
    "company",
    "financial report",
    "news",
    "people",
    "personal site",
    "research paper",
    "tweet",
}


def _fail(message: str) -> None:
    print(json.dumps({"error": message}), file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Exa semantic search CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    search_p = sub.add_parser("search")
    search_p.add_argument("query")
    search_p.add_argument("--num-results", type=int, default=10)
    search_p.add_argument("--category", default=None)
    search_p.add_argument("--include-domains", nargs="+", default=None)
    search_p.add_argument("--exclude-domains", nargs="+", default=None)
    search_p.add_argument("--start-date", default=None)
    search_p.add_argument("--end-date", default=None)
    search_p.add_argument("--text", action="store_true", default=False)
    search_p.add_argument("--highlights", action="store_true", default=False)
    search_p.add_argument("--max-chars", type=int, default=4000)

    contents_p = sub.add_parser("contents")
    contents_p.add_argument("urls", nargs="+")
    contents_p.add_argument("--text", action="store_true", default=False)
    contents_p.add_argument("--highlights", action="store_true", default=False)
    contents_p.add_argument("--max-chars", type=int, default=4000)

    similar_p = sub.add_parser("similar")
    similar_p.add_argument("url")
    similar_p.add_argument("--num-results", type=int, default=10)
    similar_p.add_argument("--text", action="store_true", default=False)
    similar_p.add_argument("--highlights", action="store_true", default=False)
    similar_p.add_argument("--max-chars", type=int, default=4000)
    similar_p.add_argument("--start-date", default=None)
    similar_p.add_argument("--end-date", default=None)

    answer_p = sub.add_parser("answer")
    answer_p.add_argument("question")

    args = parser.parse_args()

    # Validation is added task-by-task in subsequent tasks.

    if args.command == "search":
        result = asyncio.run(
            exa_search(
                args.query,
                num_results=args.num_results,
                category=args.category,
                include_domains=args.include_domains,
                exclude_domains=args.exclude_domains,
                start_date=args.start_date,
                end_date=args.end_date,
                use_text=args.text,
                max_chars=args.max_chars,
            )
        )
    elif args.command == "contents":
        urls = list(dict.fromkeys(args.urls))  # deduplicate, preserve order
        result = asyncio.run(
            exa_contents(urls, use_text=args.text, max_chars=args.max_chars)
        )
    elif args.command == "similar":
        result = asyncio.run(
            exa_similar(
                args.url,
                num_results=args.num_results,
                use_text=args.text,
                max_chars=args.max_chars,
                start_date=args.start_date,
                end_date=args.end_date,
            )
        )
    elif args.command == "answer":
        result = asyncio.run(exa_answer(args.question))

    if "error" in result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_help_exits_zero tests/test_unit.py::test_no_fetch_tools_import -v
```

Expected: both `PASSED`.

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa_tools.py exa.py tests/test_unit.py
git commit -m "feat: scaffold exa.py and exa_tools.py stubs"
```

---

## Task 3: Missing API Key Validation

**Fulfills:** AC-U1 — `EXA_API_KEY` unset → exit 1, stderr `{"error": "Missing EXA_API_KEY environment variable"}`.

**Files:**
- Modify: `exa_tools.py`
- Modify: `tests/test_unit.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_unit.py`:

```python
# ── AC-U1 ─────────────────────────────────────────────────────────────────────

def test_missing_api_key_search():
    """AC-U1: EXA_API_KEY unset on any subcommand → exit 1, structured error."""
    code, stdout, stderr = run_exa("search", "test query", unset_keys=["EXA_API_KEY"])
    assert code == 1
    assert stdout is None
    assert stderr == {"error": "Missing EXA_API_KEY environment variable"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_missing_api_key_search -v
```

Expected: `FAILED` — stub returns `{"results": []}`, printed to stdout, exit code 0.

- [ ] **Step 3: Add API key check to all four functions in `exa_tools.py`**

Replace the stub bodies with key checks. The check is identical in all four; only the stub return value changes:

```python
from __future__ import annotations

import os
from typing import Any

_MISSING_KEY_ERROR = {"error": "Missing EXA_API_KEY environment variable"}


async def exa_search(
    query: str,
    num_results: int = 10,
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"results": []}  # stub — replaced in Task 10


async def exa_contents(
    urls: list[str],
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"results": [], "failed_urls": []}  # stub — replaced in Task 13


async def exa_similar(
    url: str,
    num_results: int = 10,
    use_text: bool = False,
    max_chars: int = 4000,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"results": []}  # stub — replaced in Task 14


async def exa_answer(question: str) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"answer": "", "citations": []}  # stub — replaced in Task 15
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_missing_api_key_search -v
```

Expected: `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa_tools.py tests/test_unit.py
git commit -m "feat: validate EXA_API_KEY presence in all exa_tools functions (AC-U1)"
```

---

## Task 4: `--text` / `--highlights` Mutual Exclusion

**Fulfills:** AC-U5 — `--text --highlights` together → exit 1, `{"error": "--text and --highlights are mutually exclusive"}`.

**Files:**
- Modify: `exa.py`
- Modify: `tests/test_unit.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_unit.py`:

```python
# ── AC-U5 ─────────────────────────────────────────────────────────────────────

def test_text_highlights_mutually_exclusive_search():
    """AC-U5: --text and --highlights together on 'search' → exit 1."""
    code, stdout, stderr = run_exa("search", "test", "--text", "--highlights")
    assert code == 1
    assert stdout is None
    assert stderr == {"error": "--text and --highlights are mutually exclusive"}


def test_text_highlights_mutually_exclusive_contents():
    """AC-U5: --text and --highlights together on 'contents' → exit 1."""
    # set_keys ensures a dummy API key is present so the subprocess reaches
    # the mutual-exclusion check (which fires before dispatch) regardless of
    # whether EXA_API_KEY is set in the test environment.
    code, stdout, stderr = run_exa(
        "contents", "https://example.com", "--text", "--highlights",
        set_keys={"EXA_API_KEY": "dummy_key_for_testing"},
    )
    assert code == 1
    assert stderr == {"error": "--text and --highlights are mutually exclusive"}


def test_text_highlights_mutually_exclusive_similar():
    """AC-U5: --text and --highlights together on 'similar' → exit 1."""
    code, stdout, stderr = run_exa(
        "similar", "https://example.com", "--text", "--highlights",
        set_keys={"EXA_API_KEY": "dummy_key_for_testing"},
    )
    assert code == 1
    assert stderr == {"error": "--text and --highlights are mutually exclusive"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -k "mutually_exclusive" -v
```

Expected: all three `FAILED` — no validation in scaffold.

- [ ] **Step 3: Add mutual exclusion check in `exa.py` `main()`**

In `main()`, immediately after `args = parser.parse_args()`, add this block before any dispatch:

```python
    # Mutual exclusion applies to search, contents, similar (not answer)
    if args.command in {"search", "contents", "similar"}:
        if args.text and args.highlights:
            _fail("--text and --highlights are mutually exclusive")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -k "mutually_exclusive" -v
```

Expected: all three `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa.py tests/test_unit.py
git commit -m "feat: enforce --text/--highlights mutual exclusion (AC-U5)"
```

---

## Task 5: Invalid Category Validation

**Fulfills:** AC-U2 — `--category blorp` → exit 1, stderr contains `"Invalid category: blorp"`, no network call.

**Files:**
- Modify: `exa.py`
- Modify: `tests/test_unit.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_unit.py`:

```python
# ── AC-U2 ─────────────────────────────────────────────────────────────────────

def test_invalid_category():
    """AC-U2: invalid --category value → exit 1 before network call."""
    code, stdout, stderr = run_exa("search", "test", "--category", "blorp")
    assert code == 1
    assert stdout is None
    assert "Invalid category" in stderr["error"]
    assert "blorp" in stderr["error"]


def test_valid_category_accepted():
    """AC-U2: valid category values are accepted (no validation error)."""
    # Passes validation — stub returns {"results": []}, exits 0
    # Run without EXA_API_KEY so it fails on key check, not category check
    code, _, stderr = run_exa(
        "search", "test", "--category", "research paper", unset_keys=["EXA_API_KEY"]
    )
    # Should fail on API key, NOT on category
    assert stderr == {"error": "Missing EXA_API_KEY environment variable"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_invalid_category tests/test_unit.py::test_valid_category_accepted -v
```

Expected: `test_invalid_category` FAILED (no category check in scaffold). `test_valid_category_accepted` may PASS or FAIL depending on env — both are expected behaviors at this stage.

- [ ] **Step 3: Add category validation in `exa.py`**

In `main()`, inside the `if args.command in {"search", "contents", "similar"}:` block (after the mutual exclusion check), add for `search` only:

```python
    if args.command == "search":
        if args.category is not None and args.category not in VALID_CATEGORIES:
            _fail(
                f"Invalid category: {args.category!r}. "
                f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
            )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_invalid_category tests/test_unit.py::test_valid_category_accepted -v
```

Expected: both `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa.py tests/test_unit.py
git commit -m "feat: validate --category against VALID_CATEGORIES (AC-U2)"
```

---

## Task 6: Date Format Validation

**Fulfills:** AC-U3 — `--start-date 2024-13-01` → exit 1, stderr contains `"Invalid date format"`, no network call.

**Files:**
- Modify: `exa.py`
- Modify: `tests/test_unit.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_unit.py`:

```python
# ── AC-U3 ─────────────────────────────────────────────────────────────────────

def test_invalid_start_date_format():
    """AC-U3: --start-date with bad format → exit 1 before network call."""
    code, stdout, stderr = run_exa("search", "test", "--start-date", "2024-13-01")
    assert code == 1
    assert stdout is None
    assert "Invalid date format" in stderr["error"]
    assert "2024-13-01" in stderr["error"]


def test_invalid_end_date_format():
    """AC-U3: --end-date with non-date string → exit 1 before network call."""
    code, stdout, stderr = run_exa("search", "test", "--end-date", "not-a-date")
    assert code == 1
    assert "Invalid date format" in stderr["error"]
    assert "not-a-date" in stderr["error"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_invalid_start_date_format tests/test_unit.py::test_invalid_end_date_format -v
```

Expected: both `FAILED`.

- [ ] **Step 3: Add date validation helper and calls in `exa.py`**

Add this helper below `_fail`:

```python
import re
from datetime import date as _date

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_date(value: str) -> _date:
    """Validate YYYY-MM-DD format and parse. Calls _fail() on bad input."""
    if not _DATE_RE.match(value):
        _fail(f"Invalid date format: {value!r}. Expected YYYY-MM-DD")
    try:
        return _date.fromisoformat(value)
    except ValueError:
        _fail(f"Invalid date format: {value!r}. Expected YYYY-MM-DD")
```

Note: `_fail` calls `sys.exit(1)`, so the `return` after it is unreachable — `_validate_date` never returns `None`. Add the `-> _date` return type annotation to make this clear; mypy will accept it because `_fail` is typed `-> None` and `sys.exit` raises `SystemExit`.

In `main()`, add date validation for `search` (after category check) and `similar` (before dispatch):

```python
    if args.command in {"search", "similar"}:
        start = _validate_date(args.start_date) if args.start_date else None
        end = _validate_date(args.end_date) if args.end_date else None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_invalid_start_date_format tests/test_unit.py::test_invalid_end_date_format -v
```

Expected: both `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa.py tests/test_unit.py
git commit -m "feat: validate --start-date/--end-date format (AC-U3)"
```

---

## Task 7: Start-Date / End-Date Ordering Validation

**Fulfills:** AC-U4 — `--start-date 2024-06-01 --end-date 2024-01-01` → exit 1 (start after end).

**Files:**
- Modify: `exa.py`
- Modify: `tests/test_unit.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_unit.py`:

```python
# ── AC-U4 ─────────────────────────────────────────────────────────────────────

def test_start_date_after_end_date():
    """AC-U4: start-date after end-date → exit 1 before network call."""
    code, stdout, stderr = run_exa(
        "search", "test", "--start-date", "2024-06-01", "--end-date", "2024-01-01"
    )
    assert code == 1
    assert stdout is None
    assert "start-date" in stderr["error"] or "end-date" in stderr["error"]


def test_equal_start_end_dates_accepted():
    """AC-U4: start-date == end-date is valid (boundary case)."""
    # Fails on API key, not on date ordering
    code, _, stderr = run_exa(
        "search", "test",
        "--start-date", "2024-06-01",
        "--end-date", "2024-06-01",
        unset_keys=["EXA_API_KEY"],
    )
    assert stderr == {"error": "Missing EXA_API_KEY environment variable"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_start_date_after_end_date tests/test_unit.py::test_equal_start_end_dates_accepted -v
```

Expected: `test_start_date_after_end_date` FAILED. `test_equal_start_end_dates_accepted` may pass or fail.

- [ ] **Step 3: Add ordering check in `exa.py`**

Immediately after the date validation block from Task 6 (where `start` and `end` are parsed):

```python
    if args.command in {"search", "similar"}:
        start = _validate_date(args.start_date) if args.start_date else None
        end = _validate_date(args.end_date) if args.end_date else None
        if start is not None and end is not None and start > end:
            _fail("start-date must be before or equal to end-date")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py::test_start_date_after_end_date tests/test_unit.py::test_equal_start_end_dates_accepted -v
```

Expected: both `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa.py tests/test_unit.py
git commit -m "feat: validate start-date <= end-date ordering (AC-U4)"
```

---

## Task 8: `--num-results` Range Validation

**Fulfills:** AC-U6 — `--num-results 0` and `--num-results 101` both exit 1.

**Files:**
- Modify: `exa.py`
- Modify: `tests/test_unit.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_unit.py`:

```python
# ── AC-U6 ─────────────────────────────────────────────────────────────────────

def test_num_results_zero():
    """AC-U6: --num-results 0 → exit 1."""
    code, stdout, stderr = run_exa("search", "test", "--num-results", "0")
    assert code == 1
    assert stdout is None
    assert "--num-results" in stderr["error"]


def test_num_results_over_max():
    """AC-U6: --num-results 101 → exit 1."""
    code, stdout, stderr = run_exa("search", "test", "--num-results", "101")
    assert code == 1
    assert "--num-results" in stderr["error"]


def test_num_results_boundary_valid():
    """AC-U6: --num-results 1 and 100 are valid."""
    for n in ("1", "100"):
        code, _, stderr = run_exa(
            "search", "test", "--num-results", n, unset_keys=["EXA_API_KEY"]
        )
        # Should fail on API key, NOT on num-results
        assert stderr == {"error": "Missing EXA_API_KEY environment variable"}, (
            f"--num-results {n} triggered unexpected error: {stderr}"
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -k "num_results" -v
```

Expected: `test_num_results_zero` and `test_num_results_over_max` FAILED. `test_num_results_boundary_valid` may vary.

- [ ] **Step 3: Add range validation in `exa.py`**

In `main()`, add for `search` and `similar` (both accept `--num-results`). Insert after the mutual exclusion check:

```python
    if args.command in {"search", "similar"}:
        if not 1 <= args.num_results <= 100:
            _fail("--num-results must be between 1 and 100")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -k "num_results" -v
```

Expected: all three `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa.py tests/test_unit.py
git commit -m "feat: validate --num-results range 1-100 (AC-U6)"
```

---

## Task 9: `exa similar` URL Validation

**Fulfills:** AC-U7 — `exa similar not-a-url` → exit 1 with error on stderr.

**Files:**
- Modify: `exa.py`
- Modify: `tests/test_unit.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_unit.py`:

```python
# ── AC-U7 ─────────────────────────────────────────────────────────────────────

def test_similar_rejects_non_url():
    """AC-U7: exa similar with a non-URL string → exit 1."""
    code, stdout, stderr = run_exa("similar", "not-a-url")
    assert code == 1
    assert stdout is None
    assert "Invalid URL" in stderr["error"]


def test_similar_accepts_http_url():
    """AC-U7: valid http:// URL passes validation."""
    code, _, stderr = run_exa(
        "similar", "http://example.com", unset_keys=["EXA_API_KEY"]
    )
    assert stderr == {"error": "Missing EXA_API_KEY environment variable"}


def test_similar_accepts_https_url():
    """AC-U7: valid https:// URL passes validation."""
    code, _, stderr = run_exa(
        "similar", "https://arxiv.org/abs/2307.06435", unset_keys=["EXA_API_KEY"]
    )
    assert stderr == {"error": "Missing EXA_API_KEY environment variable"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -k "similar" -v
```

Expected: `test_similar_rejects_non_url` FAILED.

- [ ] **Step 3: Add URL validation in `exa.py`**

In `main()`, in the block where `args.command == "similar"` checks are handled, add:

```python
    if args.command == "similar":
        if not (args.url.startswith("http://") or args.url.startswith("https://")):
            _fail("Invalid URL: must start with http:// or https://")
```

Place this check before the `--num-results` range check and date validation for `similar`.

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -k "similar" -v
```

Expected: all three `PASSED`.

- [ ] **Step 5: Run full unit suite to confirm no regressions**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -v
```

Expected: all unit tests `PASSED`.

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa.py tests/test_unit.py
git commit -m "feat: validate URL format for exa similar (AC-U7)"
```

---

## Task 10: Implement `exa_search` — Highlights Mode

**Fulfills:** AC-I1 — `exa search "..." --category "research paper"` exits 0, results have `url` and `highlights`, no `text` key.

**Files:**
- Modify: `exa_tools.py`
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write the failing integration test**

Create `tests/test_integration.py`:

```python
from __future__ import annotations

import os

import pytest

from conftest import run_exa

# All tests in this file require a live EXA_API_KEY.
pytestmark = pytest.mark.skipif(
    not os.getenv("EXA_API_KEY"),
    reason="EXA_API_KEY not set — skipping integration tests",
)


# ── AC-I1 ─────────────────────────────────────────────────────────────────────

def test_search_highlights_mode():
    """AC-I1: search returns results with url+highlights, no text key."""
    code, data, stderr = run_exa(
        "search", "papers on RLHF and calibration", "--category", "research paper"
    )
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert stderr is None
    assert "results" in data
    assert len(data["results"]) > 0, "Expected at least one result"
    for result in data["results"]:
        assert "url" in result, f"Missing 'url' in result: {result}"
        assert isinstance(result["url"], str)
        assert "highlights" in result, f"Missing 'highlights' in result: {result}"
        assert isinstance(result["highlights"], list)
        assert "text" not in result, f"'text' must not appear in highlights mode: {result}"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_search_highlights_mode -v
```

Expected: `FAILED` — stub returns `{"results": []}`, so `len(data["results"]) > 0` fails.

- [ ] **Step 3: Implement `exa_search` in `exa_tools.py`**

Replace the `exa_search` stub with the full implementation. Also add `_shape_result` helper (shared with later tasks):

```python
from __future__ import annotations

import os
from typing import Any

from exa_py import AsyncExa

_MISSING_KEY_ERROR = {"error": "Missing EXA_API_KEY environment variable"}


def _shape_result(r: Any, use_text: bool) -> dict[str, Any]:
    """Map an SDK result object to the output contract shape.

    Strips: requestId, costDollars, image, favicon, highlightScores, id.
    Omits published_date and author if absent (not null).
    """
    out: dict[str, Any] = {"title": r.title or "", "url": r.url}
    if getattr(r, "published_date", None):
        out["published_date"] = r.published_date
    if getattr(r, "author", None):
        out["author"] = r.author
    if use_text:
        out["text"] = r.text or ""
    else:
        out["highlights"] = r.highlights or []
    return out


async def exa_search(
    query: str,
    num_results: int = 10,
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return _MISSING_KEY_ERROR

    contents: dict[str, Any]
    if use_text:
        contents = {"text": {"max_characters": max_chars}}
    else:
        contents = {"highlights": {"max_characters": max_chars}}

    kwargs: dict[str, Any] = {
        "num_results": num_results,
        "contents": contents,
    }
    if category:
        kwargs["category"] = category
    if include_domains:
        kwargs["include_domains"] = include_domains
    if exclude_domains:
        kwargs["exclude_domains"] = exclude_domains
    if start_date:
        kwargs["start_published_date"] = start_date + "T00:00:00.000Z"
    if end_date:
        kwargs["end_published_date"] = end_date + "T23:59:59.999Z"

    try:
        async with AsyncExa(api_key=api_key) as client:
            response = await client.search(query, **kwargs)
        return {"results": [_shape_result(r, use_text) for r in response.results]}
    except Exception as e:
        return _classify_error(e, "/search")


def _classify_error(e: Exception, endpoint: str) -> dict[str, Any]:
    msg = str(e).lower()
    if "401" in msg or "unauthorized" in msg or "authentication" in msg:
        return {"error": "Exa authentication failed. Check EXA_API_KEY."}
    if "timeout" in msg:
        return {"error": f"Request timed out calling Exa {endpoint}"}
    if "connection" in msg or "network" in msg:
        return {"error": f"Network error calling Exa {endpoint}: {e}"}
    return {"error": f"Exa API error: {e}"}


async def exa_contents(
    urls: list[str],
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"results": [], "failed_urls": []}  # stub — replaced in Task 13


async def exa_similar(
    url: str,
    num_results: int = 10,
    use_text: bool = False,
    max_chars: int = 4000,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"results": []}  # stub — replaced in Task 14


async def exa_answer(question: str) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"answer": "", "citations": []}  # stub — replaced in Task 15
```

**Note on `AsyncExa` context manager:** If `async with AsyncExa(...) as client:` raises `AttributeError: __aenter__`, the SDK version does not support the context manager protocol. In that case replace with:
```python
client = AsyncExa(api_key=api_key)
response = await client.search(query, **kwargs)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_search_highlights_mode -v
```

Expected: `PASSED`.

- [ ] **Step 5: Run unit tests to confirm no regressions**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -v
```

Expected: all `PASSED`.

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa_tools.py tests/test_integration.py
git commit -m "feat: implement exa_search with AsyncExa (AC-I1)"
```

---

## Task 11: `exa search --text` Mode

**Fulfills:** AC-I2 — `exa search "..." --text` exits 0, every result has `text`, no result has `highlights`.

**Files:**
- Modify: `tests/test_integration.py`

No changes to source — `exa_search` already handles `use_text=True` from Task 10.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_integration.py`:

```python
# ── AC-I2 ─────────────────────────────────────────────────────────────────────

def test_search_text_mode():
    """AC-I2: --text flag returns text field, no highlights field."""
    code, data, stderr = run_exa("search", "introduction to transformers", "--text")
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert stderr is None
    assert len(data["results"]) > 0
    for result in data["results"]:
        assert "text" in result, f"Missing 'text' in result: {result}"
        assert isinstance(result["text"], str)
        assert "highlights" not in result, f"'highlights' must not appear in text mode: {result}"
```

**Note — no red phase for this task.** `exa_search` is fully implemented after Task 10, and it already correctly handles `use_text=True`. Writing the test in Step 1 and running it will produce a green result immediately. This is expected: the test is being written to formally verify coverage of AC-I2, not to drive new implementation.

- [ ] **Step 2: Run test to confirm it passes**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_search_text_mode -v
```

Expected: `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add tests/test_integration.py
git commit -m "test: verify exa search --text mode (AC-I2)"
```

---

## Task 12: `exa search --num-results` Respected

**Fulfills:** AC-I3 — `exa search "..." --num-results 3` exits 0 and `len(results) <= 3`.

**Files:**
- Modify: `tests/test_integration.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_integration.py`:

```python
# ── AC-I3 ─────────────────────────────────────────────────────────────────────

def test_search_num_results_respected():
    """AC-I3: --num-results 3 returns at most 3 results."""
    code, data, stderr = run_exa("search", "machine learning", "--num-results", "3")
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert len(data["results"]) <= 3, (
        f"Expected at most 3 results, got {len(data['results'])}"
    )
```

**Note — no red phase for this task.** After Task 10, `exa_search` is fully implemented and `num_results` is already passed through from the scaffold. Writing the test and running it will pass immediately. This task formally verifies AC-I3 coverage.

- [ ] **Step 2: Run test to confirm it passes**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_search_num_results_respected -v
```

Expected: `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add tests/test_integration.py
git commit -m "test: verify --num-results cap is respected (AC-I3)"
```

---

## Task 13: Implement `exa_contents`

**Fulfills:** AC-I4 — `exa contents <url>` exits 0, `results[0].url` matches input, `failed_urls` key is present.

**Files:**
- Modify: `exa_tools.py`
- Modify: `tests/test_integration.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_integration.py`:

```python
# ── AC-I4 ─────────────────────────────────────────────────────────────────────

def test_contents_returns_url_and_failed_urls():
    """AC-I4: exa contents returns matching URL result and failed_urls key."""
    target = "https://arxiv.org/abs/2307.06435"
    code, data, stderr = run_exa("contents", target)
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert "failed_urls" in data, "Output must always contain 'failed_urls' key"
    assert isinstance(data["failed_urls"], list)
    # At least one result should match the requested URL (or it's in failed_urls)
    urls_returned = [r["url"] for r in data["results"]]
    assert target in urls_returned or target in data["failed_urls"], (
        f"{target} not in results or failed_urls"
    )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_contents_returns_url_and_failed_urls -v
```

Expected: `FAILED` — stub returns `{"results": [], "failed_urls": []}`, so `target in urls_returned` is False and `target in data["failed_urls"]` is also False.

- [ ] **Step 3: Implement `exa_contents` in `exa_tools.py`**

Replace the `exa_contents` stub:

```python
async def exa_contents(
    urls: list[str],
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return _MISSING_KEY_ERROR

    contents_spec: dict[str, Any]
    if use_text:
        contents_spec = {"text": {"max_characters": max_chars}}
    else:
        contents_spec = {"highlights": {"max_characters": max_chars}}

    try:
        async with AsyncExa(api_key=api_key) as client:
            # Pass contents as a named kwarg — consistent with client.search().
            # If this raises TypeError, check the installed SDK signature with:
            #   python -c "from exa_py import AsyncExa; help(AsyncExa.get_contents)"
            # The parameter may be `ids=` instead of positional, or `text=`/`highlights=`
            # as top-level kwargs. Adjust accordingly.
            response = await client.get_contents(urls, contents=contents_spec)
    except Exception as e:
        return _classify_error(e, "/contents")

    results = []
    failed_urls = []

    # Build a set of successfully returned URLs to detect per-URL failures.
    returned_ids = {r.url for r in response.results}

    for url in urls:
        if url in returned_ids:
            match = next(r for r in response.results if r.url == url)
            results.append(_shape_result(match, use_text))
        else:
            failed_urls.append(url)

    return {"results": results, "failed_urls": failed_urls}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_contents_returns_url_and_failed_urls -v
```

Expected: `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa_tools.py tests/test_integration.py
git commit -m "feat: implement exa_contents with per-URL failure tracking (AC-I4)"
```

---

## Task 14: Implement `exa_similar`

**Fulfills:** AC-I5 — `exa similar <url> --num-results 5` exits 0 and `len(results) <= 5`.

**Files:**
- Modify: `exa_tools.py`
- Modify: `tests/test_integration.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_integration.py`:

```python
# ── AC-I5 ─────────────────────────────────────────────────────────────────────

def test_similar_returns_bounded_results():
    """AC-I5: exa similar returns at most --num-results results."""
    code, data, stderr = run_exa(
        "similar", "https://arxiv.org/abs/2307.06435", "--num-results", "5"
    )
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert "results" in data
    assert len(data["results"]) <= 5, (
        f"Expected at most 5 results, got {len(data['results'])}"
    )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_similar_returns_bounded_results -v
```

Expected: `FAILED` — stub returns `{"results": []}`. `len([]) <= 5` is True, but we need to verify the function is actually being called with the real SDK. If the stub is returning empty and the assertion passes, the test design is wrong. Double-check: the test should also assert `len(data["results"]) > 0`.

Revise the test to also assert at least one result:

```python
    assert len(data["results"]) > 0, "Expected at least one similar result"
    assert len(data["results"]) <= 5
```

Rerun — now stub fails because `len([]) > 0` is False.

- [ ] **Step 3: Implement `exa_similar` in `exa_tools.py`**

Replace the stub:

```python
async def exa_similar(
    url: str,
    num_results: int = 10,
    use_text: bool = False,
    max_chars: int = 4000,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return _MISSING_KEY_ERROR

    contents: dict[str, Any]
    if use_text:
        contents = {"text": {"max_characters": max_chars}}
    else:
        contents = {"highlights": {"max_characters": max_chars}}

    kwargs: dict[str, Any] = {
        "num_results": num_results,
        "contents": contents,
    }
    if start_date:
        kwargs["start_published_date"] = start_date + "T00:00:00.000Z"
    if end_date:
        kwargs["end_published_date"] = end_date + "T23:59:59.999Z"

    try:
        async with AsyncExa(api_key=api_key) as client:
            response = await client.find_similar(url, **kwargs)
        return {"results": [_shape_result(r, use_text) for r in response.results]}
    except Exception as e:
        return _classify_error(e, "/findSimilar")
```

**Note on SDK method name:** The async find-similar method may be `client.find_similar(url, ...)` or `client.find_similar_and_contents(url, ...)`. Verify with `help(AsyncExa.find_similar)` if uncertain.

- [ ] **Step 4: Run test to verify it passes**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_similar_returns_bounded_results -v
```

Expected: `PASSED`.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa_tools.py tests/test_integration.py
git commit -m "feat: implement exa_similar (AC-I5)"
```

---

## Task 15: Implement `exa_answer`

**Fulfills:** AC-I6 — `exa answer "What is 2+2?"` exits 0, `answer` is a string, `citations` is a list.

**Files:**
- Modify: `exa_tools.py`
- Modify: `tests/test_integration.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_integration.py`:

```python
# ── AC-I6 ─────────────────────────────────────────────────────────────────────

def test_answer_returns_string_and_citations():
    """AC-I6: exa answer returns answer (str) and citations (list)."""
    code, data, stderr = run_exa("answer", "What is 2+2?")
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0, "Exa should return a non-empty answer for 'What is 2+2?'"
    assert "citations" in data
    assert isinstance(data["citations"], list)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_answer_returns_string_and_citations -v
```

Expected: `FAILED` — stub returns `{"answer": "", "citations": []}`, so `len(data["answer"]) > 0` fails.

- [ ] **Step 3: Implement `exa_answer` in `exa_tools.py`**

Replace the stub:

```python
async def exa_answer(question: str) -> dict[str, Any]:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return _MISSING_KEY_ERROR

    try:
        async with AsyncExa(api_key=api_key) as client:
            response = await client.answer(question)
    except Exception as e:
        return _classify_error(e, "/answer")

    citations = []
    for c in getattr(response, "citations", []) or []:
        citation: dict[str, Any] = {
            "url": c.url,
            "title": c.title or "",
        }
        if getattr(c, "published_date", None):
            citation["published_date"] = c.published_date
        citations.append(citation)

    return {
        "answer": response.answer or "",
        "citations": citations,
    }
```

**Note on SDK response shape:** The `answer` endpoint response attributes depend on the `exa-py` version. Check `response.__dict__` or `dir(response)` if attribute access fails.

- [ ] **Step 4: Run test to verify it passes**

```bash
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py::test_answer_returns_string_and_citations -v
```

Expected: `PASSED`.

- [ ] **Step 5: Run full test suite**

```bash
uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -v
EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py -v
```

Expected: all tests `PASSED`.

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/web-search
git add exa_tools.py tests/test_integration.py
git commit -m "feat: implement exa_answer (AC-I6)"
```

---

## Task 16: Update SKILL.md

No acceptance criterion — documentation task.

**Files:**
- Modify: `SKILL.md`

- [ ] **Step 1: Update SKILL.md front matter and add Exa section**

Open `SKILL.md`. Change the `name` field from `brave-web-search` to `web-search`. Add a new `## Exa` section documenting the four subcommands and key flags. Follow the existing section style. Minimum content:

```markdown
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
| `--num-results INT` | search, similar | 10 | Results count (1–100) |
| `--category STR` | search | — | Content type filter |
| `--start-date YYYY-MM-DD` | search, similar | — | Published after |
| `--end-date YYYY-MM-DD` | search, similar | — | Published before |
| `--include-domains` | search | — | Allowlist domains |
| `--exclude-domains` | search | — | Blocklist domains |

### Output

All commands print JSON to stdout on success. Errors go to stderr as `{"error": "..."}` with exit code 1.
```

- [ ] **Step 2: Commit**

```bash
cd ~/.claude/skills/web-search
git add SKILL.md
git commit -m "docs: update SKILL.md with Exa commands and rename to web-search"
```

---

## Final Verification

- [ ] Run the complete unit suite: `uv run --directory ~/.claude/skills/web-search pytest tests/test_unit.py -v`
- [ ] Run the complete integration suite: `EXA_API_KEY=$EXA_API_KEY uv run --directory ~/.claude/skills/web-search pytest tests/test_integration.py -v`
- [ ] Confirm `exa.py --help` lists all four subcommands
- [ ] Confirm `grep fetch_tools ~/.claude/skills/web-search/exa.py` returns no output
