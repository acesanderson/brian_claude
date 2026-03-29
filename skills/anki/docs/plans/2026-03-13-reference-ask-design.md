# Design: Reference Field + LLM Ask + UI Polish

**Date:** 2026-03-13

---

## 1. Goal

Add a `reference` field to cards — a human-supplied text citation stored verbatim. During study, expose it via `[r]` and enable one-shot LLM Q&A via `[k]`, both constrained to fit on screen. Tighten the action bar to clearly separate rating keys from action keys.

---

## 2. Constraints and Non-Goals

**In scope:**
- `reference` TEXT column on `cards` table (nullable)
- `[r]` key in study REPL: show reference below card (one-shot reveal, not a toggle)
- `[k]` key in study REPL: prompt for query, call LLM, display response below card
- Reference enforcement: 500-char hard cap at write time (CLI add, study add-card prompt)
- LLM response capped via `max_tokens=250`
- Display truncation: both reference and LLM response truncated to `DISPLAY_MAX_LINES = 8` rendered lines
- Action bar redesign: two-line layout, rating keys on line 1, action keys on line 2
- `[r]` greyed out with strikethrough when `reference is None`; vibrant when present
- Schema migration via `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` inside `init_schema`

**Not in scope — a subagent must not add these:**
- Scrollable reference/response display
- LLM multi-turn / conversation history
- Caching or persisting LLM responses between cards or sessions
- Auto-generating reference at card creation via LLM
- Editing a card's reference after creation (separate `edit` command, future work)
- `add-batch` JSON format change — `reference` key must NOT be added to batch schema
- Streaming LLM responses
- Showing `reference` in `list-cards` or `card history` CLI output
- Any changes to `scripts/anki.py` (the CSV-based CLI)

---

## 3. Interface Contracts

### 3.1 Schema

```sql
-- Added inside init_schema, after all CREATE TABLE statements:
ALTER TABLE cards ADD COLUMN IF NOT EXISTS reference TEXT;
```

### 3.2 Model

```python
@dataclass
class Card:
    # ... existing fields unchanged, reference appended at end ...
    reference: str | None  # None for legacy cards and cards added without reference
```

`reference` is always the last field. `_row_to_card` maps it from index 14.

### 3.3 repo.py

Every SELECT on `cards` must append `, reference` at the end of the column list. `_row_to_card` maps `row[14]` → `reference`.

```python
def add_card(
    conn: psycopg2.extensions.connection,
    deck_id: int,
    front: str,
    back: str,
    tags: list[str] | None = None,
    reference: str | None = None,
) -> Card: ...
```

The INSERT must include `reference` in both the column list and `VALUES`. `NULL` when `reference is None`.

### 3.4 service.py

```python
def add_card(
    conn: psycopg2.extensions.connection,
    deck_name: str,
    front: str,
    back: str,
    tags: list[str] | None = None,
    reference: str | None = None,
) -> Card: ...
```

`snapshot_card` is unchanged — `reference` is not a scheduling field and must not appear in the snapshot dict.

### 3.5 LLM module

New file: `study/src/llm.py`

Template file: `study/prompts/ask.md.j2`, located at `Path(__file__).parent.parent / "prompts" / "ask.md.j2"`.

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

Public interface:

```python
def ask_card(deck_name: str, card: Card, query: str) -> str:
    """
    Render the prompt template, call gpt-oss:latest via HeadwaterAsyncClient,
    return the response text.

    Raises ValueError if query is empty.
    Raises on any network or model error — no retry, no catch.
    Logs: model name, prompt char count, response char count, elapsed seconds.
    """
```

Internal implementation:

