---
name: obsidian
description: "Comprehensive Obsidian vault skill. Use for any vault operation: creating or appending to notes, logging to daily notes, searching the vault, opening notes in the app, writing Obsidian Flavored Markdown (wikilinks, embeds, callouts, properties), using the obsidian CLI for live app operations (backlinks, property:set, tasks, plugin dev, eval), or any question about Siphon-based vault ingestion and vector retrieval. Trigger phrases: save to vault, add to my daily note, create an Obsidian note, log this to Obsidian, search my vault, open this note, wikilink, callout, obsidian property, backlinks, siphon ingest."
---

# Obsidian Vault

## The Vault Is Just a Directory

The Obsidian vault is at `$MORPHY` (`/Users/bianders/morphy`). It is a folder of plain `.md` files.

**For saving, reading, or copying notes — just use file tools directly.** No scripts, no `uv run`, no CLI needed.

```
Save a note   → Write the .md file to /Users/bianders/morphy/Note Title.md
Read a note   → Read /Users/bianders/morphy/Note Title.md
Search notes  → Grep across /Users/bianders/morphy/
Copy content  → Read source, Write destination
```

That's it. Reach for `vault.py` or the obsidian CLI only when you need features those tools actually provide (daily note append with date logic, live app operations, backlinks, etc.).

---

## `vault.py` — When Plain File Ops Aren't Enough

For operations that benefit from structured logic (daily notes with auto-date, tag frontmatter injection, fuzzy note search):

```bash
SCRIPT=~/.claude/skills/obsidian/scripts/vault.py

# Create a note with frontmatter tags
uv run $SCRIPT --vault /Users/bianders/morphy create "Note Title" --tags tag1 tag2 --body "content"

# Append to a note (creates if absent)
uv run $SCRIPT --vault /Users/bianders/morphy append "Note Title" "Content to add"

# Append to today's daily note (auto-dates)
uv run $SCRIPT --vault /Users/bianders/morphy daily "Content to log"

# Search across all notes
uv run $SCRIPT --vault /Users/bianders/morphy search "query" --excerpt

# Open a note in the Obsidian app (macOS)
uv run $SCRIPT --vault /Users/bianders/morphy open "Note Title"
```

Note: `OBSIDIAN_VAULT` env var may not be set — pass `--vault /Users/bianders/morphy` explicitly.

---

## Vault Cleaning — REMOVED

> **Removed 2026-02-28.** A `rich_to_md.py` script was built and briefly included here. It used pure regex/structural passes (no LLM) to detect and convert rich-formatted text artifacts — centered headers, `•` unicode bullets, trailing whitespace — into standard Markdown. It supported single-file and vault-wide modes with an `--inplace` flag.
>
> It was removed because the vault-wide conversion silently corrupted ~1,000 notes. The heuristics (detecting "messy" files by unicode bullets or leading-space counts) were too broad — they matched notes that were intentionally formatted that way. The vault was restored from git without data loss, but the feature is too risky to keep around. If this is ever revisited, it needs per-file dry-run output with explicit approval before any in-place write, and tighter heuristics scoped to known-bad import patterns rather than general formatting signals.

---

## Live App Ops (obsidian CLI)

Requires Obsidian desktop app open and `obsidian` on PATH.

```bash
obsidian read file="My Note"
obsidian append file="My Note" content="New line"
obsidian search query="term" limit=10
obsidian daily:append content="- [ ] Task"
obsidian property:set name="status" value="done" file="My Note"
obsidian backlinks file="My Note"
obsidian tags sort=count counts
obsidian tasks daily todo
```

For the full CLI reference, see `references/cli-commands.md`.

---

## Writing Obsidian Flavored Markdown

When creating or editing vault notes, use OFM syntax — not standard Markdown.
Key differences: `[[wikilinks]]` instead of `[text](path)`, `![[embeds]]`, callouts, and frontmatter properties.

See `references/markdown-syntax.md` for the full syntax reference.

---

## Siphon Integration (WIP)

Siphon (`~/Brian_Code/siphon`) will provide embeddings-based retrieval and wikilink graph traversal over vault content once integrated. See `references/siphon.md` for design intent and implementation plan.

---

## References

| File | Load when... |
|---|---|
| `references/markdown-syntax.md` | writing/editing notes, wikilinks, embeds, callouts, properties |
| `references/cli-commands.md` | using obsidian CLI (backlinks, property:set, plugin dev, eval) |
| `references/siphon.md` | questions about vault ingestion, vector retrieval, graph traversal |
