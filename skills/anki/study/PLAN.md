# Anki Study — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a terminal-native spaced repetition system backed by PostgreSQL, with a machine-friendly JSON CLI and a Rich line-by-line study REPL, using the Anki v2 scheduler algorithm.

**Architecture:** Pure service layer (scheduler + repo) → JSON CLI → thin REPL loop on top. The REPL delegates all state mutations to the same service primitives used by the CLI, so the REPL has no business logic of its own.

**Tech Stack:** Python 3.12+, psycopg2 (via dbclients), Rich, uv, pytest

---

## Prerequisites (human action required before implementation)

Before running any task, create the `anki` database in PostgreSQL and grant permissions:

```sql
CREATE DATABASE anki;
\c anki
GRANT ALL PRIVILEGES ON DATABASE anki TO bianders;
GRANT ALL ON SCHEMA public TO bianders;
```

Environment variables required (already used by dbclients):
- `POSTGRES_PASSWORD`
- `POSTGRES_USERNAME` (defaults to `bianders`)

---

## Explicit Non-Goals

Do not implement the following. If you think one of these is missing, it's intentional:

- **No new-card daily cap.** All new cards are due immediately. There is no `NEW_CARDS_PER_DAY` setting.
- **No sync with AnkiWeb or Anki desktop.** This is a standalone tool.
- **No overdue penalties.** A learning card reviewed 12 hours late is scheduled as if reviewed on time.
- **No per-deck scheduler settings.** One global config.
- **No media, LaTeX, or image support.** Plain text + Markdown only.
- **No import/export.** The DB is the source of truth.
- **No mobile.** Terminal only.

---

## File Map

```
~/.claude/skills/anki/study/
├── pyproject.toml           # uv project: rich, psycopg2-binary, pytest, dbclients path dep
├── scripts/
│   ├── cli.py               # Entry: uv run --directory ... python scripts/cli.py <cmd>
│   └── study.py             # Entry: uv run --directory ... python scripts/study.py
├── src/
│   ├── __init__.py          # empty
│   ├── db.py                # Schema init + get_conn() helper + interval_as_timedelta()
│   ├── models.py            # Dataclasses: Card, Deck, ReviewLog, SessionStats
│   ├── scheduler.py         # Pure functions: Anki v2 SM-2 algorithm, no I/O
│   ├── repo.py              # All SQL — one function per query, returns dataclasses
│   └── service.py           # Business logic: calls repo + scheduler, no SQL
└── tests/
    └── __init__.py          # empty
```

**Responsibility boundaries (enforce strictly):**
- `db.py` — postgres connection only; no domain knowledge; also owns `interval_as_timedelta()` since it knows the dual-semantic convention
- `models.py` — data shapes only; no methods, no I/O
- `scheduler.py` — pure functions; input is card state dict + rating, output is `CardUpdate`; no DB, no I/O, no randomness other than fuzz
- `repo.py` — SQL only, returns dataclasses; no scheduling logic; no business rules
- `service.py` — orchestrates repo + scheduler; the only layer CLI/REPL imports; owns all `ValueError` raising; logs via `logging`
- `cli.py` — parses argv, calls service, prints JSON to stdout; does NOT open a DB connection for the `study` subcommand (closes before exec)
- `study.py` — REPL loop only; reads keypresses, calls service, renders with Rich

---

## Key Conventions (read before touching any file)

### Interval field dual semantics
`cards.interval` stores **minutes** when `state IN ('learning', 'relearning')` and **days** when `state = 'review'` or `state = 'new'`. Never compare or sort intervals across states. Use `interval_as_timedelta(card)` from `db.py` to get a `timedelta` for any card.

### Timezone convention
All datetimes are **UTC-aware** (`datetime.timezone.utc`). `_day_due(now, N)` anchors to **midnight UTC** of the current UTC day + N days. This is an explicit design choice: "due tomorrow" means midnight UTC tomorrow, regardless of local timezone.

### Cram mode and scheduling
Cram mode ignores `due` date but **applies normal scheduling** after each rating. This is a deliberate departure from Anki's filtered decks (which defer scheduling). A subagent must not add special "cram doesn't reschedule" logic.

### Schema init
Both `cli.py` and `study.py` call `init_schema(conn)` at startup. `init_schema` uses `CREATE TABLE IF NOT EXISTS` so it is safe to call repeatedly. It is the only schema management mechanism — do not add migrations.

### Logging
`service.py` uses `logging.getLogger(__name__)`. Log at `DEBUG` for normal operations (card scheduled, deck created), `WARNING` for suspicious values (interval > 365 days), `ERROR` for failures. No other module logs.

---

## Scheduler Reference (Anki v2)

Implement these constants and rules exactly. Do not add constants not listed here.

### Constants

```python
DEFAULT_EASE = 2500        # stored as int (2500 = factor of 2.5)
MIN_EASE = 1300
HARD_MULT = 1.2
EASY_BONUS = 1.3
EASE_AGAIN_PENALTY = -200
EASE_HARD_PENALTY = -150
EASE_EASY_BONUS = 150
NEW_STEPS_MINUTES = [1, 10]       # learning steps
RELEARN_STEPS_MINUTES = [10]      # relearning steps after lapse
GRADUATING_INTERVAL_DAYS = 1      # Good on last learning step
EASY_GRADUATING_INTERVAL_DAYS = 4 # Easy on any learning/new step
MIN_REVIEW_INTERVAL = 1           # minimum days after relearn completes
LEECH_THRESHOLD = 8               # lapses before auto-suspend
```

### Card States

- `new` — never reviewed; `interval=0`, `step_index=0`
- `learning` — in minute-based steps (NEW_STEPS_MINUTES); `interval` = current step in minutes
- `review` — graduated; `interval` = days until next review
- `relearning` — lapsed review card; in RELEARN_STEPS_MINUTES; `interval` = current step in minutes

### Rating Integers

- 1 = Again
- 2 = Hard
- 3 = Good
- 4 = Easy

### Hard behavior asymmetry (important)

**New cards:** Hard → same as Again → step 0 (no "same step" concept for new cards)
**Learning cards:** Hard → stay at current step (do NOT advance)

### Scheduling Rules by State

**State: `new`**
| Rating | Next state | Next interval | Ease delta |
|--------|-----------|---------------|------------|
| Again  | learning  | step 0 (1 min) | 0 |
| Hard   | learning  | step 0 (1 min) — same as Again | 0 |
| Good   | if step_index+1 < len(steps): learning at step_index+1; else: review | steps[step_index+1] or GRADUATING_INTERVAL days | 0 |
| Easy   | review    | EASY_GRADUATING_INTERVAL days | 0 (ease stays DEFAULT_EASE) |

**State: `learning`**
| Rating | Next state | Next interval | Ease delta |
|--------|-----------|---------------|------------|
| Again  | learning  | step 0 (1 min) | 0 |
| Hard   | learning  | steps[step_index] (same step, do not advance) | 0 |
| Good   | if step_index+1 < len(steps): learning at step_index+1; else: review | steps[step_index+1] or GRADUATING_INTERVAL days | 0 |
| Easy   | review    | EASY_GRADUATING_INTERVAL days | 0 |

**State: `review`**
| Rating | Next state | Next interval | Ease delta |
|--------|-----------|---------------|------------|
| Again  | relearning | RELEARN_STEPS_MINUTES[0] (minutes) | EASE_AGAIN_PENALTY; lapses += 1; check leech |
| Hard   | review    | max(ivl+1, round(ivl * HARD_MULT)), fuzzed | EASE_HARD_PENALTY |
| Good   | review    | round(ivl * (ease/1000)), fuzzed, min ivl+1 | 0 |
| Easy   | review    | round(ivl * (ease/1000) * EASY_BONUS), fuzzed, min ivl+1 | EASE_EASY_BONUS |

Ease is clamped to `max(new_ease, MIN_EASE)` after every delta.

**State: `relearning`**
| Rating | Next state | Next interval | Ease delta |
|--------|-----------|---------------|------------|
| Again  | relearning | step 0 | 0 |
| Hard   | relearning | steps[step_index] (same step, do not advance) | 0 |
| Good   | if step_index+1 < len(steps): relearning; else: review | steps[step_index+1] or MIN_REVIEW_INTERVAL days | 0 |
| Easy   | review    | MIN_REVIEW_INTERVAL days | 0 |

After graduating from relearning, `step_index` resets to 0.

### Fuzz Factor

```python
def apply_fuzz(interval: int) -> int:
    """Add ±fuzz to prevent card bunching. interval is in days."""
    import random
    if interval < 2:
        return interval
    if interval == 2:
        fuzz = 1
    elif interval < 7:
        fuzz = max(1, round(interval * 0.1))
    elif interval < 30:
        fuzz = max(2, round(interval * 0.05))
    else:
        fuzz = max(4, round(interval * 0.05))
    return interval + random.randint(-fuzz, fuzz)
```

Fuzz is applied to day-interval calculations only. Never applied to minute-based steps.

### Due Date Calculation

```python
def _day_due(now: datetime, days: int) -> datetime:
    """Midnight UTC of today + N days."""
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return day + timedelta(days=days)

def _minute_due(now: datetime, minutes: int) -> datetime:
    return now + timedelta(minutes=minutes)
```