```python
import asyncio
import logging
import time
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from headwater_client.client.headwater_client_async import HeadwaterAsyncClient
from headwater_api.classes import BatchRequest
from conduit.domain.request.generation_params import GenerationParams
from conduit.domain.config.conduit_options import ConduitOptions

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_MODEL = "gpt-oss:latest"

async def _ask(prompt: str) -> str:
    params = GenerationParams(model=_MODEL, output_type="text", max_tokens=250)
    options = ConduitOptions(project_name="anki-ask", include_history=False)
    req = BatchRequest(prompt_strings_list=[prompt], params=params, options=options)
    async with HeadwaterAsyncClient() as client:
        resp = await client.conduit.query_batch(req)
    if not resp.results:
        raise RuntimeError("LLM returned empty results list")
    return resp.results[0].last.content  # NOTE: verify attribute name on first run

def ask_card(deck_name: str, card: Card, query: str) -> str:
    if not query.strip():
        raise ValueError("query cannot be empty")
    env = Environment(loader=FileSystemLoader(str(_PROMPTS_DIR)))
    tmpl = env.get_template("ask.md.j2")
    prompt = tmpl.render(
        deck_name=deck_name,
        front=card.front,
        back=card.back,
        reference=card.reference,
        user_query=query,
    )
    t0 = time.monotonic()
    result = asyncio.run(_ask(prompt))
    elapsed = time.monotonic() - t0
    logger.info(
        "ask_card card_id=%d model=%s prompt_chars=%d response_chars=%d elapsed=%.2fs",
        card.id, _MODEL, len(prompt), len(result), elapsed,
    )
    return result
```

### 3.6 Screen constants

Define in `study/src/display.py` (new file), imported by `study.py`:

```python
REFERENCE_MAX_CHARS = 500   # hard cap enforced at write time
DISPLAY_MAX_LINES = 8       # lines of rendered output shown for reference and LLM response
ASK_MAX_TOKENS = 250        # max_tokens passed to LLM
```

### 3.7 Display truncation

Truncation operates on **rendered lines** as seen on screen, not raw text characters. The function receives the text string, measures it against `console.width` (never hardcoded), and returns a truncated string suitable for passing to Rich `Markdown`.

```python
def truncate_for_display(text: str, width: int, max_lines: int = DISPLAY_MAX_LINES) -> str:
    """
    Wrap text at `width` chars, keep first `max_lines` visual lines.
    Appends dim ellipsis if truncated. `width` must come from console.width, never hardcoded.
    """
    visual_lines: list[str] = []
    for raw_line in text.splitlines():
        if not raw_line:
            visual_lines.append("")
        else:
            while len(raw_line) > width:
                visual_lines.append(raw_line[:width])
                raw_line = raw_line[width:]
            visual_lines.append(raw_line)
        if len(visual_lines) >= max_lines:
            break
    was_truncated = len(text.splitlines()) > max_lines or any(
        len(l) > width for l in text.splitlines()
    )
    result = "\n".join(visual_lines[:max_lines])
    if was_truncated:
        result += "\n[dim]…[/dim]"
    return result
```

### 3.8 Action bar layout

Two printed lines. `[r]` conditional rendering:

```
Rate:  [1] Again  [2] Hard  [3] Good  [4] Easy
       [a] add  [u] undo  [~~r~~ reference]  [k] ask  [q] quit   ← when no reference
       [a] add  [u] undo  [r] reference  [k] ask  [q] quit        ← when reference present
```

Rich markup:
- No reference: `[dim][r] [s]reference[/s][/dim]` — both the key letter and the word are dimmed; only the word has strikethrough
- Has reference: `[bold magenta][r] reference[/bold magenta]`

### 3.9 Post-action state after `[r]` and `[k]`

After reference is displayed, the action bar is reprinted and the inner key-reading loop continues immediately. Rating keys (`1`–`4`), `u`, `a`, `q` all work without an intermediate keypress. Pressing `r` again is a no-op if already shown (does not re-render or toggle off).

After `[k]` LLM response is displayed, same behavior: action bar reprints, rating keys work immediately.

### 3.10 CLI (cli.py card add)

```
uv run ... python scripts/cli.py card add \
  --deck ML --front "..." --back "..." [--reference "..."]
```

If `--reference` value exceeds 500 chars: truncate silently, no warning, no error. Store exactly 500 chars.

### 3.11 Study in-session add prompt

```
Deck (default: ML):
Front:
Back:
Reference (optional, enter to skip):
```

If reference input exceeds 500 chars: print `[yellow]Reference truncated to 500 chars.[/yellow]`, store first 500 chars.

---

## 4. Acceptance Criteria

All criteria are phrased to be verifiable without a running terminal:

