---
name: job-application
description: Context artifact for Brian Anderson's job application. Use when working in ~/job_application or on any job application task (resume, cover letter, portfolio, etc.). Orients a new Claude Code instance on the project, file conventions, and its role.
---

# Job Application

Brian Anderson is applying for an internal role at LinkedIn (hiring manager: Scott Olster). The project involves producing six artifacts: resume, cover letter, message to Scott, work portfolio, work example (purpose-built annotation sample), and a 30-60-90 day plan.

All work lives in `~/job_application/`.

## Your Role

**You are a Worker unless Brian explicitly tells you that you are the Manager.**

- **Worker**: execute a specific task, write output to the appropriate `artifacts/` subdirectory, update `manifest.md`. Do not update `scratchpad.md`.
- **Manager**: coordinate the overall project, design tasks, update `scratchpad.md`. Brian talks directly to the Manager. After any key decision, new information from a call or conversation, or artifact state change, update `scratchpad.md` immediately — do not wait until the session ends.

## Orientation Protocol

When starting any session, do this in order:

1. Read `~/job_application/scratchpad.md` — strategic context, role analysis, artifact status
2. Read `~/job_application/manifest.md` — what has been done across all sessions
3. Read `~/job_application/people.json` — key people and their roles in this process
4. Read `~/job_application/registry.json` — full index of all docs; load specific ones as your task requires

Do not load source docs speculatively. The scratchpad has the distilled context — only go deeper when your task demands it. Note: `code_learnings.md` is ~178KB; only load it when working on the portfolio artifact.

If Brian says "implement taskN" or similar, read `~/job_application/tasks/taskN.md` and follow it.

## Task Handoff

Tasks are written by the Manager to `~/job_application/tasks/`. A Worker picks up a task by reading the file and executing it.

**The task file is the contract.** A Worker session starts cold — it has the skill
context but none of the Manager's conversation history. If the task file is ambiguous,
the Worker must ask clarifying questions, which collapses the two sessions into one
and defeats the purpose. A well-written task file makes the Worker fully autonomous.

**Manager**: write task files in this format:

```markdown
# Task: <name>

## Objective
One sentence: what this produces.

## Output
Where to write the result: `artifacts/<name>/v1.md` (or similar)

## Context to read first
- List of files from registry.json the worker should read before starting

## Instructions
Specific guidance, constraints, tone notes, etc.
```

The Instructions section must be complete enough that the Worker never needs to ask
a question. If you find yourself writing a vague instruction, that's a signal to
either make it more specific or break the task into smaller pieces.

**Worker**: when given a task reference (e.g. "implement task1"):
1. Read the task file at `~/job_application/tasks/task1.md`
2. Load any context files listed in it
3. Execute and write output to the specified location
4. Update `manifest.md`

**When to use a Worker session vs a CC subagent (Agent tool)**:
- **Worker session** (you open a new terminal, load this skill, declare role): tasks
  requiring judgment, mid-task decisions, or artifact production (file writes). You
  stay in the loop.
- **CC subagent** (Manager spawns via Agent tool): bounded research, summarization,
  inventory — fully mechanical, output format fully specified upfront. No user
  involvement. See Subagent Delegation Convention for output format requirements.

## File Conventions

```
~/job_application/
  registry.json       # authoritative index — always current, consult this for file list
  manifest.md         # append-only action log
  scratchpad.md       # Manager only
  people.json         # key people
  context/            # read-only reference docs (JD, resume, conv notes, strategy, etc.)
  tasks/              # Manager writes task files here; Workers read them
  artifacts/
    resume/
    cover_letter/
    message_to_scott/
    portfolio/
    work_example/
    30_60_90/
```

## Artifact Status Convention

The Manager MUST update the Artifact Status table in `scratchpad.md` whenever any artifact changes state — created, meaningfully updated, or completed. Workers should flag to the Manager when an artifact has been updated so the Manager can keep the table current. The table is the primary at-a-glance status for the whole project.

---

## Live Drafting Convention

**All artifact drafting happens in the artifacts/ file, not in chat.**

When working on any artifact:
1. Create or open the file at `artifacts/<name>/v1.md` (increment version on major revisions)
2. Write drafts directly to the file — do not paste drafts into chat responses
3. Iterate by editing the file in place — the user watches the file live in a separate tmux pane
4. Use chat only for questions, strategic discussion, and brief summaries of what changed

If Brian says "draft X" or "update the Y section", write it to the file immediately. Do not show the draft in chat first.

When a section is still in progress or needs input, use a `[TODO: ...]` placeholder in the file so Brian can see what's pending.

## Subagent Delegation Convention

When delegating to a subagent (Agent tool) for research or summarization, always
specify the output format in the prompt — not just the task. The agent result lands
directly in the main context; unfiltered raw data (git logs, file listings, large
source files) pollutes it as badly as reading those files directly would.

Every subagent prompt must include:
1. **Output format**: "Return a 3-5 sentence narrative" or "Return a bullet list of
   findings, max 400 words" — never leave format unspecified
2. **Exclusion list**: skip `.venv/`, `__pycache__/`, `.git/` in any file exploration
3. **No raw dumps**: do not return raw git log output, file path listings, or source
   code verbatim — synthesize and interpret

The rule: the agent's job is not done when it reads the data. It is done when it
returns something that fits cleanly into the main context.

---

## Manifest Convention

Append one line per file created or meaningfully edited:

```
- YYYY-MM-DD | created|updated | <path> | <description>
```

---

## Person Research Procedure

Use when Brian provides a name and asks for a mini-bio, or when the Manager identifies a key person worth profiling (panelist, stakeholder, skip-level, etc.).

**Goal:** Produce a structured entry suitable for adding to `people.json`, plus a strategic read of what the profile means for Brian's application.

**Note:** This procedure may eventually be extracted into a standalone "LinkedIn Context" skill as a reusable knowledge-base tool. For now it lives here.

### Steps

1. **Brave search** — run two searches in parallel via the `brave-web-search` skill:
   - `"{name}" LinkedIn`
   - `"{name}" site:{personal-site-if-known}` or `"{name}" {employer}` for triangulation

2. **Fetch** — from search results, fetch in priority order:
   - Their personal website (richest self-authored source)
   - Their Muck Rack or similar journalist profile if they have media background
   - Any other public bio page (author page, speaker bio, etc.)
   - Skip LinkedIn.com directly — it blocks fetching

3. **Compile the bio** — synthesize into a `people.json` entry with these fields:
   - `name`, `title`, `team`, `role_in_application`
   - `background`: career arc, education, notable work, publications, public credentials
   - `notes`: strategic read — what this profile means for Brian specifically (framing, likely panel behavior, remote stance, technical vs. editorial evaluator, etc.)

4. **Update `people.json`** — write the entry directly. If the person already exists, update in place.

5. **Update `panel_prep/v1.md`** if the person is a likely panelist — add a "For [name]" section under Questions to Ask, and note their evaluator profile (what dimension they'll assess Brian on).

6. **Report to Brian in chat** — present the bio narrative + strategic implications. Keep it concise; the full detail lives in the file.

### What makes a good strategic read

Go beyond summarizing the resume. Answer:
- What will this person evaluate Brian on? (editorial judgment? technical rigor? annotation methodology? remote reliability?)
- Are they a natural ally or a friction point on any known concern (builder identity, linguist gap, remote, level)?
- Do they share Brian's arc (content→AI transition)? Does that make them a mirror or a differentiator?
- What framing resonates with their background? (Don't use technical framing with a pure editorial person; don't over-index on journalism with a data scientist.)
- Any prior relationship or shared context with Brian worth noting?
