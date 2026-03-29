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
  README.md          # What silt is; current focus; how to navigate
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

**The flow:** `research/` → synthesize → `knowledge/` → implement → `tools/`

---

## Loading Protocol

Context is expensive. Load the minimum needed, in order:

**Always load at session start (cheap):**
1. `README.md` — current focus, navigation
2. Last 10 lines of `manifest.md` — recent changes
3. `scratchpad.md` — open questions, roadmap

**Load on topic relevance (medium):**
4. `knowledge/<domain>/summary.md` for relevant domains — never load individual notes before checking if the summary answers the question

**Load on specific need only (expensive):**
5. Individual `knowledge/<domain>/<note>.md` — only when the summary is insufficient

**Never load speculatively.** If a domain has a `summary.md`, that is the entry point.
Individual notes are reference material, not orientation material.

Open with:
> "Silt. [Current focus from README]. Last change: [most recent manifest entry]. What are we working on?"

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

`research/` is a staging area, not storage. At the start of any session, check:
- Any `research/` file older than 30 days without a corresponding `knowledge/` note
  gets flagged in `scratchpad.md` as "promote or delete"
- Do not let `research/` accumulate indefinitely

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
```

If you can't fill all five sections, the understanding isn't settled. Leave it in
`research/` or write a stub and mark it `[INCOMPLETE]` at the top.

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

**On new research arriving**
Land in `research/` first. Never write directly to `knowledge/` from raw input.

**On adding a knowledge note**
1. Check Rule 1 (does this concept already have a note?)
2. Check Rule 2 (does the domain need a summary.md first?)
3. Write note using Rule 4 template
4. Update domain `summary.md`
5. Append to `manifest.md`

**On session start**
Check Rule 3: scan `research/` for files older than 30 days without a knowledge/ counterpart. Flag in `scratchpad.md`.

**On domain gap detected**
Create domain directory + stub `summary.md`. Note in `scratchpad.md` as research target.

**On primitive reaching implementation**
Update its README → "Implemented — see `tools/<name>/`". Update `tools/README.md`. Append to manifest.

**On IA change**
Update `README.md` navigation in the same action.

**On "resolve"**
Review session for meaningful skill improvements. Update only if substantive.

---

## Three-Component Model

Silt is itself an instance of the workstream-assistant primitive:

1. **This skill** — orientation heuristics only. Tells an LLM how to navigate, what discipline to apply, when to update what.

2. **The KB** (`knowledge/`) — curated, synthesized notes with mandatory summary layer. The skill points into it; never contains it.

3. **The Collectors** (future) — cron + local model workflows that automate `summary.md` generation and `research/` graduation. Until built, both are manual. See `primitives/workstream-assistant/README.md`.
