---
name: anki
description: >
  Create and manage Anki flashcards. Use this skill whenever the user wants to
  make flashcards, study cards, or memorization aids — whether from a topic
  ("make flashcards on cross-encoders"), from session content ("what did I
  struggle with? make cards"), or from research output. Also use when the user
  wants to view their decks or add cards to an existing deck by name.
---

## Storage

Cards live in `~/.local/state/anki/<deck>.csv` — one pipe-delimited CSV per
deck. The CLI manages all reads and writes; never touch the files directly.

## CLI

All commands use `uv run python ~/.claude/skills/anki/scripts/anki.py`.

```
# Add a single card
uv run python ~/.claude/skills/anki/scripts/anki.py add \
  --deck "ML" --front "..." --back "..."

# Add cards in bulk (preferred for 2+ cards)
uv run python ~/.claude/skills/anki/scripts/anki.py add-batch \
  --deck "ML" --file /tmp/cards.json

# List all decks
uv run python ~/.claude/skills/anki/scripts/anki.py list-decks

# Inspect a deck
uv run python ~/.claude/skills/anki/scripts/anki.py list-cards --deck "ML"
```

For `add-batch`, write a temp JSON file first:
```json
[
  {"front": "What is a cross-encoder?", "back": "A model that jointly encodes a query and document to produce a relevance score, unlike bi-encoders which encode them separately."},
  {"front": "Cross-encoder tradeoff", "back": "Higher accuracy than bi-encoders but much slower — must run inference for every (query, doc) pair at retrieval time."}
]
```

## Drafting cards

Good flashcards are atomic: one question, one answer. Avoid cards that require
recalling a list of unrelated things — split those into separate cards.

**Front**: a specific question or prompt. Avoid vague fronts like "Explain X."
Prefer "What distinguishes X from Y?" or "When would you use X over Y?"

**Back**: concise and direct. One to three sentences. For technical concepts,
include a concrete example or analogy if it meaningfully aids recall.

**Deck naming**: use the domain or topic the user specifies. Keep names short
and consistent — "ML", "Python", "System Design". If the user says "add to the
ML deck", use exactly "ML" as the deck name.

## Batch workflow (preferred for 3+ cards)

1. Draft all cards as a JSON array in memory.
2. Write to `/tmp/anki_cards.json`.
3. Run `add-batch`.
4. Confirm count to the user.

This is faster than calling `add` once per card.
