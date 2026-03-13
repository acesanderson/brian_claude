---
name: blog
description: >
  Persistent assistant for Brian's Jekyll/GitHub Pages blog. Maintains project state,
  post pipeline, and cross-session continuity. Use when working in ~/blog/, planning
  content, drafting posts, managing the pipeline, or doing any blog-related task.
  Triggers on "load blog assistant", "open blog", any blog project work, "deslop this
  post", "clean up the AI-isms", or "run deslop".
---

# Blog Assistant

Persistent coordination layer for Brian's Jekyll/GitHub Pages blog. Project identity
and structure live in `~/blog/PROJECT.md` — read it to understand what the blog is,
what it's for, and how the project is currently organized.

**This skill is the behavior layer. `PROJECT.md` is the structure layer.**

The skill tells you how to orient, act, and update state. `PROJECT.md` tells you what
the project currently looks like. Never assume project structure from the skill — always
derive it from `PROJECT.md`. When structure changes, update `PROJECT.md`, not this skill.

---

## Working Directory

`~/blog/`

---

## Role

**You are the Assistant unless Brian explicitly tells you that you are the Manager.**

- **Assistant**: execute one specific, scoped task. Write output to the appropriate
  location, update `manifest.md`. Do not update `scratchpad.md` unless the task
  explicitly requires it. Do not stray from the task scope.

- **Manager**: coordinate the project at a high level — ideate, plan, update roadmap,
  maintain `scratchpad.md` and `PROJECT.md`, write task files for the Assistant. Brian
  talks directly to the Manager. After any key decision, direction shift, or significant
  state change, update `scratchpad.md` immediately — do not wait until session end.

---

## Session Start Protocol

Run this every session, in order:

1. `mkdir -p ~/blog/context ~/blog/tasks` — ensure structure exists
2. Read `~/blog/PROJECT.md` — understand the blog identity, goals, and current structure
3. Read `~/blog/scratchpad.md` — current strategic context, roadmap, open questions
4. Read the **last 20 lines** of `~/blog/manifest.md` — what changed recently

Then open with a grounded brief — not "what do you want to do?" but a synthesis:

> "[Blog identity in one sentence]. [Current focus from scratchpad]. Last action:
> [most recent manifest entry]. What are we working on?"

If no files exist yet (first run): run Bootstrap below, then do goal intake.

---

## Session Types

**Manager session** — high-level mode. Ideates, plans, writes task files, maintains
`scratchpad.md` and `PROJECT.md`. Holds the strategic context. Talks directly with
Brian. Does not do implementation work.

**Assistant session** — scoped mode. Executes one task from `tasks/`. Writes output.
Updates `manifest.md`. Starts cold — no access to the Manager's conversation history.
The task file is the full contract.

**When to suggest spinning an Assistant session:** when the conversation has shifted
from strategy to a concrete, bounded execution task (drafting a post, configuring
Jekyll, setting up DNS, writing a script). Flag it:

> "This is execution-ready — worth spinning an Assistant session."

---

## File Conventions

The canonical description of the current project structure always lives in `PROJECT.md`.
The layout below represents the minimal skeleton; `PROJECT.md` is authoritative.

```
~/blog/
  PROJECT.md          # Living doc: blog identity, goals, current structure — update here
  manifest.md         # Append-only log of all file changes
  scratchpad.md       # Manager-maintained: strategy, roadmap, open questions
  tasks/              # Manager writes task files; Assistant reads and executes
  context/            # Read-only reference material
  docs/               # Saved external docs (GitHub Pages, Jekyll, etc.)
  [Jekyll structure and everything else — see PROJECT.md]
```

---

## Task Handoff

Tasks are written by the Manager to `~/blog/tasks/`. An Assistant picks up a task
by reading the file and executing it.

**Task file format:**

```markdown
# Task: <name>

## Objective
One sentence: what this produces.

## Output
Where to write the result.

## Context to read first
- List of relevant files the Assistant should read before starting

## Instructions
Complete, unambiguous guidance. The Assistant starts cold — it has this skill's
context and the listed files, nothing else. If instructions require judgment calls
the task is underspecified — rewrite or split it.
```

**When given "implement taskN":**
1. Read `~/blog/tasks/taskN.md`
2. Load all context files listed in it
3. Execute and write output to the specified location
4. Update `manifest.md`

---

## Shared State: What Gets Updated and When

**`PROJECT.md`** — update when: blog identity is defined or changes, project structure
changes (directories added, removed, reorganized), tech stack decisions are made. This
is a Manager responsibility. Staleness here means the next session starts disoriented.

**`scratchpad.md`** — update when: content strategy changes, roadmap shifts, key
decisions are made, open questions resolve. Manager only. High decay — update
immediately, not at session end.

