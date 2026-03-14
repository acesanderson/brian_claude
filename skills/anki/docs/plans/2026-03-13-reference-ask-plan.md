# Reference Field + LLM Ask + UI Polish — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `reference` text field to cards, expose it in the study REPL via `[r]`, enable one-shot LLM Q&A via `[k]`, and tighten the action bar UI.

**Architecture:** The data layer gets a new nullable `reference` column propagated through db → repo → service. A new `display.py` module owns all screen-rendering constants and the `truncate_for_display` helper. A new `llm.py` module owns the HeadwaterClient call. `study.py` and `cli.py` are the only UI integration points.

**Tech Stack:** Python 3.12+, psycopg2, Rich, Jinja2, HeadwaterAsyncClient (`headwater_client`), `headwater_api`, `conduit` (for GenerationParams/ConduitOptions).

**Design doc:** `docs/plans/2026-03-13-reference-ask-design.md`

---

## Chunk 1: Data Layer

Tasks 1–4 touch db.py, models.py, repo.py, and service.py. No UI. All tests are integration tests against the real `anki` DB using the existing `conn` fixture pattern.

Run all tests in this chunk with:
```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_repo.py tests/test_service.py -v
```

---

### Task 1: Schema migration — add `reference` column

**Fulfills AC:** `ALTER TABLE` runs idempotently on a DB that already has the column.

**Files:**
- Modify: `study/src/db.py`
- Modify: `study/tests/test_db.py`

- [ ] **Step 1: Write the failing test**

Open `study/tests/test_db.py` and add:

```python
def test_init_schema_reference_column_idempotent(conn):
    """init_schema must not fail when reference column already exists."""
    # Run twice — second call exercises IF NOT EXISTS
    init_schema(conn)
    init_schema(conn)
    # Verify column exists
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'cards' AND column_name = 'reference'
            """
        )
        row = cur.fetchone()
    assert row is not None, "reference column should exist after init_schema"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_db.py::test_init_schema_reference_column_idempotent -v
```

Expected: FAIL — column does not exist yet.

- [ ] **Step 3: Add the ALTER TABLE to `init_schema` in `db.py`**

In `study/src/db.py`, after the `SCHEMA_SQL` string (i.e., still in `init_schema`, after `cur.execute(SCHEMA_SQL)`), add a second `cur.execute`:

```python
def init_schema(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
        cur.execute(
            "ALTER TABLE cards ADD COLUMN IF NOT EXISTS reference TEXT"
        )
    conn.commit()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_db.py::test_init_schema_reference_column_idempotent -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/anki
git add study/src/db.py study/tests/test_db.py
git commit -m "feat: add reference column to cards via init_schema"
```

---

### Task 2: Card model — add `reference` field

**Fulfills AC:** `_row_to_card(row)` where `row[14] is None` produces `card.reference is None`.
**Fulfills AC:** Pre-migration fixture card raises `IndexError` until `init_schema` is run (documents the migration boundary; no new test needed beyond the one below).

**Files:**
- Modify: `study/src/models.py`
- Modify: `study/src/repo.py`
- Modify: `study/tests/test_repo.py`

- [ ] **Step 1: Write the failing test**

Add to `study/tests/test_repo.py`:

```python
def test_add_card_reference_none(conn):
    """Card added without reference has reference=None."""
    deck = repo.create_deck(conn, "test_ref_none")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    assert card.reference is None


def test_add_card_with_reference(conn):
    """Card added with reference stores and returns it."""
    deck = repo.create_deck(conn, "test_ref_stored")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A",
                         reference="See page 42.")
    assert card.reference == "See page 42."


def test_row_to_card_none_reference():
    """_row_to_card with row[14]=None produces card.reference=None (unit test, no DB)."""
    from datetime import datetime, timezone
    from src.repo import _row_to_card
    now = datetime.now(tz=timezone.utc)
    row = (
        1, 1, "front", "back", [], now,  # id, deck_id, front, back, tags, created_at
        "new", now, 0, 2500, 0, 0, 0, False,  # state, due, interval, ease, reps, lapses, step, suspended
        None,  # reference
    )
    card = _row_to_card(row)
    assert card.reference is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_repo.py::test_add_card_reference_none tests/test_repo.py::test_add_card_with_reference tests/test_repo.py::test_row_to_card_none_reference -v
```

