---
name: silt
description: >
  Personal LLM best practices workstream. Use when working in ~/silt/, researching
  context engineering / NLP / agentic patterns, designing new LLM tooling primitives,
  or doing any meta-work around Claude Code workflows and personal AI infrastructure.
  Triggers on "load silt", "open silt", or any work in ~/silt/.
---

# Silt

Personal knowledge base and tooling lab for LLM best practices, context engineering,
and agentic workflow design. The project is explicitly evolutionary — the IA reflects
current understanding and will change.

**This skill is the orientation layer, not the knowledge layer.**
Do not put domain knowledge here. The files are the knowledge. This skill tells you
how to navigate them.

---

## Working Directory

`~/silt/`

---

## The IA

```
~/silt/
  index.md           # Global knowledge map — entry point for all navigation
  README.md          # What silt is; current focus
  scratchpad.md      # Active ideation, open questions, roadmap — high decay
  manifest.md        # Append-only log of all changes
  knowledge/         # Settled, synthesized understanding — organized by domain
    <domain>/
      summary.md     # REQUIRED once domain has 3+ notes — domain synthesis, always loaded first
      <note>.md      # Individual notes — loaded only on specific need
  primitives/        # Design specs for tools in progress or under consideration
  research/          # Staging area for raw inputs — NOT permanent storage
  tools/             # Scripts that graduated from primitives/
```

### What lives where

| You have... | It goes to... |
|---|---|
| A synthesized understanding of a technique | `knowledge/<domain>/<note>.md` |
| Raw research output (Perplexity, arxiv, transcript) | `research/` — staging only |
| A design spec or idea for a tool | `primitives/<name>/README.md` |
| A working script that emerged from a primitive | `tools/` |
| An active thought, open question, or next step | `scratchpad.md` |
| A log entry | `manifest.md` |
| A valuable Q&A synthesis worth keeping | `research/` (staged) → `knowledge/` (promoted) |

**The flow:** `research/` → synthesize → `knowledge/` → implement → `tools/`

---

## Loading Protocol

Context is expensive. Load the minimum needed, in order:

**Always load at session start (cheap):**
1. `index.md` — global knowledge map; use this to identify relevant domains and notes
2. `scratchpad.md` — active focus and open questions
3. Last 10 lines of `manifest.md` — recent changes

**Load on topic relevance (medium):**
4. `knowledge/<domain>/summary.md` for relevant domains — never load individual notes before checking if the summary answers the question

**Load on specific need only (expensive):**
5. Individual `knowledge/<domain>/<note>.md` — only when the summary is insufficient

**Never load speculatively.** `index.md` is the navigation entry point. Domain summaries
are the second level. Individual notes are reference material, not orientation material.

Open with:
> "Silt. Last change: [most recent manifest entry]. What are we working on?"

---

## Discipline Rules (enforced, not optional)

### Rule 1: Check before creating

Before writing a new `knowledge/` note, scan the relevant domain directory. If a note
on the same concept exists: **update it, do not create a new one.** Duplication is the
primary failure mode of a growing KB. One canonical note per concept.

### Rule 2: Summary gate

A domain with 3 or more notes **must** have a `summary.md` before a new note can be
added. If `summary.md` doesn't exist, create it first. Format:

```markdown
# <Domain> — Summary
Last updated: YYYY-MM-DD

## What this domain covers
[2-3 sentences]

## Notes in this domain
| File | What it covers |
|---|---|
| note.md | one line |

## Key findings
[Bulleted synthesis of the most important things across all notes]

## Open questions
[What we don't know yet or need to research]
```

The summary is updated every time a note is added or significantly changed.
The Collector will eventually automate this. Until then, it's manual.

### Rule 3: Graduate or prune research/

`research/` is a staging area, not storage. Files age differently by type — check the
`type:` frontmatter field:

- **Research output** (`type: research-output`, or no type field): flag as "promote or delete"
  after **30 days** without a corresponding `knowledge/` note
- **Research spec** (`type: research-spec`): flag as "execute or prune" after **14 days**.
  A spec that doesn't get executed quickly usually won't. The spec itself is never promoted
  to `knowledge/`; only the outputs produced by executing it are. Prune the spec once executed.

Do not let `research/` accumulate indefinitely.

### Rule 4: Note template

Every `knowledge/` note must have these sections (in order):

