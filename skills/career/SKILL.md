# Career

Persistent coordination layer for career pivot work. The skill is the workflow/routing
layer; `~/career/` is the knowledge base. The KB's `context/README.md` is the authoritative
IA map — this file never inlines file-to-trigger mappings.

## Three-Part System

| Part | Location | Role |
|------|----------|------|
| Skill | `~/.claude/skills/career/` | Session protocol, hooks, workflow |
| Knowledge base | `~/career/` | Wiki, companies, projects, state |
| Code project | `~/vibe/career-project/` | Python tooling — create when a concrete scripting need arises |

---

## Session Start Protocol

1. Read `~/career/state.md` — session dashboard; derive the opening brief directly from it
2. If `state.md` is absent: read `projects/*/notes.md` + available company notes, synthesize
   a first-pass `state.md`, then proceed
3. Open with a tight brief — not "what do you want to do?" but a synthesis of what's active

---

## Session Types

Declared explicitly ("strategy session", "company session on X") or inferred from context.

**strategy** — default. Big-picture pivot work. Reads `state.md` + relevant project notes.

**company** — focused on one company. Read `companies/<slug>/notes.md` before saying anything.
Never advise on a company without loading its file first.

**application** — artifact production for a specific role. Creates a subdirectory under the
relevant pivot project: `projects/<pivot>-pivot/<company>-<role>/`.

**ingest** — Karpathy ingest workflow. Takes one raw source, produces/updates wiki pages,
updates `context/index.md`, appends to `context/log.md`. See Ingest Workflow below.

---

## Hooks

**On company mention**
When a company name appears that hasn't been loaded this session: check if
`companies/<slug>/notes.md` exists and read it before responding. Never advise on a company
without its file loaded.

**On new company introduced**
When a company appears in conversation with no existing file: create `companies/<slug>/notes.md`
from `~/.claude/skills/career/templates/company-notes.md`, append to `manifest.md`, then proceed.

**On ingest trigger**
Phrases: "ingest this", "process this source", "add this to the wiki", "file this".
Execute the full ingest workflow (see below).

**On person mention**
When a person is named: check `rolodex.json` for an existing entry before advising on
the relationship or drafting any outreach.

**On application triggered**
When a specific role + company is being actively pursued: create
`projects/<pivot>-pivot/<company>-<role>/` as the artifact directory.

**On "create project <name>"**
Create `projects/<name>/notes.md` from `~/.claude/skills/career/templates/project-notes.md`.
Append to `manifest.md`.

**On "open project <name>" / project name mentioned**
Read `projects/<slug>/notes.md` before responding.

**Skill delegation**

| Trigger | Invoke |
|---------|--------|
| Online research, web lookup, URL fetch | `web-search` skill |
| Claude Code, agentic patterns, skill design | `silt` skill |
| Learning plan, what to study, skill gap | `anki` + `tutorialize` skills |
| Obsidian vault, notes, graph | `obsidian` skill |
| Blog post, thought leadership, writing | `blog` skill |
| Postgres, DB queries, Caruana | `postgres` skill |

---

## Ingest Workflow

Fires on ingest trigger. Execute in order — do not skip steps.

1. Identify the source file in `context/raw/`. If not present, ask Brian to drop it there first.
2. Read the source. Discuss key takeaways with Brian (one exchange — don't spiral).
3. Write or update the appropriate wiki page(s) in `context/wiki/`. Use conventions in `context/README.md`.
4. If people appear in the source: update `rolodex.json` entries (create if absent).
5. Update `context/index.md` — add or refresh the entry for each touched page.
6. Append to `context/log.md`: `## [YYYY-MM-DD] ingest | <source title>`
7. Append to `manifest.md`.

**Contradiction rule:** If a new source conflicts with an existing wiki claim, add a
`## Contradictions / Open Questions` section to the wiki page. Do not silently overwrite.

**One source per ingest.** If Brian drops multiple sources, process them one at a time.

---

## Resolve Protocol

Fires when Brian says "resolve". Four steps in order.

**Step 1 — Update `state.md`:**
- Update Active Pivots lines for any pivots touched this session
- Update Active Applications table for any roles in motion
- Update Companies — Needs Attention for any companies touched
- Move resolved Time-Sensitive items out; add new ones with dates
- Carry forward open threads; close any resolved this session
- Update the `_Last updated_` header with today's date + one-phrase session description

**Step 2 — Append to `context/log.md`:**
`## [YYYY-MM-DD] session | <one-phrase summary>`

**Step 3 — Review SKILL.md:**
Scan the conversation for substantive workflow improvements. Update SKILL.md only if
there are real changes to hooks, session types, or workflow. A resolve with no SKILL.md
changes is normal — use judgment.

**Step 4 — Root cleanup audit:**
Run `ls ~/career/` and diff against the canonical allowlist:
- **Files:** `CLAUDE.md`, `state.md`, `manifest.md`, `rolodex.json`, `README.md`
- **Dirs:** `context/`, `companies/`, `projects/`, `meta/`, `docs/`

Surface any items not on the allowlist as a table with recommended action. Do not auto-delete.

---

## IA Reference

For the full file-to-trigger map: read `~/career/context/README.md`.
For the wiki page index: read `~/career/context/index.md`.
These files are the IA — do not duplicate their content here.

---

## Domain Language

| Term | Meaning |
|------|---------|
| **pivot** | A career direction being explored. Top-level strategic unit. |
| **company** | An organization being researched as a potential employer. Lives in `companies/<slug>/`. |
| **project** | A parallel workstream. May be a pivot, skill, brand effort, or meta work. |
| **application** | A specific role being pursued. Artifact sub-unit of a pivot project. |
| **ingest** | Processing a raw source into the wiki. Only operation that writes to `context/wiki/`. |
| **wiki** | LLM-maintained compiled knowledge at `context/wiki/`. Distinct from raw sources. |
| **raw source** | Immutable input document in `context/raw/`. Never modified after drop-in. |
| **entity page** | A wiki page about a specific person, company, or named concept. |
| **resolve** | Session-close protocol. Fires on "resolve". |
| **rolodex** | `rolodex.json` — the person registry at KB root. |
| **session type** | One of: strategy, company, application, ingest. |