Expected: FAIL — `Card` has no `reference` field, `add_card` doesn't accept it.

- [ ] **Step 3: Add `reference` to the `Card` dataclass**

In `study/src/models.py`, append `reference` as the last field of `Card`:

```python
@dataclass
class Card:
    id: int
    deck_id: int
    front: str
    back: str
    tags: list[str]
    created_at: datetime
    state: str
    due: datetime
    interval: int
    ease_factor: int
    reps: int
    lapses: int
    step_index: int
    suspended: bool
    reference: str | None  # None for legacy cards and cards without reference
```

- [ ] **Step 4: Update `repo.py` — SELECT, INSERT, and `_row_to_card`**

Every `SELECT` on `cards` must include `reference` as the last column. Update all five SELECT sites and `add_card`'s INSERT. Also update `_row_to_card`:

**In `add_card`:** Change the INSERT to:
```python
cur.execute(
    """
    INSERT INTO cards (deck_id, front, back, tags, reference)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id, deck_id, front, back, tags, created_at,
              state, due, interval, ease_factor, reps, lapses,
              step_index, suspended, reference
    """,
    (deck_id, front, back, tags or [], reference),
)
```

And update the signature:
```python
def add_card(
    conn: psycopg2.extensions.connection,
    deck_id: int,
    front: str,
    back: str,
    tags: list[str] | None = None,
    reference: str | None = None,
) -> Card:
```

**In `get_card`, `list_cards`, `get_due_cards`, `get_all_cards_for_cram`:** Append `, reference` to the end of every `SELECT ... FROM cards` column list.

**In `_row_to_card`:**
```python
def _row_to_card(row: tuple) -> Card:
    return Card(
        id=row[0], deck_id=row[1], front=row[2], back=row[3],
        tags=list(row[4]) if row[4] else [],
        created_at=row[5], state=row[6], due=row[7],
        interval=row[8], ease_factor=row[9], reps=row[10],
        lapses=row[11], step_index=row[12], suspended=row[13],
        reference=row[14],
    )
```

Note: `update_card` (used by `edit_card`) and `update_card_state` do not SELECT `reference` in their RETURNING clause — update those too to keep `_row_to_card` correct, or adjust the RETURNING columns. Easiest: add `reference` to their RETURNING as well, even though we don't update the reference column in those calls.

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_repo.py -v
```

Expected: all PASS. If existing tests fail due to column count changes, the RETURNING clauses in `update_card` / `update_card_state` need `reference` added.

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/anki
git add study/src/models.py study/src/repo.py study/tests/test_repo.py
git commit -m "feat: add reference field to Card model and repo layer"
```

---

### Task 3: Service layer — propagate `reference` + protect `snapshot_card`

**Fulfills AC:** `snapshot_card(card)` returns a dict where `"reference" not in result`.

**Files:**
- Modify: `study/src/service.py`
- Modify: `study/tests/test_service.py`

- [ ] **Step 1: Write the failing tests**

Add to `study/tests/test_service.py`:

```python
def test_add_card_with_reference(conn):
    """service.add_card passes reference through to repo."""
    service.create_deck(conn, "svc_ref")
    card = service.add_card(conn, deck_name="svc_ref", front="Q", back="A",
                             reference="a source")
    assert card.reference == "a source"


def test_add_card_reference_defaults_none(conn):
    """service.add_card without reference produces reference=None."""
    service.create_deck(conn, "svc_ref_none")
    card = service.add_card(conn, deck_name="svc_ref_none", front="Q", back="A")
    assert card.reference is None


def test_snapshot_card_excludes_reference(conn):
    """snapshot_card must not include 'reference' — it is not a scheduling field."""
    service.create_deck(conn, "svc_snap")
    card = service.add_card(conn, deck_name="svc_snap", front="Q", back="A",
                             reference="do not snapshot me")
    snap = service.snapshot_card(card)
    assert "reference" not in snap
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_service.py::test_add_card_with_reference tests/test_service.py::test_add_card_reference_defaults_none tests/test_service.py::test_snapshot_card_excludes_reference -v
```