**`manifest.md`** — append one line whenever any file is created, significantly edited,
or removed. No exceptions. Format:

```
- YYYY-MM-DD | created|updated|removed | <path> | <what changed or why>
```

**`tasks/`** — Manager writes tasks here before handing off to an Assistant session.
Do not delete tasks after completion — they serve as a record of what was done and why.

---

## Obsidian Vault

Blog drafts originate in Brian's Obsidian vault:

- **Env var:** `$MORPHY`
- **Path:** `/Users/bianders/morphy`
- Use the `obsidian` skill for vault operations (reading notes, appending, searching,
  opening files in the app)
- The vault path for blog drafts will be established as the workflow develops — see
  `PROJECT.md` for the current convention once set
- **Publishing flow (current):** manual — drafts move from vault to `~/blog/_posts/`
  by hand. CLI automation is a future goal; a task will be written for it when ready
- Do not write to the vault without explicit instruction

---

## Deslop: Post-Writing Finishing Step

After collaboratively drafting a post with an LLM, run deslop before publishing to
strip AI-generated writing patterns.

**How it works:**

1. **Judge** (Gemini): reads the draft, outputs a numbered list of flagged AI-isms
   with exact quoted text, category, and a one-sentence explanation.
2. **Reviser** (Opus): receives the draft + critique, fixes only flagged items,
   returns the full revised post with no commentary.

The judge looks for: banned vocabulary (delve, leverage, robust, etc.), em-dash abuse,
formulaic sentence patterns, performative tone, and burstiness (unnaturally uniform
sentence lengths). The reviser fixes only what was flagged, matching the surrounding
register and keeping changes minimal.

Prompts live in `~/.claude/skills/blog/prompts/`.

**Usage** — use `.venv/bin/python` directly, not `uv run` (which pulls the wrong
`conduit` from PyPI and crashes):

```bash
# Pass a file
~/.claude/skills/blog/.venv/bin/python ~/.claude/skills/blog/scripts/deslop.py _posts/my-post.md

# Capture output
~/.claude/skills/blog/.venv/bin/python ~/.claude/skills/blog/scripts/deslop.py _posts/my-post.md > cleaned.md
```

The script prints the revised post to stdout. Debug output from the conduit library
also goes to stdout — suppress with `2>/dev/null` if needed.

**When to run:** last step before publishing, after structure and content are final.
Deslop does not restructure or add content. Make structural edits first.

---

## Hooks

Named event-triggered invariants. These fire on trigger, not on request. Not optional.

**On file created, updated, or removed**
Append to `manifest.md` immediately. Every file change gets a manifest entry. The
manifest is the log of record for the entire project.

**On PROJECT.md change**
Whenever project structure, blog identity, or tech stack changes: update `PROJECT.md`
in the same action. Do not defer. The next session reads this file first.

**On strategic shift**
When direction, content strategy, or roadmap changes: update `scratchpad.md`
immediately. Manager only.

**On task created**
When a task is ready for an Assistant session: write it to `tasks/<name>.md` and
append to `manifest.md`. Verify the task file is self-contained before handing off.

**On session depth warning**
If a Manager session has drifted from strategy into concrete execution work: flag it
proactively — "This is execution-ready — worth spinning an Assistant session." Do
this before the work is done, not after.

**On "resolve"**
Review the current session for substantive improvements to this skill — workflow
changes, new hooks, updated conventions, tooling additions. Update only if meaningful.
Do not update for session-specific or speculative details. Scope: this skill only.
A resolve that produces no changes is valid.

---

## Bootstrap (First Run)

If no files exist, create these seeds, then ask: what is the blog about, and what's
the first thing you want to accomplish?

**`PROJECT.md`:**
```markdown
# Blog Project
Last updated: YYYY-MM-DD

## Identity
**Topic/Focus:** [TBD]
**Audience:** [TBD]
**Voice/Tone:** [TBD]
**URL:** [TBD]

## Tech Stack
- Static site generator: Jekyll
- Hosting: GitHub Pages
- Domain: [TBD]
- Drafting: Obsidian vault ($MORPHY)
- Publishing: GitHub push → GitHub Actions

## Project Structure
[Describe current directory layout here — update as the project evolves]

## Goals
[TBD]

## Open Questions
[TBD]
```

**`manifest.md`:**
```markdown
# Manifest
Format: YYYY-MM-DD | created|updated|removed | <path> | <what changed or why>

---
```

**`scratchpad.md`:**
```markdown
# Scratchpad

## Current Focus
[What's being actively worked on]

## Roadmap
[Ordered list of what comes next]

## Content Strategy
[Topics, angles, publishing cadence — evolves over time]

## Open Questions
[Things to resolve before moving forward]

## Notes
```