- `ALTER TABLE cards ADD COLUMN IF NOT EXISTS reference TEXT` executes without error on a DB that already has the column
- `_row_to_card(row)` where `row[14] is None` produces `card.reference is None`
- `snapshot_card(card)` returns a dict where `"reference" not in result`
- `ask_card(deck_name, card, query="")` raises `ValueError`
- `ask_card(deck_name, card, query="  ")` raises `ValueError`
- `truncate_for_display("a" * 1000, width=80, max_lines=8)` returns a string with at most 8 lines before the ellipsis line
- `truncate_for_display("short text", width=80, max_lines=8)` returns the text unchanged with no ellipsis
- A card with `reference=None` produces a Rich markup string containing `[s]reference[/s]` in the action bar render
- A card with `reference="some text"` produces a Rich markup string containing `[bold magenta][r] reference[/bold magenta]`
- `add_card(..., reference="x" * 600)` via CLI stores a `reference` of exactly 500 chars (query the DB to verify)
- `add_card(..., reference="x" * 600)` via study prompt stores 500 chars and prints a truncation warning
- `add-batch` JSON `[{"front": "q", "back": "a"}]` succeeds; resulting card has `reference is None`
- `add-batch` JSON `[{"front": "q", "back": "a", "reference": "x"}]` raises an error or ignores the key — must not silently store it (define which: raise is preferred)
- A card loaded from a DB row with no `reference` column (pre-migration fixture) raises `IndexError` until `init_schema` is run — confirming migration is required

---

## 5. Error Handling / Failure Modes

| Failure | Behavior |
|---------|----------|
| HeadwaterServer unreachable | Unhandled exception propagates → hard crash with traceback |
| `resp.results` is empty list | `RuntimeError("LLM returned empty results list")` raised in `_ask` |
| `resp.results[0].last.content` is wrong attribute | Hard crash on first `[k]` use; fix attribute in `llm.py` |
| LLM returns empty string | Display empty block with no special-casing |
| `reference` column missing on DB start | `init_schema` adds it idempotently on next study session start via `IF NOT EXISTS` |
| User presses `k`, hits enter with empty query | Re-prompt once: `[yellow]Query cannot be empty.[/yellow]`; Ctrl+C cancels and returns to action bar |
| User presses `r` with no reference | Print `[dim]No reference.[/dim]`, reprint action bar, continue loop |
| DB connection stale after long LLM call | Connection error propagates as unhandled exception on next DB operation |
| Reference is one long line exceeding `console.width` | `truncate_for_display` wraps at `width` chars, counts visual lines correctly |

---

## 6. Code Example: Conventions and Style

The following shows the pattern to follow for the `llm.py` module — async internal, sync public interface, logging at the boundary:

```python
# study/src/llm.py
from __future__ import annotations
import asyncio
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models import Card

logger = logging.getLogger(__name__)
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def ask_card(deck_name: str, card: Card, query: str) -> str:
    if not query.strip():
        raise ValueError("query cannot be empty")
    prompt = _render(deck_name, card, query)
    t0 = time.monotonic()
    result = asyncio.run(_call(prompt))
    logger.info("ask_card card_id=%d elapsed=%.2fs", card.id, time.monotonic() - t0)
    return result
```

---

## 7. Domain Language

- **reference**: a free-text field on a card, human-supplied. Not LLM-generated. Stored verbatim. Always optional.
- **ask**: the one-shot LLM interaction triggered by `[k]` during study. Never persisted.
- **action bar**: the two printed lines shown after card flip — line 1 has rating keys, line 2 has action keys.
- **rating keys**: `1`, `2`, `3`, `4` — map to Again/Hard/Good/Easy.
- **action keys**: `a`, `u`, `r`, `k`, `q` — add, undo, reference, ask, quit.
- **display truncation**: hard-cutting rendered output at `DISPLAY_MAX_LINES` visual lines. Does not affect stored value.
- **write truncation**: capping `reference` at `REFERENCE_MAX_CHARS` chars before storage.
- **rendered lines**: visual lines as seen in the terminal after word-wrap at `console.width`, not raw newlines in the stored string.

---

## 8. Invalid State Transitions

- `ask_card` called with `query=""` or `query` containing only whitespace → must raise `ValueError`
- `snapshot_card` must not include `"reference"` key — if it does, undo would silently overwrite a reference edit
- `add-batch` receiving a JSON object with a `"reference"` key must raise `ValueError` (reject unknown keys), not silently store or silently ignore
- Pressing `r` when `card.reference is None` must not block on a key-read — it must print and immediately reprint the action bar
- `truncate_for_display` must never be called with a hardcoded `width` argument; it must always receive `console.width`
- `asyncio.run(_ask(...))` must not be called from within an already-running event loop — `llm.py` is only valid in the synchronous study REPL context