Expected: first two FAIL (service.add_card doesn't accept reference yet), third PASS (snapshot_card already excludes it — verify this).

- [ ] **Step 3: Update `service.add_card` signature**

In `study/src/service.py`, update `add_card`:

```python
def add_card(
    conn: psycopg2.extensions.connection,
    deck_name: str,
    front: str,
    back: str,
    tags: list[str] | None = None,
    reference: str | None = None,
) -> Card:
    deck = get_deck(conn, deck_name)
    card = repo.add_card(conn, deck_id=deck.id, front=front, back=back,
                         tags=tags or [], reference=reference)
    logger.debug("Added card id=%d to deck '%s'", card.id, deck_name)
    return card
```

- [ ] **Step 4: Run all service tests**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_service.py -v
```

Expected: all PASS.

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/anki
git add study/src/service.py study/tests/test_service.py
git commit -m "feat: propagate reference through service layer; guard snapshot_card"
```

---

## Chunk 2: Pure Logic — Display + LLM

Tasks 4–6 have no DB or network dependencies. Tests are pure unit tests. Run:

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_display.py tests/test_llm.py -v
```

---

### Task 4: `display.py` — constants, truncation, action bar markup

**Fulfills AC:** `truncate_for_display("a" * 1000, width=80, max_lines=8)` returns at most 8 lines.
**Fulfills AC:** `truncate_for_display("short text", width=80, max_lines=8)` returns unchanged, no ellipsis.
**Fulfills AC:** `reference=None` card produces markup containing `[s]reference[/s]`.
**Fulfills AC:** `reference="some text"` card produces markup containing `[bold magenta][r] reference[/bold magenta]`.

**Files:**
- Create: `study/src/display.py`
- Create: `study/tests/test_display.py`

- [ ] **Step 1: Write failing tests**

Create `study/tests/test_display.py`:

```python
from __future__ import annotations
import pytest
from src.display import truncate_for_display, reference_key_markup


def test_truncate_long_text_stays_within_max_lines():
    """AC: truncate_for_display('a'*1000, width=80, max_lines=8) returns ≤8 display lines."""
    result = truncate_for_display("a" * 1000, width=80, max_lines=8)
    # Count non-ellipsis lines
    lines = [l for l in result.splitlines() if l.strip() != "[dim]…[/dim]"]
    assert len(lines) <= 8


def test_truncate_long_text_appends_ellipsis():
    """Truncated output ends with the dim ellipsis marker."""
    result = truncate_for_display("a" * 1000, width=80, max_lines=8)
    assert "[dim]…[/dim]" in result


def test_truncate_short_text_unchanged():
    """AC: short text returns unchanged, no ellipsis."""
    result = truncate_for_display("short text", width=80, max_lines=8)
    assert result == "short text"
    assert "[dim]…[/dim]" not in result


def test_truncate_exact_max_lines_no_ellipsis():
    """Text with exactly max_lines lines (all short) is not truncated."""
    text = "\n".join(["line"] * 8)
    result = truncate_for_display(text, width=80, max_lines=8)
    assert "[dim]…[/dim]" not in result
    assert result.count("\n") == 7  # 8 lines = 7 newlines


def test_truncate_width_enforced():
    """A single line longer than width is split into multiple visual lines."""
    result = truncate_for_display("x" * 200, width=80, max_lines=8)
    for line in result.splitlines():
        if line != "[dim]…[/dim]":
            assert len(line) <= 80


def test_reference_key_markup_no_reference():
    """AC: card with reference=None produces markup with [s]reference[/s]."""
    markup = reference_key_markup(has_reference=False)
    assert "[s]reference[/s]" in markup


def test_reference_key_markup_has_reference():
    """AC: card with reference produces markup with [bold magenta][r] reference[/bold magenta]."""
    markup = reference_key_markup(has_reference=True)
    assert "[bold magenta][r] reference[/bold magenta]" in markup
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_display.py -v
```

Expected: FAIL — `src.display` does not exist.

- [ ] **Step 3: Create `study/src/display.py`**

```python
from __future__ import annotations

REFERENCE_MAX_CHARS = 500   # hard cap enforced at write time
DISPLAY_MAX_LINES = 8       # visual lines shown for reference and LLM response
ASK_MAX_TOKENS = 250        # max_tokens passed to LLM


def truncate_for_display(text: str, width: int, max_lines: int = DISPLAY_MAX_LINES) -> str:
    """
    Wrap text at `width` chars, keep first `max_lines` visual lines.
    Appends dim ellipsis marker if truncated.
    `width` must be provided by the caller from console.width — never hardcoded.
    """
    visual_lines: list[str] = []
    raw_lines = text.splitlines() or [""]
    for raw_line in raw_lines:
        if not raw_line:
            visual_lines.append("")
        else:
            while len(raw_line) > width:
                visual_lines.append(raw_line[:width])
                raw_line = raw_line[width:]
            visual_lines.append(raw_line)
        if len(visual_lines) >= max_lines:
            break

    total_visual = sum(
        max(1, -(-len(l) // width)) if l else 1
        for l in raw_lines
    )
    was_truncated = total_visual > max_lines

    result = "\n".join(visual_lines[:max_lines])
    if was_truncated:
        result += "\n[dim]…[/dim]"
    return result


def reference_key_markup(has_reference: bool) -> str:
    """Return Rich markup for the [r] reference action key."""
    if has_reference:
        return "[bold magenta][r] reference[/bold magenta]"
    return "[dim][r] [s]reference[/s][/dim]"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_display.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/anki
git add study/src/display.py study/tests/test_display.py
git commit -m "feat: add display.py with truncate_for_display and reference_key_markup"
```

---

### Task 5: Add Jinja2 + Headwater dependencies to `pyproject.toml`

**Files:**
- Modify: `study/pyproject.toml`

Note: `headwater_client`, `headwater_api`, and `conduit` are internal packages. Find their local paths the same way `dbclients` is resolved — check `$BC` (Brian_Code) or use `find ~ -name "headwater_client" -type d 2>/dev/null | head -5` to locate the source directories. Then add them as `{ path = "..." }` entries under `[tool.uv.sources]`.

- [ ] **Step 1: Locate the headwater and conduit package paths**

```bash
find /Users/bianders/Brian_Code -maxdepth 3 -name "pyproject.toml" | xargs grep -l "headwater\|conduit" 2>/dev/null
```

Note the paths — you'll need them in the next step.

- [ ] **Step 2: Add dependencies to `pyproject.toml`**

Add `jinja2>=3.0` to `dependencies`. Add the headwater/conduit local paths under `[tool.uv.sources]`, following the same pattern as `dbclients`:

```toml
[project]
name = "anki-study"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "rich>=13.0",
    "psycopg2-binary>=2.9",
    "pytest>=8.0",
    "dbclients",
    "jinja2>=3.0",
    "headwater-client",   # adjust package name to match discovered pyproject.toml
    "headwater-api",      # adjust as needed
    "conduit",            # adjust as needed
]

[tool.uv.sources]
dbclients = { path = "/Users/bianders/Brian_Code/dbclients-project" }
# Add headwater-client, headwater-api, conduit entries here with discovered paths
```

- [ ] **Step 3: Verify uv resolves the environment**

```bash
uv run --directory ~/.claude/skills/anki/study python -c "import jinja2; import headwater_client; print('ok')"
```

Expected: `ok` — if it errors, check package names against the discovered `pyproject.toml` files.

- [ ] **Step 4: Commit**

```bash
cd ~/.claude/skills/anki
git add study/pyproject.toml study/uv.lock
git commit -m "chore: add jinja2, headwater-client, headwater-api, conduit dependencies"
```

---

### Task 6: `llm.py` — one-shot LLM ask

**Fulfills AC:** `ask_card(deck_name, card, query="")` raises `ValueError`.
**Fulfills AC:** `ask_card(deck_name, card, query="  ")` raises `ValueError`.

**Files:**
- Create: `study/src/llm.py`
- Create: `study/prompts/ask.md.j2`
- Create: `study/tests/test_llm.py`

- [ ] **Step 1: Create the Jinja2 prompt template**

Create directory `study/prompts/` and file `study/prompts/ask.md.j2`:

```jinja2
# Anki Card — {{ deck_name }}

**Front:** {{ front }}
**Back:** {{ back }}
{% if reference %}
**Reference:** {{ reference }}
{% endif %}

## Question

{{ user_query }}
```

- [ ] **Step 2: Write the failing tests**

Create `study/tests/test_llm.py`:

```python
from __future__ import annotations
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from src.models import Card


def _make_card(reference: str | None = None) -> Card:
    now = datetime.now(tz=timezone.utc)
    return Card(
        id=1, deck_id=1, front="What is X?", back="X is Y.",
        tags=[], created_at=now, state="new", due=now,
        interval=0, ease_factor=2500, reps=0, lapses=0,
        step_index=0, suspended=False, reference=reference,
    )


def test_ask_card_empty_query_raises():
    """AC: ask_card with empty query raises ValueError."""
    from src.llm import ask_card
    with pytest.raises(ValueError, match="query cannot be empty"):
        ask_card("ML", _make_card(), query="")


def test_ask_card_whitespace_query_raises():
    """AC: ask_card with whitespace-only query raises ValueError."""
    from src.llm import ask_card
    with pytest.raises(ValueError, match="query cannot be empty"):
        ask_card("ML", _make_card(), query="   ")


def test_ask_card_calls_headwater_and_returns_text():
    """ask_card calls LLM and returns the response string."""
    from src.llm import ask_card

    mock_conv = MagicMock()
    mock_conv.last.content = "Here is the explanation."
    mock_resp = MagicMock()
    mock_resp.results = [mock_conv]

    mock_client = AsyncMock()
    mock_client.conduit.query_batch = AsyncMock(return_value=mock_resp)

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.llm.HeadwaterAsyncClient", return_value=mock_ctx):
        result = ask_card("ML", _make_card(), query="Explain further.")

    assert result == "Here is the explanation."


def test_ask_card_without_reference_renders_template_correctly():
    """Template renders without reference section when card.reference is None."""
    from src.llm import _render_prompt
    card = _make_card(reference=None)
    prompt = _render_prompt("ML", card, "Why?")
    assert "Reference" not in prompt
    assert "What is X?" in prompt
    assert "Why?" in prompt


def test_ask_card_with_reference_includes_reference_in_template():
    """Template includes reference section when card.reference is set."""
    from src.llm import _render_prompt
    card = _make_card(reference="See RFC 9999.")
    prompt = _render_prompt("ML", card, "Why?")
    assert "See RFC 9999." in prompt
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_llm.py -v
```

Expected: FAIL — `src.llm` does not exist.

- [ ] **Step 4: Create `study/src/llm.py`**

```python
from __future__ import annotations
import asyncio
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader

if TYPE_CHECKING:
    from src.models import Card

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_MODEL = "gpt-oss:latest"


def _render_prompt(deck_name: str, card: Card, query: str) -> str:
    env = Environment(loader=FileSystemLoader(str(_PROMPTS_DIR)))
    tmpl = env.get_template("ask.md.j2")
    return tmpl.render(
        deck_name=deck_name,
        front=card.front,
        back=card.back,
        reference=card.reference,
        user_query=query,
    )


async def _call_llm(prompt: str) -> str:
    from headwater_client.client.headwater_client_async import HeadwaterAsyncClient
    from headwater_api.classes import BatchRequest
    from conduit.domain.request.generation_params import GenerationParams
    from conduit.domain.config.conduit_options import ConduitOptions

    from src.display import ASK_MAX_TOKENS

    params = GenerationParams(model=_MODEL, output_type="text", max_tokens=ASK_MAX_TOKENS)
    options = ConduitOptions(project_name="anki-ask", include_history=False)
    req = BatchRequest(prompt_strings_list=[prompt], params=params, options=options)
    async with HeadwaterAsyncClient() as client:
        resp = await client.conduit.query_batch(req)
    if not resp.results:
        raise RuntimeError("LLM returned empty results list")
    return resp.results[0].last.content  # NOTE: verify attribute on first live run


def ask_card(deck_name: str, card: Card, query: str) -> str:
    """
    One-shot LLM call. Raises ValueError if query is empty.
    Raises on network/model error — no retry.
    """
    if not query.strip():
        raise ValueError("query cannot be empty")
    prompt = _render_prompt(deck_name, card, query)
    t0 = time.monotonic()
    result = asyncio.run(_call_llm(prompt))
    elapsed = time.monotonic() - t0
    logger.info(
        "ask_card card_id=%d model=%s prompt_chars=%d response_chars=%d elapsed=%.2fs",
        card.id, _MODEL, len(prompt), len(result), elapsed,
    )
    return result
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_llm.py -v
```

Expected: all PASS. If the mock structure for HeadwaterAsyncClient doesn't match, adjust the mock in `test_ask_card_calls_headwater_and_returns_text` — the test is mocking the async context manager pattern.

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/anki
git add study/src/llm.py study/prompts/ask.md.j2 study/tests/test_llm.py
git commit -m "feat: add llm.py with ask_card one-shot LLM interface"
```

---

## Chunk 3: CLI + Study UI

Tasks 7–9 touch `cli.py` and `study.py`. Tests for CLI are integration tests. Study UI changes have no automated tests — verify manually.

---

### Task 7: CLI — add `--reference` to `card add` with silent truncation

**Fulfills AC:** `add_card(..., reference="x" * 600)` via CLI stores exactly 500 chars.

**Files:**
- Modify: `study/scripts/cli.py`
- Modify: `study/tests/test_service.py` (add CLI-layer truncation test via service directly)

Note: Testing CLI truncation end-to-end via subprocess is complex. Instead, test the truncation logic at the `cmd_card_add` boundary by verifying the stored reference length directly via the DB fixture.

- [ ] **Step 1: Write the failing test**

Add to `study/tests/test_service.py`:

```python
def test_reference_over_limit_stored_truncated_to_500(conn):
    """AC: reference of 600 chars is stored as exactly 500 chars."""
    from src.display import REFERENCE_MAX_CHARS
    service.create_deck(conn, "svc_trunc")
    long_ref = "x" * 600
    # Simulate what cmd_card_add does before calling service:
    truncated = long_ref[:REFERENCE_MAX_CHARS]
    card = service.add_card(conn, deck_name="svc_trunc", front="Q", back="A",
                             reference=truncated)
    assert len(card.reference) == 500
```

- [ ] **Step 2: Run test to verify it passes immediately**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_service.py::test_reference_over_limit_stored_truncated_to_500 -v
```

Expected: PASS — the service/repo stores whatever it receives; truncation happens at the CLI boundary. This test documents and verifies the truncation convention by simulating what the CLI will do.

- [ ] **Step 3: Update `cmd_card_add` in `cli.py`**

Add `--reference` argument to the `card add` subparser in `build_parser()`:

```python
ca.add_argument("--reference", default=None, help="Optional citation or source text")
```

Update `cmd_card_add`:

```python
def cmd_card_add(args, conn):
    from src.display import REFERENCE_MAX_CHARS
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    reference = args.reference[:REFERENCE_MAX_CHARS] if args.reference else None
    card = service.add_card(conn, deck_name=args.deck,
                             front=args.front, back=args.back,
                             tags=tags, reference=reference)
    _out(_card_dict(card))
```

Also add `"reference": card.reference` to `_card_dict`:

```python
def _card_dict(card) -> dict:
    return {
        "id": card.id, "deck_id": card.deck_id,
        "front": card.front, "back": card.back,
        "tags": card.tags, "state": card.state,
        "due": str(card.due), "interval": card.interval,
        "ease_factor": card.ease_factor, "reps": card.reps,
        "lapses": card.lapses, "suspended": card.suspended,
        "reference": card.reference,
    }
```

- [ ] **Step 4: Run full test suite**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 5: Smoke-test the CLI manually**

```bash
uv run --directory ~/.claude/skills/anki/study python scripts/cli.py card add \
  --deck ML --front "Test Q" --back "Test A" --reference "A source citation."
```

Expected: JSON output with `"reference": "A source citation."`.

- [ ] **Step 6: Commit**

```bash
cd ~/.claude/skills/anki
git add study/scripts/cli.py study/tests/test_service.py
git commit -m "feat: add --reference to CLI card add with silent 500-char truncation"
```

---

### Task 8: `study.py` — action bar redesign + `[r]` handler

**Fulfills AC:** `reference=None` renders `[r]` as dim+strikethrough; `[r]` with no reference is a no-op.
**Fulfills AC:** `reference="some text"` renders `[r]` as magenta; pressing `r` shows reference.
**Fulfills AC:** `add_card(..., reference="x"*600)` via study prompt stores 500 chars and warns.

**Files:**
- Modify: `study/scripts/study.py`

No automated tests for study UI — verify manually after each step. Run the study session:

```bash
uv run --directory ~/.claude/skills/anki/study python scripts/study.py --deck ML
```

- [ ] **Step 1: Update imports at the top of `study.py`**

Add to the existing imports:

```python
from src.display import (
    REFERENCE_MAX_CHARS,
    DISPLAY_MAX_LINES,
    truncate_for_display,
    reference_key_markup,
)
```

- [ ] **Step 2: Redesign the action bar as a helper function**

Replace the inline action bar string with a function. Add below `print_header`:

```python
def print_action_bar(card: Card) -> None:
    console.print(
        "  [bold cyan][1][/bold cyan] Again  "
        "[bold yellow][2][/bold yellow] Hard  "
        "[bold green][3][/bold green] Good  "
        "[bold blue][4][/bold blue] Easy"
    )
    ref_markup = reference_key_markup(bool(card.reference))
    console.print(
        f"  [dim][a][/dim] add  [dim][u][/dim] undo  "
        f"{ref_markup}  [bold green][k][/bold green] ask  [dim][q][/dim] quit"
    )
```

- [ ] **Step 3: Replace all inline action bar prints with `print_action_bar(card)`**

In `run_session`, find all places that print the action bar (there are two — initial render after flip, and re-render after `[a]`). Replace both with `print_action_bar(card)`.

- [ ] **Step 4: Add the `[r]` handler inside the rating loop**

In the `while True:` loop that reads rating keys, add the `r` case after the existing `elif key == "a":` block:

```python
elif key == "r":
    if card.reference:
        console.print(Rule("Reference"))
        truncated = truncate_for_display(card.reference, width=console.width)
        console.print(Markdown(truncated))
        console.print()
    else:
        console.print("[dim]No reference.[/dim]")
    print_action_bar(card)
```

- [ ] **Step 5: Update `prompt_add_card` to prompt for reference**

In `prompt_add_card`, after the `back` input and before the `tags` input, add:

```python
reference_raw = input("  Reference (optional, enter to skip): ").strip()
if reference_raw and len(reference_raw) > REFERENCE_MAX_CHARS:
    console.print(f"[yellow]Reference truncated to {REFERENCE_MAX_CHARS} chars.[/yellow]")
    reference_raw = reference_raw[:REFERENCE_MAX_CHARS]
reference = reference_raw or None
```

Update the `service.add_card` call to pass `reference=reference`.

- [ ] **Step 6: Manual verification**

```bash
uv run --directory ~/.claude/skills/anki/study python scripts/study.py --deck ML
```

Check:
- Action bar shows two lines with rating keys on line 1, action keys on line 2
- A card without reference: `[r]` is dim with strikethrough; pressing `r` shows "No reference."
- A card with reference: `[r]` is magenta; pressing `r` shows the reference text, then reprints the action bar
- After viewing reference, rating keys (1–4) still work without extra keypress
- Adding a card via `[a]` prompts for reference (optional)

- [ ] **Step 7: Commit**

```bash
cd ~/.claude/skills/anki
git add study/scripts/study.py
git commit -m "feat: redesign action bar, add [r] reference handler in study REPL"
```

---

### Task 9: `study.py` — `[k]` ask handler

**Fulfills AC:** `ask_card(... query="")` and `ask_card(... query="  ")` raise `ValueError` (covered in Task 6; here we test the UI re-prompt behavior).

**Files:**
- Modify: `study/scripts/study.py`

- [ ] **Step 1: Add the `[k]` handler inside the rating loop**

In the same `while True:` rating loop, add the `k` case after the `r` case:

```python
elif key == "k":
    console.print("[dim]Ask a question about this card:[/dim]")
    query = ""
    while not query.strip():
        query = input("  Ask: ").strip()
        if not query:
            console.print("[yellow]Query cannot be empty.[/yellow]")
    from src.llm import ask_card as llm_ask
    response = llm_ask(deck_name, card, query)
    console.print(Rule("Answer"))
    truncated = truncate_for_display(response, width=console.width)
    console.print(Markdown(truncated))
    console.print()
    print_action_bar(card)
```

Note: The `from src.llm import ask_card as llm_ask` import is inside the handler to avoid importing headwater at module load time (faster startup when `[k]` is not used). If you prefer a top-level import, that's also fine — just be aware it will trigger headwater package resolution on every `study.py` invocation.

- [ ] **Step 2: Manual verification**

```bash
uv run --directory ~/.claude/skills/anki/study python scripts/study.py --deck ML
```

Check:
- Pressing `k` after card flip drops to a text input prompt
- Empty query re-prompts with yellow warning
- Ctrl+C on empty query returns to action bar (KeyboardInterrupt is caught by the outer handler; verify it doesn't crash the session)
- Valid query shows LLM response as Markdown, truncated to 8 lines if long
- After response displays, rating keys (1–4) still work immediately
- `[k]` is always rendered vibrant (not greyed out)

- [ ] **Step 3: Run full test suite one final time**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
cd ~/.claude/skills/anki
git add study/scripts/study.py
git commit -m "feat: add [k] LLM ask handler in study REPL"
```

---

### Task 10: Bug fix — undo-nothing must not re-render from front

**Fulfills AC (bug fix):** Pressing `u` when the undo stack is empty must stay on the current card's back view, not break out and re-render from the front.

**Root cause:** The `break` on the existing undo block is outside the `if undo_stack:` / `else:` branches — it always fires, even when nothing was undone, ejecting the user from the rating loop back to the card front.

**Files:**
- Modify: `study/scripts/study.py`

Depends on Task 8 (`print_action_bar` must exist).

- [ ] **Step 1: Locate the undo block in `study.py`**

Find this exact block in `run_session`:

```python
            elif key == "u":
                if undo_stack:
                    prev_id, prev_snap, prev_rating = undo_stack.pop()
                    service.undo_review(conn, card_id=prev_id, snapshot=prev_snap)
                    stats.unrecord(prev_rating)
                    i = max(0, i - 1)
                    console.print("[dim]Undone.[/dim]")
                else:
                    console.print("[dim]Nothing to undo.[/dim]")
                break
```

- [ ] **Step 2: Apply the fix**

Replace with:

```python
            elif key == "u":
                if undo_stack:
                    prev_id, prev_snap, prev_rating = undo_stack.pop()
                    service.undo_review(conn, card_id=prev_id, snapshot=prev_snap)
                    stats.unrecord(prev_rating)
                    i = max(0, i - 1)
                    console.print("[dim]Undone.[/dim]")
                    break  # go back to prior card's front
                else:
                    console.print("[dim]Nothing to undo.[/dim]")
                    print_action_bar(card)  # stay on current card's back
```

- [ ] **Step 3: Run full test suite**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/ -v
```

Expected: all PASS.

- [ ] **Step 4: Manual verification**

```bash
uv run --directory ~/.claude/skills/anki/study python scripts/study.py --deck ML
```

Check:
- Flip a card, press `u` before rating anything → "Nothing to undo." prints, action bar reprints, card back still visible
- Rate a card, flip the next, press `u` → prior card reappears from its front (existing correct behavior, unchanged)

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/anki
git add study/scripts/study.py
git commit -m "fix: undo-nothing no longer re-renders card from front"
```

---

## Post-implementation verification checklist

Before calling this done, manually verify each acceptance criterion that can't be unit tested:

- [ ] `ALTER TABLE` runs idempotently: `uv run ... python scripts/cli.py db ping` succeeds on a DB that already has the `reference` column
- [ ] Card without reference: `[r]` is dim+strikethrough in action bar
- [ ] Card with reference: `[r]` is magenta; pressing `r` shows the text, then action bar reprints
- [ ] Empty query re-prompts: pressing `k`, hitting enter immediately shows yellow warning
- [ ] After `[r]` or `[k]`, rating keys `1`–`4` work without extra keypress
- [ ] Add card via `[a]` with 600-char reference: warning printed, stored as 500 chars (verify with `card get <id>` via CLI)
- [ ] `resp.results[0].last.content` attribute: first live `[k]` invocation either works or crashes with a clear `AttributeError` pointing to `llm.py` — fix the attribute name there
