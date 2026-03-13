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