```markdown
# <Concept Name>

*Source: [where this came from] ([date])*

## What it is
[1-3 sentences — the concept, plainly stated]

## How it works
[Mechanics, key components, relevant details]

## Applicability to this stack
[Specifically: how does this apply to claude-history, silt, Aquifer, conduit, etc.]

## Tradeoffs / limitations
[What it doesn't do well; when not to use it]

## Eval angle
[How would we know if this works better than what we have? Be specific.]

## Related
[Links to other knowledge/ notes that connect to this concept — use relative paths]
```

If you can't fill the first five sections, the understanding isn't settled. Leave it in
`research/` or write a stub and mark it `[INCOMPLETE]` at the top. `## Related` can be
empty on creation and filled in as the KB grows.

### Rule 5: Stale flagging

When a note is superseded or outdated:
- Add `> [!warning] Stale as of YYYY-MM-DD: [reason]` at the top — do NOT silently rewrite
- Update the domain `summary.md` to reflect the change
- Append to `manifest.md` with `stale` tag

Old understanding is worth preserving with context. Knowing *why* we moved on from
something is as useful as the current best practice.

---

## Manifest Convention

```
- YYYY-MM-DD | created|updated|stale|removed | <path> | <what changed>
```

Append after every file change. No exceptions.

---

## Hooks

### On Ingest (new source arriving)
Land raw input in `research/` first. Then:
1. Read the source; identify key concepts and which existing notes it relates to
2. Check Rule 1 and Rule 2 before writing
3. Write new `knowledge/` note(s) using Rule 4 template
4. Update `index.md` — add new entry under correct domain section
5. Update domain `summary.md` — notes table and key findings
6. Update `## Related` in any existing notes this new note connects to
7. Append to `manifest.md`

A single source should touch **3–10 files** (new note + index + domain summary + related notes).
If you're only touching 1–2, you're not cross-referencing enough.

### On Query (answering a question against the KB)
1. Read `index.md` first — identify relevant domains and specific notes
2. Read domain `summary.md` for relevant domains
3. Drill into individual notes only as needed
4. Synthesize answer with citations (reference specific notes by path)
5. If the synthesis was non-trivial: stage it to `research/` as `YYYY-MM-DD-query-<slug>.md`
   marked "query output — consider promoting to knowledge/"

Valuable Q&A outputs compound the KB just like ingested sources do. Don't let them
disappear into chat history.

### On Lint (periodic health check)
Run on request or when the KB feels stale. Check for:
- **Orphan pages**: notes with no inbound `## Related` links from other notes
- **Missing concepts**: terms mentioned in multiple notes that lack their own page
- **Stale claims**: notes in fast-moving domains not updated in 60+ days (Rule 5 candidates)
- **Index completeness**: every `knowledge/` note appears in `index.md`
- **Summary gaps**: domains with 3+ notes lacking `summary.md`
- **research/ age**: research outputs older than 30 days without a `knowledge/` note; research specs older than 14 days without execution (Rule 3)

Surface findings in `scratchpad.md` as a dated lint report. Don't fix everything at once —
prioritize the orphan pages and missing concepts first.

### On adding a knowledge note (existing hook, expanded)
1. Check Rule 1 (does this concept already have a note?)
2. Check Rule 2 (does the domain need a summary.md first?)
3. Write note using Rule 4 template (including `## Related`)
4. Update `index.md`
5. Update domain `summary.md`
6. Update `## Related` in connected notes
7. Append to `manifest.md`

### On session start
Check Rule 3: scan `research/` and flag in `scratchpad.md`:
- Research outputs older than 30 days without a `knowledge/` counterpart → "promote or delete"
- Research specs (`type: research-spec`) older than 14 days without execution → "execute or prune"

### On domain gap detected
Create domain directory + stub `summary.md`. Note in `scratchpad.md` as research target.

### On primitive reaching implementation
Update its README → "Implemented — see `tools/<name>/`". Update `tools/README.md`. Append to manifest.

### On IA change
Update `README.md` and `index.md` in the same action.

### On "resolve"
Review session for meaningful skill improvements. Update only if substantive.

---

## Three-Component Model

Silt is itself an instance of the workstream-assistant primitive:

1. **This skill** — orientation heuristics only. Tells an LLM how to navigate, what discipline to apply, when to update what.

2. **The KB** (`knowledge/`) — curated, synthesized notes with mandatory summary layer. The skill points into it; never contains it.

3. **The Collectors** (future) — cron + local model workflows that automate `summary.md` generation and `research/` graduation. Until built, both are manual. See `primitives/workstream-assistant/README.md`.