### Leech Detection

After every lapse (Again on a review card): if `card.lapses >= LEECH_THRESHOLD`, set `suspended = True`. The study REPL must print a visible warning when a card is leeched.

---

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS decks (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- SM-2 state
    -- IMPORTANT: interval semantics depend on state:
    --   state IN ('learning','relearning') -> interval is MINUTES
    --   state IN ('new','review')          -> interval is DAYS
    state TEXT NOT NULL DEFAULT 'new',
    due TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    interval INTEGER NOT NULL DEFAULT 0,
    ease_factor INTEGER NOT NULL DEFAULT 2500,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    step_index INTEGER NOT NULL DEFAULT 0,
    suspended BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS cards_deck_due ON cards(deck_id, due)
    WHERE suspended = FALSE;

CREATE TABLE IF NOT EXISTS review_log (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    reviewed_at TIMESTAMPTZ DEFAULT NOW(),
    rating INTEGER NOT NULL,           -- 1=Again 2=Hard 3=Good 4=Easy
    prior_state TEXT NOT NULL,
    prior_interval INTEGER NOT NULL,
    prior_ease_factor INTEGER NOT NULL,
    new_interval INTEGER NOT NULL,
    new_ease_factor INTEGER NOT NULL
);
```

---

## CLI Contract

Entry: `uv run --directory ~/.claude/skills/anki/study python scripts/cli.py <command> [args]`

All output is JSON to stdout. Errors print a plain-text message to stderr and exit non-zero.

### Commands

```
deck create <name>
deck list
deck delete <name>

card add --deck <name> --front <text> --back <text> [--tags tag1,tag2]
card edit <id> [--front <text>] [--back <text>] [--tags tag1,tag2]
card delete <id>
card list --deck <name>
card get <id>
card history <id>           # full review_log for a card
card suspend <id>
card unsuspend <id>

stats [--deck <name>]       # per-deck or global

db ping                     # verify DB connectivity; exits 0 if ok, 1 if not

study [--deck <name>] [--cram]   # closes DB connection then execs study.py
```

### Response envelope

Success:
```json
{"ok": true, "data": { ... }}
```

Error (stderr + exit 1 — no JSON):
```
Error: deck "ML" not found
```

### `stats` response shape (both cases)

With `--deck`:
```json
{
  "ok": true,
  "data": {
    "deck": "ML",
    "new": 12,
    "learning": 3,
    "review": 8,
    "relearning": 1,
    "suspended": 2,
    "total": 26,
    "daily_counts": [
      {"date": "2026-03-12", "reviewed": 17}
    ]
  }
}
```

Without `--deck` (global — no per-state breakdown, only daily counts):
```json
{
  "ok": true,
  "data": {
    "deck": null,
    "daily_counts": [
      {"date": "2026-03-12", "reviewed": 42}
    ]
  }
}
```

### `card history <id>` response shape

```json
{
  "ok": true,
  "data": [
    {
      "reviewed_at": "2026-03-12T10:00:00+00:00",
      "rating": 3,
      "prior_state": "new",
      "prior_interval": 0,
      "new_interval": 1,
      "prior_ease_factor": 2500,
      "new_ease_factor": 2500
    }
  ]
}
```

### `db ping` response shape

```json
{"ok": true, "data": {"host": "172.16.0.4", "db": "anki"}}
```

---

## Study Session UX

Entry: `uv run --directory ~/.claude/skills/anki/study python scripts/study.py [--deck <name>] [--cram]`

**TTY check:** At startup, if `sys.stdin.isatty()` is False, print `Error: study requires an interactive terminal` and exit 1. Do not attempt `tty.setraw()` on non-TTY stdin.

```
Due: 12 new  |  5 review  |  Deck: ML

--- Card 1 of 17 ---

[front rendered as Rich Markdown]

Press ENTER to flip...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[back rendered as Rich Markdown]

[1] Again  [2] Hard  [3] Good  [4] Easy  [a] Add card  [u] Undo  [q] Quit
```

**Leech warning:** When a card's `suspended` becomes True after rating, print before moving on:
```
[yellow]Leech: this card has been suspended after 8 lapses.[/yellow]
```

**Input handling:**

```python
import sys, tty, termios

def read_key() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
```

**Undo:** Store `(card_id, snapshot)` before each rating. On `u`, pop the stack, restore state via `service.undo_review()`, decrement `i` so the outer loop re-shows the same card. The undo stack holds one entry (undo one card back, not unlimited history).

**Add card mid-session:** On `a`, read front/back/deck/tags with `input()`. Deck defaults to current session deck. Card is added via `service.add_card()`. After adding, resume session at current position (do not add the new card to the current session queue).

**Cram mode:** Show all non-suspended cards in random order. Apply normal scheduling after each rating.

**Session summary** (printed on quit or queue exhaustion):
```
Session complete.
  Reviewed: 17
  Again:  3  (18%)
  Hard:   2  (12%)
  Good:  10  (59%)
  Easy:   2  (12%)
```

---

## Chunk 1: Foundation — pyproject, init files, db, models

### Task 1: pyproject.toml + package init files

**Files:**
- Create: `~/.claude/skills/anki/study/pyproject.toml`
- Create: `~/.claude/skills/anki/study/src/__init__.py`
- Create: `~/.claude/skills/anki/study/tests/__init__.py`

**These two `__init__.py` files must exist before any other task runs pytest.**

- [ ] **Step 1: Create pyproject.toml**

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
]

[tool.uv.sources]
dbclients = { path = "/Users/bianders/Brian_Code/dbclients-project" }
```

- [ ] **Step 2: Create empty `__init__.py` files**

Both files are empty. Create them:
- `src/__init__.py` — empty
- `tests/__init__.py` — empty

- [ ] **Step 3: Verify uv resolves deps**

```bash
uv run --directory ~/.claude/skills/anki/study python -c "import rich; import psycopg2; import pytest; import dbclients; print('ok')"
```
Expected: `ok`

---

### Task 2: models.py

**Files:**
- Create: `~/.claude/skills/anki/study/src/models.py`

- [ ] **Step 1: Write models**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Deck:
    id: int
    name: str
    created_at: datetime


@dataclass
class Card:
    id: int
    deck_id: int
    front: str
    back: str
    tags: list[str]
    created_at: datetime
    state: str        # new | learning | review | relearning
    due: datetime
    interval: int     # MINUTES when state in (learning, relearning); DAYS otherwise
    ease_factor: int  # stored * 1000: 2500 = 2.5
    reps: int
    lapses: int
    step_index: int
    suspended: bool


@dataclass(frozen=True)
class ReviewLog:
    id: int
    card_id: int
    reviewed_at: datetime
    rating: int
    prior_state: str
    prior_interval: int
    prior_ease_factor: int
    new_interval: int
    new_ease_factor: int


@dataclass
class SessionStats:
    reviewed: int = 0
    again: int = 0
    hard: int = 0
    good: int = 0
    easy: int = 0

    def record(self, rating: int) -> None:
        self.reviewed += 1
        if rating == 1:
            self.again += 1
        elif rating == 2:
            self.hard += 1
        elif rating == 3:
            self.good += 1
        elif rating == 4:
            self.easy += 1

    def unrecord(self, rating: int) -> None:
        """Reverse a record() call. Used by undo."""
        self.reviewed = max(0, self.reviewed - 1)
        if rating == 1:
            self.again = max(0, self.again - 1)
        elif rating == 2:
            self.hard = max(0, self.hard - 1)
        elif rating == 3:
            self.good = max(0, self.good - 1)
        elif rating == 4:
            self.easy = max(0, self.easy - 1)
```

- [ ] **Step 2: Sanity check**

```bash
uv run --directory ~/.claude/skills/anki/study python -c "
from src.models import SessionStats
s = SessionStats()
s.record(1); s.record(3); s.record(4)
assert s.reviewed == 3 and s.again == 1
s.unrecord(3)
assert s.reviewed == 2 and s.good == 0
print('models ok')
"
```
Expected: `models ok`

---

### Task 3: db.py — connection + schema + interval helper

**Files:**
- Create: `~/.claude/skills/anki/study/src/db.py`
- Create: `~/.claude/skills/anki/study/tests/test_db.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_db.py
from datetime import timedelta
from src.db import get_conn, init_schema, interval_as_timedelta
from src.models import Card
from datetime import datetime, timezone

def test_schema_init():
    with get_conn() as conn:
        init_schema(conn)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            tables = {row[0] for row in cur.fetchall()}
    assert "decks" in tables
    assert "cards" in tables
    assert "review_log" in tables

def _make_card(state, interval):
    now = datetime.now(tz=timezone.utc)
    return Card(id=1, deck_id=1, front="Q", back="A", tags=[],
                created_at=now, state=state, due=now,
                interval=interval, ease_factor=2500, reps=0,
                lapses=0, step_index=0, suspended=False)

def test_interval_as_timedelta_learning():
    card = _make_card("learning", 10)
    td = interval_as_timedelta(card)
    assert td == timedelta(minutes=10)

def test_interval_as_timedelta_review():
    card = _make_card("review", 7)
    td = interval_as_timedelta(card)
    assert td == timedelta(days=7)

def test_interval_as_timedelta_relearning():
    card = _make_card("relearning", 10)
    td = interval_as_timedelta(card)
    assert td == timedelta(minutes=10)

def test_interval_as_timedelta_new():
    card = _make_card("new", 0)
    td = interval_as_timedelta(card)
    assert td == timedelta(days=0)
```

- [ ] **Step 2: Run to verify fails**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_db.py -v
```
Expected: ImportError

- [ ] **Step 3: Implement db.py**

```python
from __future__ import annotations
from contextlib import contextmanager
from datetime import timedelta
from collections.abc import Generator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg2.extensions
    from src.models import Card

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS decks (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    state TEXT NOT NULL DEFAULT 'new',
    due TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    interval INTEGER NOT NULL DEFAULT 0,
    ease_factor INTEGER NOT NULL DEFAULT 2500,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    step_index INTEGER NOT NULL DEFAULT 0,
    suspended BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS cards_deck_due ON cards(deck_id, due)
    WHERE suspended = FALSE;

CREATE TABLE IF NOT EXISTS review_log (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    reviewed_at TIMESTAMPTZ DEFAULT NOW(),
    rating INTEGER NOT NULL,
    prior_state TEXT NOT NULL,
    prior_interval INTEGER NOT NULL,
    prior_ease_factor INTEGER NOT NULL,
    new_interval INTEGER NOT NULL,
    new_ease_factor INTEGER NOT NULL
);
"""


@contextmanager
def get_conn(dbname: str = "anki") -> Generator[psycopg2.extensions.connection, None, None]:
    from dbclients.clients.postgres import get_db_connection
    with get_db_connection(dbname=dbname) as conn:
        yield conn


def init_schema(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()


def interval_as_timedelta(card: Card) -> timedelta:
    """
    Convert card.interval to a timedelta, respecting dual-semantic convention:
    - learning/relearning: interval is MINUTES
    - new/review: interval is DAYS
    """
    if card.state in ("learning", "relearning"):
        return timedelta(minutes=card.interval)
    return timedelta(days=card.interval)
```

- [ ] **Step 4: Run tests**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_db.py -v
```
Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/anki/study && git add pyproject.toml src/__init__.py src/models.py src/db.py tests/__init__.py tests/test_db.py
git commit -m "feat: foundation — pyproject, models, schema, interval helper"
```

---

## Chunk 2: Scheduler + Repo

### Task 4: scheduler.py — pure SM-2 logic

**Files:**
- Create: `~/.claude/skills/anki/study/src/scheduler.py`
- Create: `~/.claude/skills/anki/study/tests/test_scheduler.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_scheduler.py
import random
from datetime import datetime, timezone
from src.scheduler import schedule, apply_fuzz, CardUpdate

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def _card(state="review", interval=10, ease=2500, reps=3, lapses=0, step_index=0):
    return dict(state=state, interval=interval, ease_factor=ease,
                reps=reps, lapses=lapses, step_index=step_index, suspended=False)


# --- New card ---
def test_new_again_goes_to_step_0():
    u = schedule(_card(state="new", interval=0, reps=0), rating=1, now=NOW)
    assert u.state == "learning"
    assert u.step_index == 0
    assert u.interval == 1  # first step: 1 minute

def test_new_hard_same_as_again():
    u = schedule(_card(state="new", interval=0, reps=0), rating=2, now=NOW)
    assert u.state == "learning"
    assert u.step_index == 0
    assert u.interval == 1

def test_new_good_first_step_advances():
    u = schedule(_card(state="new", interval=0, reps=0, step_index=0), rating=3, now=NOW)
    assert u.state == "learning"
    assert u.step_index == 1
    assert u.interval == 10  # second step

def test_new_good_on_last_step_graduates():
    u = schedule(_card(state="new", interval=0, reps=0, step_index=1), rating=3, now=NOW)
    assert u.state == "review"
    assert u.interval == 1  # GRADUATING_INTERVAL

def test_new_easy_graduates_with_easy_interval():
    u = schedule(_card(state="new", interval=0, reps=0), rating=4, now=NOW)
    assert u.state == "review"
    assert u.interval == 4  # EASY_GRADUATING_INTERVAL

# --- Learning card ---
def test_learning_hard_stays_at_same_step():
    u = schedule(_card(state="learning", interval=10, reps=0, step_index=1), rating=2, now=NOW)
    assert u.state == "learning"
    assert u.step_index == 1
    assert u.interval == 10  # same step, not advanced

def test_learning_hard_different_from_new_hard():
    # Hard on new → step 0; Hard on learning → same step
    u_new = schedule(_card(state="new", reps=0, step_index=1), rating=2, now=NOW)
    u_learning = schedule(_card(state="learning", interval=10, reps=0, step_index=1), rating=2, now=NOW)
    assert u_new.step_index == 0
    assert u_learning.step_index == 1

# --- Review card ---
def test_review_good_interval_uses_ease():
    u = schedule(_card(state="review", interval=10, ease=2500), rating=3, now=NOW)
    assert u.state == "review"
    # 10 * 2.5 = 25; fuzz range for 25: max(2, round(25*0.05))=2 → 23-27
    assert 23 <= u.interval <= 27

def test_review_good_interval_at_least_ivl_plus_one():
    # interval * ease could round down to same as current; must be >= interval+1
    u = schedule(_card(state="review", interval=1, ease=1300), rating=3, now=NOW)
    assert u.interval >= 2  # 1 * 1.3 = 1.3 → rounds to 1; clamped to min ivl+1 = 2

def test_review_again_sends_to_relearn():
    u = schedule(_card(state="review", interval=10, ease=2500), rating=1, now=NOW)
    assert u.state == "relearning"
    assert u.ease_factor == 2300  # 2500 - 200
    assert u.lapses == 1
    assert u.step_index == 0

def test_review_hard_ease_penalty():
    u = schedule(_card(state="review", interval=10, ease=2500), rating=2, now=NOW)
    assert u.ease_factor == 2350  # 2500 - 150
    assert u.state == "review"

def test_review_easy_ease_bonus():
    u = schedule(_card(state="review", interval=10, ease=2500), rating=4, now=NOW)
    assert u.ease_factor == 2650  # 2500 + 150
    assert u.state == "review"

def test_ease_floor_respected():
    u = schedule(_card(state="review", interval=10, ease=1400), rating=1, now=NOW)
    assert u.ease_factor == 1300  # floor: 1400-200=1200 clamped to 1300

# --- Leech ---
def test_leech_suspends_at_threshold():
    u = schedule(_card(state="review", interval=10, lapses=7), rating=1, now=NOW)
    assert u.lapses == 8
    assert u.suspended is True

def test_not_suspended_below_threshold():
    u = schedule(_card(state="review", interval=10, lapses=6), rating=1, now=NOW)
    assert u.lapses == 7
    assert u.suspended is False

# --- Relearning ---
def test_relearning_good_graduates():
    # RELEARN_STEPS_MINUTES = [10], so step_index=0 is last step
    u = schedule(_card(state="relearning", interval=10, step_index=0), rating=3, now=NOW)
    assert u.state == "review"
    assert u.interval == 1  # MIN_REVIEW_INTERVAL

def test_relearning_hard_stays_at_step():
    u = schedule(_card(state="relearning", interval=10, step_index=0), rating=2, now=NOW)
    assert u.state == "relearning"
    assert u.step_index == 0

# --- Fuzz ---
def test_fuzz_small_interval():
    # interval=2: fuzz=1, so result in [1, 3]
    random.seed(42)
    results = {apply_fuzz(2) for _ in range(50)}
    assert results.issubset({1, 2, 3})

def test_fuzz_medium_interval():
    # interval=10: fuzz=max(1, round(10*0.1))=1, so result in [9, 11]
    random.seed(42)
    results = {apply_fuzz(10) for _ in range(50)}
    assert results.issubset({9, 10, 11})

def test_fuzz_large_interval():
    # interval=30: fuzz=max(2, round(30*0.05))=2, so result in [28, 32]
    random.seed(42)
    results = {apply_fuzz(30) for _ in range(50)}
    assert results.issubset(set(range(28, 33)))

def test_fuzz_does_not_apply_to_interval_0():
    assert apply_fuzz(0) == 0

def test_fuzz_does_not_apply_to_interval_1():
    assert apply_fuzz(1) == 1

# --- Due date ---
def test_learning_due_is_minutes():
    u = schedule(_card(state="new", interval=0, reps=0), rating=1, now=NOW)
    expected = NOW + __import__("datetime").timedelta(minutes=1)
    assert u.due == expected

def test_review_due_is_midnight_utc():
    u = schedule(_card(state="new", interval=0, reps=0, step_index=1), rating=3, now=NOW)
    # NOW = 2026-01-01 12:00 UTC; graduating: due = midnight UTC + 1 day = 2026-01-02 00:00
    assert u.due.hour == 0
    assert u.due.minute == 0
    assert u.due.second == 0
```

- [ ] **Step 2: Run to verify fails**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_scheduler.py -v
```
Expected: ImportError

- [ ] **Step 3: Implement scheduler.py**

```python
from __future__ import annotations
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

DEFAULT_EASE = 2500
MIN_EASE = 1300
HARD_MULT = 1.2
EASY_BONUS = 1.3
EASE_AGAIN_PENALTY = -200
EASE_HARD_PENALTY = -150
EASE_EASY_BONUS = 150
NEW_STEPS_MINUTES = [1, 10]
RELEARN_STEPS_MINUTES = [10]
GRADUATING_INTERVAL_DAYS = 1
EASY_GRADUATING_INTERVAL_DAYS = 4
MIN_REVIEW_INTERVAL = 1
LEECH_THRESHOLD = 8


@dataclass
class CardUpdate:
    state: str
    due: datetime
    interval: int
    ease_factor: int
    reps: int
    lapses: int
    step_index: int
    suspended: bool


def apply_fuzz(interval: int) -> int:
    if interval < 2:
        return interval
    if interval == 2:
        fuzz = 1
    elif interval < 7:
        fuzz = max(1, round(interval * 0.1))
    elif interval < 30:
        fuzz = max(2, round(interval * 0.05))
    else:
        fuzz = max(4, round(interval * 0.05))
    return interval + random.randint(-fuzz, fuzz)


def _day_due(now: datetime, days: int) -> datetime:
    day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return day + timedelta(days=days)


def _minute_due(now: datetime, minutes: int) -> datetime:
    return now + timedelta(minutes=minutes)


def schedule(card: dict, rating: int, now: datetime | None = None) -> CardUpdate:
    if now is None:
        now = datetime.now(tz=timezone.utc)

    state = card["state"]
    if state in ("new", "learning"):
        return _schedule_learning(state, card, rating, now)
    elif state == "review":
        return _schedule_review(card, rating, now)
    elif state == "relearning":
        return _schedule_relearning(card, rating, now)
    else:
        raise ValueError(f"Unknown card state: {state!r}")


def _schedule_learning(state: str, card: dict, rating: int, now: datetime) -> CardUpdate:
    steps = NEW_STEPS_MINUTES
    step_index = card["step_index"]
    ease = card["ease_factor"]
    reps = card["reps"]
    lapses = card["lapses"]

    if rating == 1 or (rating == 2 and state == "new"):
        # Again (any) or Hard on new → step 0
        return CardUpdate(
            state="learning", due=_minute_due(now, steps[0]),
            interval=steps[0], ease_factor=ease,
            reps=reps, lapses=lapses, step_index=0, suspended=False,
        )
    elif rating == 2:
        # Hard on learning → same step (do not advance)
        current_ivl = steps[step_index]
        return CardUpdate(
            state="learning", due=_minute_due(now, current_ivl),
            interval=current_ivl, ease_factor=ease,
            reps=reps, lapses=lapses, step_index=step_index, suspended=False,
        )
    elif rating == 3:
        next_step = step_index + 1
        if next_step >= len(steps):
            ivl = GRADUATING_INTERVAL_DAYS
            return CardUpdate(
                state="review", due=_day_due(now, ivl),
                interval=ivl, ease_factor=ease,
                reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
            )
        else:
            new_ivl = steps[next_step]
            return CardUpdate(
                state="learning", due=_minute_due(now, new_ivl),
                interval=new_ivl, ease_factor=ease,
                reps=reps, lapses=lapses, step_index=next_step, suspended=False,
            )
    else:  # Easy
        ivl = EASY_GRADUATING_INTERVAL_DAYS
        return CardUpdate(
            state="review", due=_day_due(now, ivl),
            interval=ivl, ease_factor=ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )


def _schedule_review(card: dict, rating: int, now: datetime) -> CardUpdate:
    interval = card["interval"]
    ease = card["ease_factor"]
    reps = card["reps"]
    lapses = card["lapses"]

    if rating == 1:
        new_ease = max(MIN_EASE, ease + EASE_AGAIN_PENALTY)
        new_lapses = lapses + 1
        suspended = new_lapses >= LEECH_THRESHOLD
        relearn_ivl = RELEARN_STEPS_MINUTES[0]
        return CardUpdate(
            state="relearning", due=_minute_due(now, relearn_ivl),
            interval=relearn_ivl, ease_factor=new_ease,
            reps=reps, lapses=new_lapses, step_index=0, suspended=suspended,
        )
    elif rating == 2:
        new_ease = max(MIN_EASE, ease + EASE_HARD_PENALTY)
        raw = max(interval + 1, round(interval * HARD_MULT))
        new_ivl = apply_fuzz(raw)
        return CardUpdate(
            state="review", due=_day_due(now, new_ivl),
            interval=new_ivl, ease_factor=new_ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )
    elif rating == 3:
        raw = max(interval + 1, round(interval * (ease / 1000)))
        new_ivl = apply_fuzz(raw)
        return CardUpdate(
            state="review", due=_day_due(now, new_ivl),
            interval=new_ivl, ease_factor=ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )
    else:  # Easy
        new_ease = ease + EASE_EASY_BONUS
        raw = max(interval + 1, round(interval * (ease / 1000) * EASY_BONUS))
        new_ivl = apply_fuzz(raw)
        return CardUpdate(
            state="review", due=_day_due(now, new_ivl),
            interval=new_ivl, ease_factor=new_ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )


def _schedule_relearning(card: dict, rating: int, now: datetime) -> CardUpdate:
    steps = RELEARN_STEPS_MINUTES
    step_index = card["step_index"]
    ease = card["ease_factor"]
    reps = card["reps"]
    lapses = card["lapses"]

    if rating == 1:
        return CardUpdate(
            state="relearning", due=_minute_due(now, steps[0]),
            interval=steps[0], ease_factor=ease,
            reps=reps, lapses=lapses, step_index=0, suspended=False,
        )
    elif rating == 2:
        current_ivl = steps[step_index]
        return CardUpdate(
            state="relearning", due=_minute_due(now, current_ivl),
            interval=current_ivl, ease_factor=ease,
            reps=reps, lapses=lapses, step_index=step_index, suspended=False,
        )
    elif rating == 3:
        next_step = step_index + 1
        if next_step >= len(steps):
            return CardUpdate(
                state="review", due=_day_due(now, MIN_REVIEW_INTERVAL),
                interval=MIN_REVIEW_INTERVAL, ease_factor=ease,
                reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
            )
        else:
            new_ivl = steps[next_step]
            return CardUpdate(
                state="relearning", due=_minute_due(now, new_ivl),
                interval=new_ivl, ease_factor=ease,
                reps=reps, lapses=lapses, step_index=next_step, suspended=False,
            )
    else:  # Easy
        return CardUpdate(
            state="review", due=_day_due(now, MIN_REVIEW_INTERVAL),
            interval=MIN_REVIEW_INTERVAL, ease_factor=ease,
            reps=reps + 1, lapses=lapses, step_index=0, suspended=False,
        )
```

- [ ] **Step 4: Run tests**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_scheduler.py -v
```
Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add src/scheduler.py tests/test_scheduler.py
git commit -m "feat: Anki v2 SM-2 scheduler (pure functions)"
```

---

### Task 5: repo.py — all SQL queries

**Files:**
- Create: `~/.claude/skills/anki/study/src/repo.py`
- Create: `~/.claude/skills/anki/study/tests/test_repo.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_repo.py
from datetime import datetime, timezone, timedelta
import pytest
import psycopg2
from src.db import get_conn, init_schema
from src import repo


@pytest.fixture
def conn():
    with get_conn() as c:
        init_schema(c)
        yield c
        with c.cursor() as cur:
            cur.execute("DELETE FROM decks WHERE name LIKE 'test_%'")
        c.commit()


def test_create_and_get_deck(conn):
    deck = repo.create_deck(conn, "test_ml")
    assert deck.name == "test_ml"
    assert deck.id is not None
    fetched = repo.get_deck_by_name(conn, "test_ml")
    assert fetched.id == deck.id


def test_create_deck_duplicate_raises(conn):
    repo.create_deck(conn, "test_dup")
    with pytest.raises(psycopg2.errors.UniqueViolation):
        repo.create_deck(conn, "test_dup")


def test_add_and_get_card(conn):
    deck = repo.create_deck(conn, "test_cards")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A", tags=["x"])
    assert card.front == "Q"
    assert card.state == "new"
    assert card.ease_factor == 2500
    assert card.tags == ["x"]


def test_get_due_cards(conn):
    deck = repo.create_deck(conn, "test_due")
    repo.add_card(conn, deck_id=deck.id, front="Q1", back="A1")
    repo.add_card(conn, deck_id=deck.id, front="Q2", back="A2")
    due = repo.get_due_cards(conn, deck_id=deck.id, limit=10)
    assert len(due) == 2


def test_update_card_state(conn):
    deck = repo.create_deck(conn, "test_update")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    future = datetime.now(tz=timezone.utc) + timedelta(days=1)
    repo.update_card_state(conn, card_id=card.id, state="review",
                           due=future, interval=1, ease_factor=2500,
                           reps=1, lapses=0, step_index=0, suspended=False)
    updated = repo.get_card(conn, card.id)
    assert updated.state == "review"
    assert updated.reps == 1


def test_log_review_and_delete_last(conn):
    deck = repo.create_deck(conn, "test_log")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    log_id_1 = repo.log_review(conn, card_id=card.id, rating=3,
                                prior_state="new", prior_interval=0,
                                prior_ease_factor=2500, new_interval=1,
                                new_ease_factor=2500)
    log_id_2 = repo.log_review(conn, card_id=card.id, rating=1,
                                prior_state="review", prior_interval=1,
                                prior_ease_factor=2500, new_interval=10,
                                new_ease_factor=2300)
    # delete_last should delete log_id_2, not log_id_1
    repo.delete_last_review_log(conn, card.id)
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM review_log WHERE card_id = %s", (card.id,))
        remaining = [r[0] for r in cur.fetchall()]
    assert log_id_1 in remaining
    assert log_id_2 not in remaining


def test_get_daily_counts(conn):
    deck = repo.create_deck(conn, "test_stats")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    repo.log_review(conn, card_id=card.id, rating=3,
                    prior_state="new", prior_interval=0,
                    prior_ease_factor=2500, new_interval=1, new_ease_factor=2500)
    counts = repo.get_daily_counts(conn, days=7)
    assert len(counts) >= 1
    assert "date" in counts[0]
    assert "reviewed" in counts[0]


def test_get_card_history(conn):
    deck = repo.create_deck(conn, "test_history")
    card = repo.add_card(conn, deck_id=deck.id, front="Q", back="A")
    repo.log_review(conn, card_id=card.id, rating=3,
                    prior_state="new", prior_interval=0,
                    prior_ease_factor=2500, new_interval=1, new_ease_factor=2500)
    history = repo.get_card_history(conn, card.id)
    assert len(history) == 1
    assert history[0].rating == 3
```

- [ ] **Step 2: Run to verify fails**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_repo.py -v
```
Expected: ImportError

- [ ] **Step 3: Implement repo.py**

```python
from __future__ import annotations
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from src.models import Card, Deck, ReviewLog

if TYPE_CHECKING:
    import psycopg2.extensions


def create_deck(conn: psycopg2.extensions.connection, name: str) -> Deck:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO decks (name) VALUES (%s) RETURNING id, name, created_at",
            (name,)
        )
        row = cur.fetchone()
    conn.commit()
    return Deck(id=row[0], name=row[1], created_at=row[2])


def get_deck_by_name(conn: psycopg2.extensions.connection, name: str) -> Deck | None:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, created_at FROM decks WHERE name = %s", (name,))
        row = cur.fetchone()
    return Deck(id=row[0], name=row[1], created_at=row[2]) if row else None


def list_decks(conn: psycopg2.extensions.connection) -> list[Deck]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, name, created_at FROM decks ORDER BY name")
        rows = cur.fetchall()
    return [Deck(id=r[0], name=r[1], created_at=r[2]) for r in rows]


def delete_deck(conn: psycopg2.extensions.connection, deck_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM decks WHERE id = %s", (deck_id,))
    conn.commit()


def add_card(
    conn: psycopg2.extensions.connection,
    deck_id: int,
    front: str,
    back: str,
    tags: list[str] | None = None,
) -> Card:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cards (deck_id, front, back, tags)
            VALUES (%s, %s, %s, %s)
            RETURNING id, deck_id, front, back, tags, created_at,
                      state, due, interval, ease_factor, reps, lapses,
                      step_index, suspended
            """,
            (deck_id, front, back, tags or []),
        )
        row = cur.fetchone()
    conn.commit()
    return _row_to_card(row)


def get_card(conn: psycopg2.extensions.connection, card_id: int) -> Card | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, deck_id, front, back, tags, created_at,
                   state, due, interval, ease_factor, reps, lapses,
                   step_index, suspended
            FROM cards WHERE id = %s
            """,
            (card_id,),
        )
        row = cur.fetchone()
    return _row_to_card(row) if row else None


def update_card(
    conn: psycopg2.extensions.connection,
    card_id: int,
    front: str | None = None,
    back: str | None = None,
    tags: list[str] | None = None,
) -> Card:
    updates, values = [], []
    if front is not None:
        updates.append("front = %s"); values.append(front)
    if back is not None:
        updates.append("back = %s"); values.append(back)
    if tags is not None:
        updates.append("tags = %s"); values.append(tags)
    if not updates:
        return get_card(conn, card_id)
    values.append(card_id)
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE cards SET {', '.join(updates)} WHERE id = %s "
            "RETURNING id, deck_id, front, back, tags, created_at, "
            "state, due, interval, ease_factor, reps, lapses, step_index, suspended",
            values,
        )
        row = cur.fetchone()
    conn.commit()
    return _row_to_card(row)


def update_card_state(
    conn: psycopg2.extensions.connection,
    card_id: int,
    state: str,
    due: datetime,
    interval: int,
    ease_factor: int,
    reps: int,
    lapses: int,
    step_index: int,
    suspended: bool,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE cards SET state=%s, due=%s, interval=%s, ease_factor=%s,
                reps=%s, lapses=%s, step_index=%s, suspended=%s
            WHERE id = %s
            """,
            (state, due, interval, ease_factor, reps, lapses,
             step_index, suspended, card_id),
        )
    conn.commit()


def set_suspended(conn: psycopg2.extensions.connection, card_id: int, suspended: bool) -> None:
    with conn.cursor() as cur:
        cur.execute("UPDATE cards SET suspended = %s WHERE id = %s", (suspended, card_id))
    conn.commit()


def delete_card(conn: psycopg2.extensions.connection, card_id: int) -> None:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM cards WHERE id = %s", (card_id,))
    conn.commit()


def list_cards(conn: psycopg2.extensions.connection, deck_id: int) -> list[Card]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, deck_id, front, back, tags, created_at,
                   state, due, interval, ease_factor, reps, lapses,
                   step_index, suspended
            FROM cards WHERE deck_id = %s ORDER BY id
            """,
            (deck_id,),
        )
        rows = cur.fetchall()
    return [_row_to_card(r) for r in rows]


def get_due_cards(
    conn: psycopg2.extensions.connection,
    deck_id: int,
    limit: int = 100,
    now: datetime | None = None,
) -> list[Card]:
    if now is None:
        now = datetime.now(tz=timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, deck_id, front, back, tags, created_at,
                   state, due, interval, ease_factor, reps, lapses,
                   step_index, suspended
            FROM cards
            WHERE deck_id = %s AND due <= %s AND suspended = FALSE
            ORDER BY due ASC
            LIMIT %s
            """,
            (deck_id, now, limit),
        )
        rows = cur.fetchall()
    return [_row_to_card(r) for r in rows]


def get_all_cards_for_cram(
    conn: psycopg2.extensions.connection,
    deck_id: int,
) -> list[Card]:
    import random
    cards = [c for c in list_cards(conn, deck_id) if not c.suspended]
    random.shuffle(cards)
    return cards


def log_review(
    conn: psycopg2.extensions.connection,
    card_id: int,
    rating: int,
    prior_state: str,
    prior_interval: int,
    prior_ease_factor: int,
    new_interval: int,
    new_ease_factor: int,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO review_log
                (card_id, rating, prior_state, prior_interval, prior_ease_factor,
                 new_interval, new_ease_factor)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (card_id, rating, prior_state, prior_interval, prior_ease_factor,
             new_interval, new_ease_factor),
        )
        row = cur.fetchone()
    conn.commit()
    return row[0]


def delete_last_review_log(conn: psycopg2.extensions.connection, card_id: int) -> None:
    """Delete the most recent review_log entry for this card, identified by highest id."""
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM review_log WHERE id = (
                SELECT id FROM review_log WHERE card_id = %s
                ORDER BY id DESC LIMIT 1
            )
            """,
            (card_id,),
        )
    conn.commit()


def get_card_history(
    conn: psycopg2.extensions.connection,
    card_id: int,
) -> list[ReviewLog]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, card_id, reviewed_at, rating, prior_state,
                   prior_interval, prior_ease_factor, new_interval, new_ease_factor
            FROM review_log WHERE card_id = %s ORDER BY id ASC
            """,
            (card_id,),
        )
        rows = cur.fetchall()
    return [
        ReviewLog(id=r[0], card_id=r[1], reviewed_at=r[2], rating=r[3],
                  prior_state=r[4], prior_interval=r[5], prior_ease_factor=r[6],
                  new_interval=r[7], new_ease_factor=r[8])
        for r in rows
    ]


def get_deck_stats(conn: psycopg2.extensions.connection, deck_id: int) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT state, suspended, COUNT(*)
            FROM cards WHERE deck_id = %s
            GROUP BY state, suspended
            """,
            (deck_id,),
        )
        rows = cur.fetchall()
    counts: dict[str, int] = {"new": 0, "learning": 0, "review": 0,
                               "relearning": 0, "suspended": 0, "total": 0}
    for state, suspended, count in rows:
        counts["total"] += count
        if suspended:
            counts["suspended"] += count
        else:
            counts[state] = counts.get(state, 0) + count
    return counts


def get_daily_counts(
    conn: psycopg2.extensions.connection,
    days: int = 7,
    deck_id: int | None = None,
) -> list[dict]:
    """
    Return review counts per day for the last N days.
    Uses parameterized interval: NOW() - (%s * INTERVAL '1 day')
    """
    if deck_id is not None:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DATE(rl.reviewed_at AT TIME ZONE 'UTC') AS day, COUNT(*)
                FROM review_log rl
                JOIN cards c ON rl.card_id = c.id
                WHERE c.deck_id = %s
                  AND rl.reviewed_at >= NOW() - (%s * INTERVAL '1 day')
                GROUP BY day
                ORDER BY day DESC
                """,
                (deck_id, days),
            )
            rows = cur.fetchall()
    else:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DATE(reviewed_at AT TIME ZONE 'UTC') AS day, COUNT(*)
                FROM review_log
                WHERE reviewed_at >= NOW() - (%s * INTERVAL '1 day')
                GROUP BY day
                ORDER BY day DESC
                """,
                (days,),
            )
            rows = cur.fetchall()
    return [{"date": str(r[0]), "reviewed": r[1]} for r in rows]


def restore_card_state(
    conn: psycopg2.extensions.connection,
    card_id: int,
    state: str,
    due: datetime,
    interval: int,
    ease_factor: int,
    reps: int,
    lapses: int,
    step_index: int,
    suspended: bool,
) -> None:
    update_card_state(conn, card_id, state, due, interval, ease_factor,
                      reps, lapses, step_index, suspended)
    delete_last_review_log(conn, card_id)


def _row_to_card(row: tuple) -> Card:
    return Card(
        id=row[0], deck_id=row[1], front=row[2], back=row[3],
        tags=list(row[4]) if row[4] else [],
        created_at=row[5], state=row[6], due=row[7],
        interval=row[8], ease_factor=row[9], reps=row[10],
        lapses=row[11], step_index=row[12], suspended=row[13],
    )
```

- [ ] **Step 4: Run tests**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_repo.py -v
```
Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add src/repo.py tests/test_repo.py
git commit -m "feat: repo layer — all SQL queries"
```

---

## Chunk 3: Service Layer + CLI

### Task 6: service.py

**Files:**
- Create: `~/.claude/skills/anki/study/src/service.py`
- Create: `~/.claude/skills/anki/study/tests/test_service.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_service.py
import pytest
from src.db import get_conn, init_schema
from src import service


@pytest.fixture
def conn():
    with get_conn() as c:
        init_schema(c)
        yield c
        with c.cursor() as cur:
            cur.execute("DELETE FROM decks WHERE name LIKE 'svc_%'")
        c.commit()


def test_create_and_get_deck(conn):
    deck = service.create_deck(conn, "svc_test")
    assert deck.name == "svc_test"


def test_create_deck_duplicate_raises_valueerror(conn):
    service.create_deck(conn, "svc_dup")
    with pytest.raises(ValueError, match="already exists"):
        service.create_deck(conn, "svc_dup")


def test_add_card(conn):
    service.create_deck(conn, "svc_cards")
    card = service.add_card(conn, deck_name="svc_cards", front="Q", back="A")
    assert card.state == "new"


def test_add_card_unknown_deck_raises(conn):
    with pytest.raises(ValueError, match="not found"):
        service.add_card(conn, deck_name="svc_ghost", front="Q", back="A")


def test_review_card_updates_state(conn):
    service.create_deck(conn, "svc_review")
    card = service.add_card(conn, deck_name="svc_review", front="Q", back="A")
    updated = service.review_card(conn, card_id=card.id, rating=3)
    assert updated.state in ("learning", "review")


def test_undo_restores_state_and_deletes_log(conn):
    service.create_deck(conn, "svc_undo")
    card = service.add_card(conn, deck_name="svc_undo", front="Q", back="A")
    snapshot = service.snapshot_card(card)
    service.review_card(conn, card_id=card.id, rating=1)
    service.undo_review(conn, card_id=card.id, snapshot=snapshot)
    restored = service.get_card(conn, card.id)
    assert restored.state == "new"
    # Verify review_log entry was deleted
    history = service.get_card_history(conn, card.id)
    assert len(history) == 0


def test_get_study_queue(conn):
    service.create_deck(conn, "svc_queue")
    service.add_card(conn, deck_name="svc_queue", front="Q1", back="A1")
    service.add_card(conn, deck_name="svc_queue", front="Q2", back="A2")
    cards = service.get_study_queue(conn, deck_name="svc_queue")
    assert len(cards) == 2


def test_get_stats_with_deck(conn):
    service.create_deck(conn, "svc_stats")
    service.add_card(conn, deck_name="svc_stats", front="Q", back="A")
    stats = service.get_stats(conn, deck_name="svc_stats")
    assert stats["new"] == 1
    assert stats["deck"] == "svc_stats"


def test_get_stats_global(conn):
    service.create_deck(conn, "svc_global")
    service.add_card(conn, deck_name="svc_global", front="Q", back="A")
    stats = service.get_stats(conn, deck_name=None)
    assert stats["deck"] is None
    assert "daily_counts" in stats
    # no per-state breakdown for global stats
    assert "new" not in stats
```

- [ ] **Step 2: Run to verify fails**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_service.py -v
```

- [ ] **Step 3: Implement service.py**

```python
from __future__ import annotations
import logging
from typing import TYPE_CHECKING
from src import repo
from src.models import Card, Deck, ReviewLog
from src.scheduler import schedule, CardUpdate

if TYPE_CHECKING:
    import psycopg2.extensions

logger = logging.getLogger(__name__)


def create_deck(conn: psycopg2.extensions.connection, name: str) -> Deck:
    if repo.get_deck_by_name(conn, name):
        raise ValueError(f"Deck '{name}' already exists")
    deck = repo.create_deck(conn, name)
    logger.debug("Created deck '%s' (id=%d)", name, deck.id)
    return deck


def get_deck(conn: psycopg2.extensions.connection, name: str) -> Deck:
    deck = repo.get_deck_by_name(conn, name)
    if not deck:
        raise ValueError(f"Deck '{name}' not found")
    return deck


def list_decks(conn: psycopg2.extensions.connection) -> list[Deck]:
    return repo.list_decks(conn)


def delete_deck(conn: psycopg2.extensions.connection, name: str) -> None:
    deck = get_deck(conn, name)
    repo.delete_deck(conn, deck.id)
    logger.debug("Deleted deck '%s'", name)


def add_card(
    conn: psycopg2.extensions.connection,
    deck_name: str,
    front: str,
    back: str,
    tags: list[str] | None = None,
) -> Card:
    deck = get_deck(conn, deck_name)
    card = repo.add_card(conn, deck_id=deck.id, front=front, back=back, tags=tags or [])
    logger.debug("Added card id=%d to deck '%s'", card.id, deck_name)
    return card


def get_card(conn: psycopg2.extensions.connection, card_id: int) -> Card:
    card = repo.get_card(conn, card_id)
    if not card:
        raise ValueError(f"Card {card_id} not found")
    return card


def get_card_history(
    conn: psycopg2.extensions.connection,
    card_id: int,
) -> list[ReviewLog]:
    get_card(conn, card_id)  # raises if not found
    return repo.get_card_history(conn, card_id)


def edit_card(
    conn: psycopg2.extensions.connection,
    card_id: int,
    front: str | None = None,
    back: str | None = None,
    tags: list[str] | None = None,
) -> Card:
    get_card(conn, card_id)
    return repo.update_card(conn, card_id, front=front, back=back, tags=tags)


def delete_card(conn: psycopg2.extensions.connection, card_id: int) -> None:
    get_card(conn, card_id)
    repo.delete_card(conn, card_id)


def suspend_card(conn: psycopg2.extensions.connection, card_id: int) -> None:
    get_card(conn, card_id)
    repo.set_suspended(conn, card_id, True)


def unsuspend_card(conn: psycopg2.extensions.connection, card_id: int) -> None:
    get_card(conn, card_id)
    repo.set_suspended(conn, card_id, False)


def list_cards(conn: psycopg2.extensions.connection, deck_name: str) -> list[Card]:
    deck = get_deck(conn, deck_name)
    return repo.list_cards(conn, deck.id)


def get_study_queue(
    conn: psycopg2.extensions.connection,
    deck_name: str,
    cram: bool = False,
    limit: int = 200,
) -> list[Card]:
    deck = get_deck(conn, deck_name)
    if cram:
        return repo.get_all_cards_for_cram(conn, deck.id)
    return repo.get_due_cards(conn, deck_id=deck.id, limit=limit)


def snapshot_card(card: Card) -> dict:
    return {
        "state": card.state, "due": card.due, "interval": card.interval,
        "ease_factor": card.ease_factor, "reps": card.reps, "lapses": card.lapses,
        "step_index": card.step_index, "suspended": card.suspended,
    }


def review_card(
    conn: psycopg2.extensions.connection,
    card_id: int,
    rating: int,
) -> Card:
    card = get_card(conn, card_id)
    prior = snapshot_card(card)
    update: CardUpdate = schedule(
        {"state": card.state, "interval": card.interval,
         "ease_factor": card.ease_factor, "reps": card.reps,
         "lapses": card.lapses, "step_index": card.step_index,
         "suspended": card.suspended},
        rating=rating,
    )
    if update.interval > 365:
        logger.warning("Card %d scheduled for %d days — unusually large interval",
                       card_id, update.interval)
    repo.update_card_state(
        conn, card_id,
        state=update.state, due=update.due, interval=update.interval,
        ease_factor=update.ease_factor, reps=update.reps, lapses=update.lapses,
        step_index=update.step_index, suspended=update.suspended,
    )
    repo.log_review(
        conn, card_id=card_id, rating=rating,
        prior_state=prior["state"], prior_interval=prior["interval"],
        prior_ease_factor=prior["ease_factor"],
        new_interval=update.interval, new_ease_factor=update.ease_factor,
    )
    logger.debug("Reviewed card %d: rating=%d state=%s→%s interval=%d",
                 card_id, rating, prior["state"], update.state, update.interval)
    return get_card(conn, card_id)


def undo_review(
    conn: psycopg2.extensions.connection,
    card_id: int,
    snapshot: dict,
) -> None:
    repo.restore_card_state(conn, card_id, **snapshot)
    logger.debug("Undid review for card %d", card_id)


def get_stats(
    conn: psycopg2.extensions.connection,
    deck_name: str | None = None,
) -> dict:
    if deck_name:
        deck = get_deck(conn, deck_name)
        counts = repo.get_deck_stats(conn, deck.id)
        counts["deck"] = deck_name
        counts["daily_counts"] = repo.get_daily_counts(conn, days=7, deck_id=deck.id)
        return counts
    return {
        "deck": None,
        "daily_counts": repo.get_daily_counts(conn, days=7),
    }
```

- [ ] **Step 4: Run tests**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/test_service.py -v
```
Expected: all PASSED

- [ ] **Step 5: Commit**

```bash
git add src/service.py tests/test_service.py
git commit -m "feat: service layer with logging"
```

---

### Task 7: cli.py

**Files:**
- Create: `~/.claude/skills/anki/study/scripts/cli.py`

- [ ] **Step 1: Implement cli.py**

```python
#!/usr/bin/env python
"""Anki study CLI — machine-friendly JSON interface."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import get_conn, init_schema
from src import service


def _out(data: object) -> None:
    print(json.dumps({"ok": True, "data": data}, default=str))


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def _card_dict(card) -> dict:
    return {
        "id": card.id, "deck_id": card.deck_id,
        "front": card.front, "back": card.back,
        "tags": card.tags, "state": card.state,
        "due": str(card.due), "interval": card.interval,
        "ease_factor": card.ease_factor, "reps": card.reps,
        "lapses": card.lapses, "suspended": card.suspended,
    }


def cmd_deck_create(args, conn):
    deck = service.create_deck(conn, args.name)
    _out({"id": deck.id, "name": deck.name, "created_at": str(deck.created_at)})


def cmd_deck_list(args, conn):
    decks = service.list_decks(conn)
    _out([{"id": d.id, "name": d.name} for d in decks])


def cmd_deck_delete(args, conn):
    service.delete_deck(conn, args.name)
    _out({"deleted": args.name})


def cmd_card_add(args, conn):
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    card = service.add_card(conn, deck_name=args.deck,
                             front=args.front, back=args.back, tags=tags)
    _out(_card_dict(card))


def cmd_card_edit(args, conn):
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
    card = service.edit_card(conn, args.id, front=args.front, back=args.back, tags=tags)
    _out(_card_dict(card))


def cmd_card_delete(args, conn):
    service.delete_card(conn, args.id)
    _out({"deleted": args.id})


def cmd_card_list(args, conn):
    cards = service.list_cards(conn, args.deck)
    _out([_card_dict(c) for c in cards])


def cmd_card_get(args, conn):
    card = service.get_card(conn, args.id)
    _out(_card_dict(card))


def cmd_card_history(args, conn):
    history = service.get_card_history(conn, args.id)
    _out([{
        "reviewed_at": str(r.reviewed_at),
        "rating": r.rating,
        "prior_state": r.prior_state,
        "prior_interval": r.prior_interval,
        "new_interval": r.new_interval,
        "prior_ease_factor": r.prior_ease_factor,
        "new_ease_factor": r.new_ease_factor,
    } for r in history])


def cmd_card_suspend(args, conn):
    service.suspend_card(conn, args.id)
    _out({"suspended": args.id})


def cmd_card_unsuspend(args, conn):
    service.unsuspend_card(conn, args.id)
    _out({"unsuspended": args.id})


def cmd_stats(args, conn):
    _out(service.get_stats(conn, deck_name=args.deck))


def cmd_db_ping(args, conn):
    from dbclients.clients.postgres import get_connection_params, PREFERRED_HOST
    params = get_connection_params("anki")
    _out({"host": params["host"], "db": "anki"})


def cmd_study(args, conn):
    """Close DB connection and exec study.py. Do not hold conn open during session."""
    conn.close()
    study_script = Path(__file__).parent / "study.py"
    cmd = [sys.executable, str(study_script)]
    if args.deck:
        cmd += ["--deck", args.deck]
    if args.cram:
        cmd.append("--cram")
    os.execv(sys.executable, cmd)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="anki-study")
    sub = p.add_subparsers(dest="entity", required=True)

    deck_p = sub.add_parser("deck")
    dsub = deck_p.add_subparsers(dest="action", required=True)
    dsub.add_parser("create").add_argument("name")
    dsub.add_parser("list")
    dsub.add_parser("delete").add_argument("name")

    card_p = sub.add_parser("card")
    csub = card_p.add_subparsers(dest="action", required=True)
    ca = csub.add_parser("add")
    ca.add_argument("--deck", required=True)
    ca.add_argument("--front", required=True)
    ca.add_argument("--back", required=True)
    ca.add_argument("--tags", default="")
    ce = csub.add_parser("edit")
    ce.add_argument("id", type=int)
    ce.add_argument("--front"); ce.add_argument("--back"); ce.add_argument("--tags")
    csub.add_parser("delete").add_argument("id", type=int)
    csub.add_parser("list").add_argument("--deck", required=True)
    csub.add_parser("get").add_argument("id", type=int)
    csub.add_parser("history").add_argument("id", type=int)
    csub.add_parser("suspend").add_argument("id", type=int)
    csub.add_parser("unsuspend").add_argument("id", type=int)

    st = sub.add_parser("stats")
    st.add_argument("--deck", default=None)

    db_p = sub.add_parser("db")
    dbsub = db_p.add_subparsers(dest="action", required=True)
    dbsub.add_parser("ping")

    sy = sub.add_parser("study")
    sy.add_argument("--deck", default=None)
    sy.add_argument("--cram", action="store_true")

    return p


DISPATCH = {
    ("deck", "create"): cmd_deck_create,
    ("deck", "list"): cmd_deck_list,
    ("deck", "delete"): cmd_deck_delete,
    ("card", "add"): cmd_card_add,
    ("card", "edit"): cmd_card_edit,
    ("card", "delete"): cmd_card_delete,
    ("card", "list"): cmd_card_list,
    ("card", "get"): cmd_card_get,
    ("card", "history"): cmd_card_history,
    ("card", "suspend"): cmd_card_suspend,
    ("card", "unsuspend"): cmd_card_unsuspend,
    ("stats", None): cmd_stats,
    ("db", "ping"): cmd_db_ping,
    ("study", None): cmd_study,
}


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    action = getattr(args, "action", None)

    fn = DISPATCH.get((args.entity, action))
    if fn is None:
        _err(f"Unknown command: {args.entity} {action}")

    try:
        with get_conn() as conn:
            init_schema(conn)
            fn(args, conn)
    except ValueError as e:
        _err(f"Error: {e}")
    except ConnectionError as e:
        _err(f"DB connection failed: {e}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke tests**

```bash
uv run --directory ~/.claude/skills/anki/study python scripts/cli.py db ping
# Expected: {"ok": true, "data": {"host": "...", "db": "anki"}}

uv run --directory ~/.claude/skills/anki/study python scripts/cli.py deck create SmokeTest
uv run --directory ~/.claude/skills/anki/study python scripts/cli.py deck list

uv run --directory ~/.claude/skills/anki/study python scripts/cli.py card add \
  --deck SmokeTest --front "What is SM-2?" --back "A spaced repetition algorithm"

uv run --directory ~/.claude/skills/anki/study python scripts/cli.py card history 1
# Expected: {"ok": true, "data": []}  (no reviews yet)

uv run --directory ~/.claude/skills/anki/study python scripts/cli.py stats --deck SmokeTest
# Expected: {"ok": true, "data": {"new": 1, "deck": "SmokeTest", ...}}

uv run --directory ~/.claude/skills/anki/study python scripts/cli.py stats
# Expected: {"ok": true, "data": {"deck": null, "daily_counts": [...]}}

uv run --directory ~/.claude/skills/anki/study python scripts/cli.py deck delete SmokeTest
```

All commands must exit 0 and produce valid JSON on stdout.

- [ ] **Step 3: Verify error paths**

```bash
uv run --directory ~/.claude/skills/anki/study python scripts/cli.py card get 999999
# Expected: exit 1, stderr: "Error: Card 999999 not found"

uv run --directory ~/.claude/skills/anki/study python scripts/cli.py deck create ""
# Expected: exit non-zero (argparse will reject empty string before service)
```

- [ ] **Step 4: Commit**

```bash
git add scripts/cli.py
git commit -m "feat: JSON CLI (deck, card, stats, db ping, study)"
```

---

## Chunk 4: Study REPL

### Task 8: study.py

**Files:**
- Create: `~/.claude/skills/anki/study/scripts/study.py`

- [ ] **Step 1: Implement study.py**

```python
#!/usr/bin/env python
"""Anki study REPL — line-by-line interactive study session."""
from __future__ import annotations
import argparse
import sys
import tty
import termios
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule

from src.db import get_conn, init_schema
from src import service
from src.models import Card, SessionStats

console = Console()


def read_key() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def render_card_side(text: str) -> None:
    console.print(Markdown(text))


def print_header(deck_name: str, total: int, position: int) -> None:
    console.print(Rule(f"[bold]{deck_name}[/bold]  Card {position + 1}/{total}"))


def prompt_add_card(conn, current_deck: str) -> None:
    console.print("\n[dim]Add card[/dim]")
    deck_input = input(f"  Deck (default: {current_deck}): ").strip()
    deck_name = deck_input or current_deck
    front = input("  Front: ").strip()
    if not front:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    back = input("  Back: ").strip()
    if not back:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    tags_raw = input("  Tags (comma-separated, optional): ").strip()
    tags = [t.strip() for t in tags_raw.split(",")] if tags_raw else []
    try:
        card = service.add_card(conn, deck_name=deck_name, front=front, back=back, tags=tags)
        console.print(f"[green]Added card {card.id} to '{deck_name}'.[/green]")
        console.print("[dim](Card not added to current session queue.)[/dim]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


def print_session_summary(stats: SessionStats) -> None:
    console.print(Rule("Session complete"))
    if stats.reviewed == 0:
        console.print("[dim]No cards reviewed.[/dim]")
        return
    console.print(f"  Reviewed: {stats.reviewed}")
    for label, count in [("Again", stats.again), ("Hard", stats.hard),
                          ("Good", stats.good), ("Easy", stats.easy)]:
        pct = round(count / stats.reviewed * 100)
        console.print(f"  {label:<6} {count:>3}  ({pct}%)")


def run_session(conn, deck_name: str, cram: bool) -> None:
    queue = service.get_study_queue(conn, deck_name=deck_name, cram=cram)
    if not queue:
        console.print(f"[green]Nothing due in '{deck_name}'.[/green]")
        return

    stats = SessionStats()
    # undo_stack: list of (card_id, snapshot, rating) — rating needed for unrecord()
    undo_stack: list[tuple[int, dict, int]] = []
    i = 0

    while i < len(queue):
        card = queue[i]
        console.clear()
        print_header(deck_name, len(queue), i)
        console.print()
        render_card_side(card.front)
        console.print()
        console.print("[dim]Press ENTER to flip...[/dim]")

        while True:
            key = read_key()
            if key in ("\r", "\n", " "):
                break
            elif key == "q":
                print_session_summary(stats)
                return

        console.print(Rule())
        render_card_side(card.back)
        console.print()
        console.print(
            "  [bold cyan][1][/bold cyan] Again  "
            "[bold yellow][2][/bold yellow] Hard  "
            "[bold green][3][/bold green] Good  "
            "[bold blue][4][/bold blue] Easy  "
            "[dim][a][/dim] Add  [dim][u][/dim] Undo  [dim][q][/dim] Quit"
        )

        while True:
            key = read_key().lower()
            if key in ("1", "2", "3", "4"):
                rating = int(key)
                snapshot = service.snapshot_card(card)
                try:
                    updated = service.review_card(conn, card_id=card.id, rating=rating)
                    stats.record(rating)
                    undo_stack.append((card.id, snapshot, rating))
                    if updated.suspended:
                        console.print(
                            f"\n[yellow]Leech: card {card.id} suspended after "
                            f"{updated.lapses} lapses.[/yellow]"
                        )
                        read_key()  # pause so user sees the warning
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                i += 1
                break
            elif key == "a":
                prompt_add_card(conn, current_deck=deck_name)
                console.print(
                    "  [bold cyan][1][/bold cyan] Again  "
                    "[bold yellow][2][/bold yellow] Hard  "
                    "[bold green][3][/bold green] Good  "
                    "[bold blue][4][/bold blue] Easy  "
                    "[dim][a][/dim] Add  [dim][u][/dim] Undo  [dim][q][/dim] Quit"
                )
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
            elif key == "q":
                print_session_summary(stats)
                return

    print_session_summary(stats)


def main() -> None:
    if not sys.stdin.isatty():
        print("Error: study requires an interactive terminal", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(prog="anki-study")
    parser.add_argument("--deck", default=None)
    parser.add_argument("--cram", action="store_true")
    args = parser.parse_args()

    try:
        with get_conn() as conn:
            init_schema(conn)

            if args.deck is None:
                decks = service.list_decks(conn)
                if not decks:
                    console.print("[red]No decks found. Add cards first.[/red]")
                    sys.exit(1)
                console.print("Available decks:")
                for d in decks:
                    console.print(f"  {d.name}")
                deck_name = input("Deck: ").strip()
            else:
                deck_name = args.deck

            # Validate deck exists before entering session
            service.get_deck(conn, deck_name)  # raises ValueError if not found
            run_session(conn, deck_name=deck_name, cram=args.cram)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except ConnectionError as e:
        console.print(f"[red]DB connection failed: {e}[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted.[/dim]")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Manual smoke test**

```bash
uv run --directory ~/.claude/skills/anki/study python scripts/cli.py deck create Manual
uv run --directory ~/.claude/skills/anki/study python scripts/cli.py card add \
  --deck Manual --front "What is the default ease factor?" --back "2.5 (stored as 2500)"
uv run --directory ~/.claude/skills/anki/study python scripts/cli.py card add \
  --deck Manual --front "How does fuzz prevent bunching?" \
  --back "Adds ±5–15% randomness to intervals so cards don't all cluster on the same day."

uv run --directory ~/.claude/skills/anki/study python scripts/study.py --deck Manual
```

Verify manually:
- Front renders with markdown
- ENTER flips to back
- Rating keys 1–4 advance to next card
- `u` restores previous card state and decrements stats correctly
- `a` drops into add prompt and resumes session (new card not in current queue)
- `q` shows session summary with correct counts
- Non-TTY: `echo "" | uv run ... python scripts/study.py --deck Manual` → exits 1 with error message

- [ ] **Step 3: Test error path for unknown deck**

```bash
uv run --directory ~/.claude/skills/anki/study python scripts/study.py --deck DoesNotExist
# Expected: exit 1, "Error: Deck 'DoesNotExist' not found"
```

- [ ] **Step 4: Commit**

```bash
git add scripts/study.py
git commit -m "feat: study REPL — line-by-line interactive, TTY guard, leech warning"
```

---

## Chunk 5: Full test run + README

### Task 9: Verify full suite + README

**Files:**
- Create: `~/.claude/skills/anki/study/README.md`

- [ ] **Step 1: Run full test suite**

```bash
uv run --directory ~/.claude/skills/anki/study python -m pytest tests/ -v
```
Expected: all PASSED. If any test fails, fix it before continuing. Do not skip.

- [ ] **Step 2: Create README.md**

```markdown
# anki-study

Terminal spaced repetition. PostgreSQL backend. Anki v2 scheduler.

## Prerequisites

- `uv` installed: https://docs.astral.sh/uv/getting-started/installation/
- PostgreSQL running with `anki` database created and `bianders` granted access
- `POSTGRES_PASSWORD` env var set

## Usage

### Verify DB connectivity

    uv run --directory ~/.claude/skills/anki/study python scripts/cli.py db ping

### CLI (machine-friendly JSON)

    uv run --directory ~/.claude/skills/anki/study python scripts/cli.py deck create ML
    uv run --directory ~/.claude/skills/anki/study python scripts/cli.py card add \
      --deck ML --front "Question" --back "Answer"
    uv run --directory ~/.claude/skills/anki/study python scripts/cli.py stats --deck ML
    uv run --directory ~/.claude/skills/anki/study python scripts/cli.py card history 1

### Study session

    uv run --directory ~/.claude/skills/anki/study python scripts/study.py --deck ML
    uv run --directory ~/.claude/skills/anki/study python scripts/study.py --deck ML --cram

### Run tests

    uv run --directory ~/.claude/skills/anki/study python -m pytest tests/ -v

## Design notes

- `interval` field dual semantics: minutes for learning/relearning, days for review
- Due dates anchor to midnight UTC
- Cram mode applies normal scheduling (unlike Anki filtered decks)
- No new-card daily cap: all new cards are due immediately
- Cards with 8+ lapses are auto-suspended (leech threshold)
```

- [ ] **Step 3: Final commit**

```bash
git add README.md
git commit -m "docs: README for anki-study"
```

---

## Known Limitations / v2 Candidates

- No new-card daily cap (intentional for v1; add `NEW_CARDS_PER_DAY` constant + filter in `get_due_cards` for v2)
- Undo is single-level (one card back)
- No persistent session log (summary lost if terminal clears)
- FSRS upgrade path: `scheduler.py` is fully isolated; swapping algorithms is a single-file change
- Tags with commas are not supported (CLI splits on `,`); use spaces instead
- `--no-deck stats` returns no per-state breakdown (only daily counts)
