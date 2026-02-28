---
name: obsidian-vault
description: Automate Obsidian vault operations during Claude Code sessions — create notes, append to notes, log to daily notes, search vault content, and open notes in the Obsidian desktop app. Use when the user wants to capture output from a Claude session into their vault, log decisions or insights, write a meeting note, append to an existing note, or search across their vault. Trigger phrases include "save this to my vault", "add to my daily note", "create an Obsidian note", "log this to Obsidian", "capture this as a note", "search my vault for", or any request to write into or read from an Obsidian vault.
---

# Obsidian Vault Automation

## Prerequisites

- **uv** — Install: https://docs.astral.sh/uv/getting-started/installation/
- **OBSIDIAN_VAULT** env var set to vault path (or pass `--vault` per invocation)
- Optional: **OBSIDIAN_DAILY_NOTES_FOLDER** — subfolder for daily notes (default: vault root)

## Script

`scripts/vault.py` — all operations. No external dependencies.

```
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py [--vault PATH] <command> [args]
```

## Commands

**Create a note** (with optional frontmatter tags):
```bash
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py \
  create "Note Title" --tags tag1 tag2 --body "Initial content"
```

**Append to an existing note** (creates note if it doesn't exist):
```bash
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py \
  append "Note Title" "Content to add"
```

**Append to today's daily note** (creates it if absent, YYYY-MM-DD.md format):
```bash
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py \
  daily "Content to log"
```

**Search vault** (basic text match across all .md files):
```bash
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py \
  search "query" [--excerpt]
```
`--excerpt` shows the matching line with file:line reference.

**Open a note in the Obsidian desktop app** (macOS, uses `obsidian://` URI):
```bash
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py open "Note Title"
```

**List all notes:**
```bash
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py ls
```

## Common Patterns

**Capture a Claude session output as a note:**
```bash
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py \
  create "LLM Eval Patterns 2026-02-27" \
  --tags evals llm \
  --body "## Key insight\n\nExternal behavioral scenarios must live outside the codebase."
```

**Log a decision to daily note:**
```bash
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py \
  daily "Decided to use Dash over Streamlit for Darwin deployment — Dash runs on Flask, enables dual UI+API from one server."
```

**Append to an existing meeting note:**
```bash
uv run ~/.claude/skills/obsidian-vault/scripts/vault.py \
  append "1:1 Colin 2026-02-27" "Action: send 30-60-90 draft by Friday"
```

## Vault Path Resolution

Resolve vault path in this order:
1. `--vault PATH` argument
2. `OBSIDIAN_VAULT` env var
3. Ask the user

Note titles are slugified (special chars stripped, spaces preserved) to match Obsidian's
default filename behavior. Wikilinks use `[[Note Title]]` format as-is.
