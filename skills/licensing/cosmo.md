# Cosmo — Subskill

Cosmo is LinkedIn Learning's internal course production management system. Every licensed
course requires a **project record** and a linked **course record**, both filled with
deal-specific metadata before production can begin.

This subskill governs all Claude-assisted Cosmo operations within the licensing workflow.

---

## Postgres is the SOT — not JSON files

**Blob data lives in the `cosmo_blobs` table in the `catalog` postgres DB on Caruana.**
This is the single source of truth going forward. Do not create or edit standalone JSON
files as blobs. The legacy JSON files in `data/` (debugging_with_genai.json,
data_science_portfolio.json) existed before the DB was built — they are not the pattern
for new work.

---

## Read Operations — Daily Checks

These are the most frequent Cosmo operations. Chrome is required for `milestones`; all others hit the DB only.

```bash
# All blobs for a partner
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli list --partner <slug>

# All blobs needing attention
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli list --needs-resync

# QC: inspect field values for a specific blob
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli show <id|slug>

# Live milestone state from Cosmo (Chrome required)
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli milestones <id|slug>

# Fill run history for a blob
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli runs <id|slug>
```

**Sync state check (DB vs Cosmo):** `cosmo-cli list --partner <slug>` shows DB status. `cosmo-cli milestones` reads live Cosmo state. If a blob shows `entered` in DB but milestones 1–2 aren't complete in Cosmo, HITL 2 is still pending.

---

## Roadmap

| Phase | Approach | Status |
|---|---|---|
| Now | Playwright browser automation via Chrome CDP (remote-debugging-port=9222) | Active |
| Now | Clone fill only — human creates the cloned record in Cosmo UI first | Active |
| Future | Headless API scripting with official CPS service account credentials | Pending Infosec/CPS approval (design spec at `docs/superpowers/specs/`) |
| Future | Full new-record-from-scratch automation (no manual clone step) | Not yet scoped |

**Why not spoofed credentials now:** Infosec is explicit — do not spoof human credentials for
automated scripts. The Playwright CDP approach uses an already-authenticated human browser
session and is the compliant interim path.

---

## Session Prerequisites — Chrome Remote Debugging

All Cosmo automation (read.py, fill.py) requires Chrome running with remote debugging enabled
and logged into Cosmo. **Check this at the start of any Cosmo session:**

```bash
curl -s http://localhost:9222/json/version | python3 -m json.tool | grep Browser
```

If the curl fails or returns nothing, Chrome is not ready. Prompt the user:

> "Chrome isn't running with remote debugging. Please run `chrome-debug`, then navigate to `https://www.linkedin.com/cosmo/` and confirm you're logged in. Let me know when ready."

Do not proceed with any read.py or fill.py calls until the check passes.

---

## Safeguards — Hard Rules

**fill.py may only write to Cosmo records that a human explicitly registered.**

The enforcement chain:
1. **Human action required to enter the allowlist.** Project ID and course ID enter the system
   only via `cosmo-cli set-ids`, which requires Brian to first manually clone a record in the
   Cosmo UI and hand over the IDs. There is no automated clone step.
2. **`--blob-id` is required.** fill.py will not run without it. No bypass flag exists.
3. **Pre-flight DB validation before any writes.** On startup, fill.py:
   - Looks up the blob in `cosmo_blobs` by `--blob-id`
   - Verifies `status == 'ready'` (set-ids was called)
   - Verifies `project_id` and `course_id` in the input JSON match the DB record exactly
   - Aborts with a clear error if any check fails — no partial writes, no fallback
4. **`cosmo_blobs` is the allowlist.** The only way a project_id/course_id pair is in the DB
   with `status = ready` is if Brian ran `set-ids` on it. Hand-crafted JSON blobs pointing at
   arbitrary Cosmo records will fail the pre-flight check.

**The implication for Claude:** Never run fill.py without `--blob-id`. Never construct a blob
JSON from scratch and feed it directly to fill.py. Always go through `cosmo-cli new` →
`cosmo-cli edit` → `cosmo-cli set-ids` (HITL) → export → fill.py.

---

## HITL Structure — Two Bookends

Every Cosmo record creation has human-in-the-loop steps at both ends:

**HITL 1 (beginning):** Brian clones a source project in the Cosmo UI, gets the new
`project_id` and `course_id` from the URL, and passes them to Claude via `set-ids`.
The fill script cannot run until this happens.

If the course already exists in Cosmo and only the project_id is unknown, use
`cosmo-cli lookup <course_id>` to retrieve it (Chrome required).

**HITL 2 (end):** After `fill.py` completes, Brian manually:
1. Adds the instructor contract rows in the Contracting tab
2. Clicks through the 2 milestone gates to hand off to production

Claude handles everything between the two bookends.

---

## What Exists

**Project root:** `/Users/bianders/vibe/licensing-project/cosmo/`

```
cosmo/
├── fill.py                        # Main automation script (Playwright + Chrome CDP)
├── read.py                        # Reads live Cosmo project into a blob JSON (CDP)
├── lookup.py                      # Looks up project_id by course_id via /cosmo/projects search (CDP)
├── scripts/
│   └── scrape_anaconda_toc.py    # Thinkific TOC scraper (standalone inline-script)
├── data/
│   ├── debugging_with_genai.json  # Historical blob — project 3835001 (already entered)
│   └── data_science_portfolio.json # Historical blob — project 3834002 (already entered)
├── cosmo/
│   ├── models.py                  # Pydantic v2 models (CosmoCloneInput, ProjectRecord, etc.)
│   ├── db.py                      # Postgres persistence layer (cosmo_blobs, cosmo_runs)
│   ├── cli.py                     # cosmo-cli entry point
│   └── nav.py                     # FSM-safe navigation layer — use instead of raw page.goto()
├── docs/
│   ├── notes.md                   # Canonical field reference, interaction patterns, gotchas
│   ├── fsm-map.md                 # Ember FSM map: error signatures, resource map, live test results
│   ├── cps-service-account-request.md
│   └── superpowers/specs/
│       └── 2026-04-15-cosmo-clone-fill-design.md  # Historical API-based spec (superseded)
├── pyproject.toml
└── uv.lock
```

**Status:** Clone fill flow fully operational. All 8 Anaconda records entered (2026-04-16).
FSM navigation layer (`nav.py`) implemented 2026-04-16 — see `docs/fsm-map.md`.
Full record creation from scratch is TBD.

---

## Persistence Layer

Blobs live in the `catalog` postgres DB on Caruana (auto-discovered via dbclients).

### `cosmo_blobs`

| Column | Type | Notes |
|---|---|---|
| `id` | serial PK | internal anchor for FK and CLI |
| `uuid` | uuid | stable external identifier — never changes |
| `slug` | text unique | mutable label, auto-generated from partner+title at creation |
| `partner_slug` | text | e.g. `anaconda` |
| `status` | enum | `draft` \| `ready` \| `entered` |
| `project_id` | int nullable | null until user provides after cloning |
| `course_id` | int nullable | null until user provides after cloning |
| `blob` | jsonb | full `CosmoCloneInput` content |
| `blob_updated_at` | timestamptz | updates on every blob edit |
| `needs_resync` | bool | set true when blob edited while `entered`; reset on successful run |
| `last_run_at` | timestamptz | timestamp of last successful fill.py execution |

**Status transitions:**
- `draft → ready`: `set-ids` command — validates all required fields, then sets IDs
- `ready → entered`: `mark-entered` or automatic via `log-run --mode live --exit-status success`
- Editing blob while `entered` → `needs_resync = true` (status stays `entered`)

### `cosmo_runs`

Replaces `logs/runs.jsonl`. One row per fill.py execution (live or dry-run).
Columns: `blob_id`, `ran_at`, `mode`, `exit_status`, `input_snapshot`, `results`, `summary`, `error_message`.

### `set-ids` validation gate

Before `draft → ready`, all of these must be non-null/non-empty:
- `project.project_name`, `project.due_date`, `project.draft_toc_url`
- All four strategy fields (`summary`, `goals`, `fit`, `target_audience`)
- `course.title` (not blank or "TK")
- `course.suggested_course_titles` (non-empty list)
- `project.instructor_contract.instructor_id`, `subscription_royalty_rate`, `content_delivery_due_date`

---

## cosmo-cli — Command Reference

```bash
# Setup (one-time)
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli init-db

# Create a draft blob
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli new \
  --partner anaconda --title "Course Title"
# With full blob JSON pre-populated:
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli new \
  --partner anaconda --title "Course Title" --blob-json path/to/blob.json

# List
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli list
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli list --partner anaconda --status draft
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli list --needs-resync

# Show blob as JSON
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli show <id|slug>

# Edit a field (dotted path into blob; values auto-coerced from string)
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli edit <id|slug> course.title "New Title"
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli edit <id|slug> project.strategy_summary "..."
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli edit <id|slug> \
  course.suggested_course_titles '["Course A", "Course B"]'

# HITL 1: Brian provides IDs after cloning in UI
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli set-ids <id|slug> \
  --project-id 3836001 --course-id 8163000

# After fill.py runs successfully
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli mark-entered <id|slug>

# Delete a blob (blocks on status=entered without --force)
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli delete <id|slug>
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli delete <id|slug> --force

# Look up project_id for a course_id via /cosmo/projects search (Chrome required)
# Dismisses stale pills, types into #search_course_id, reads project_id from first result
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli lookup <course_id>
# Standalone (prints raw project_id integer — pipe-friendly):
uv run --project ~/vibe/licensing-project/cosmo python lookup.py <course_id>

# Validate blob schema (Pydantic check — no DB writes; canonical readiness check)
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli validate <id|slug>

# Open Cosmo record in browser
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli open <id|slug>

# Run history
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli runs <id|slug>

# Log a fill.py run (reads JSON from stdin)
echo '{"input_snapshot": {...}, "results": [...], "summary": {...}}' | \
  uv run --project ~/vibe/licensing-project/cosmo cosmo-cli log-run <id|slug> \
  --mode live --exit-status success
```

---

## Current Automation Scope

**fill.py automates:**
- Project name, strategy tab (4 fields), planning tab, production scope tab,
  production tab (TOC/background/script links), contracting tab (`Note to Content Operations` only),
  course details tab (title, description, short description), suggested courses typeahead

**Not automated (manual only):**
- Cosmo clone step (HITL 1)
- Instructor contract rows in Contracting tab (HITL 2)
- Milestone completion — milestones 1 and 2 (HITL 2; see Milestone Taxonomy below)

---

## Milestone Taxonomy

Cosmo projects move through 14 milestones in sequence. Each has a set of blocking criteria
that must pass before it can be completed. Brian owns only the first two; everything after
is handed off to Content Operations and Production.

| # | Milestone | Owner | Notes |
|---|---|---|---|
| 1 | Project Started | **Brian** | Requires Content Manager assigned. fill.py triggers this. |
| 2 | Submitted to Content and Production Approval | **Brian** | Requires instructor assigned, tags, course + project metadata filled. fill.py triggers this. |
| 3 | Content and Production Approved | Content Operations | Brian clicks "Complete" after CP approval, but approval itself is downstream. |
| 4 | Submit to Content Operations | Content Operations | Requires contracting metadata filled + milestone 3 done. |
| 5 | Content Operations Completed | Content Operations | Requires contract link for all instructors. |
| 6 | Hand-off to Producer | Production | Requires Producer role assigned. |
| 7 | Pre-Production | Production | Requires Production Complete Date filled out. |
| 8 | Production Completed | Production | |
| 9 | Video Editing Completed | Production | |
| 10 | Ready for Beta Testing | QA | Requires Beta PreFlight, beta compression, Software License tasks. |
| 11 | Beta Testing Complete | QA | |
| 12 | Post Production Completed | Production | Bug Fixing + Audio phases. |
| 13 | Assessments Published | Content | Assessment phase tasks. |
| 14 | Project Complete | Publication | Course must be active; due date in the past; publication tasks done. |

**Brian's gate:** Milestones 1–2 are the BD handoff. Once milestone 2 is complete and
contracting metadata is filled (HITL 2), the record moves to Content Operations and Brian
is no longer the blocking party.

**What `fill.py` does:** Populates the fields that satisfy milestones 1 and 2. After
fill.py + HITL 2 (instructor contract rows), milestone 2 becomes completable.

**`cosmo-cli milestones <id>`** — reads live milestone state from Cosmo via Playwright.
Read-only. Use to check progress without opening a browser.

---

## On "create Cosmo records" / "set up Cosmo for [courses]" / "build blobs"

This is the primary workflow trigger. Work through it sequentially — do not skip ahead.

---

### Step 1 — Establish scope (agent)

If not already clear from context, ask:
- Which partner?
- Which courses? (list of titles, or "all remaining [partner] courses")

Then read `partners/<slug>/notes.md` before doing anything else (standard on-partner-mention hook).

---

### Step 2 — Build blobs (agent, one per course)

For each course:

**2a. Fetch course structure**
Use WebFetch on the course URL to get chapter/video titles. For Anaconda (Thinkific):
```bash
uv run ~/vibe/licensing-project/cosmo/scripts/scrape_anaconda_toc.py <course-url>
```
If the page is gated, use Playwright (Chrome must be running with `--remote-debugging-port=9222`).

**2b. Generate TOC sheet**
Follow `generate-tocs.md` (same skill directory). Output: a PTOC Google Sheet URL.
This becomes `project.draft_toc_url`.

**2c. Find suggested courses**
Search the LiL library for 4–6 related courses:
```bash
uv run --project ~/Brian_Code/kramer-project linkedin-catalog search "<topic keywords>" --limit 10
```
Pick titles most relevant to the course topic. These go into `course.suggested_course_titles`.

**2d. Draft strategy fields**
Using the course description, chapter list, and partner context from `partners/<slug>/notes.md`:

| Field | What to write |
|---|---|
| `strategy_summary` | 1–2 sentences: what the course covers, how it's structured |
| `strategy_goals` | What learners will be able to do after completing the course |
| `strategy_fit` | Why this fits LiL's library (topic priority, partner credibility, gap it fills) |
| `strategy_target_audience` | Who the learner is (role, experience level, use case) |

**2e. Assemble and create the blob**
```bash
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli new \
  --partner <slug> --title "<course title>"
```
Then fill fields with `cosmo-cli edit <id> <field.path> "<value>"`. Key fields:
- `project.project_name` → `"Course Title [Licensed] [Text]"` (append `[Text]` when content_styles includes TEXT)
- `project.due_date` — from deal context or ask Brian
- `project.draft_toc_url` — from Step 2b
- `project.strategy_summary/goals/fit/target_audience` — from Step 2d
- `project.production_content_styles` → `'["LICENSED", "TEXT"]'`
- `project.instructor_recording_availability` — e.g. `"Est. files due 4/27/2026"`
- `project.instructor_contract` — use partner deal constants (see Active Work section)
- `project.notes_to_producer` — include TOC URL + QA level
- `course.title` — course title (no suffix)
- `course.suggested_course_titles` — from Step 2c

Verify completeness: `cosmo-cli show <id>` and confirm all required fields are populated.

---

### Step 3 — HITL 1 handoff (pause — wait for Brian)

When all blobs for this batch are ready, hand off:

> "Blobs are ready for [N] courses. For each one, go to
> `https://www.linkedin.com/cosmo/project/3830001/` → Actions → Duplicate Project.
> After the duplicate is created, grab the new project ID and course ID from the URL
> and give them to me. I'll need both for each course."

When Brian provides the IDs, run:
```bash
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli set-ids <id|slug> \
  --project-id X --course-id Y
```
If validation fails, the command lists exactly which fields are missing — fix them and retry.

---

### Step 4 — Run fill.py (agent)

Confirm Chrome is running (`open -na "Google Chrome" --args --remote-debugging-port=9222`)
and Brian is logged into Cosmo. Then for each course:

```bash
uv run --project ~/vibe/licensing-project/cosmo cosmo-cli show <id> \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
blob = d['blob']
if d['project_id']: blob['project_id'] = d['project_id']
if d['course_id']:  blob['course_id']  = d['course_id']
print(json.dumps(blob))
" > /tmp/blob.json

uv run --project ~/vibe/licensing-project/cosmo fill.py /tmp/blob.json --blob-id <id>
```

`--blob-id` logs the run to `cosmo_runs` and marks the blob `entered` on success automatically.

---

### Step 5 — HITL 2 handoff (pause — Brian finishes)

> "Fill complete for [course]. Two manual steps remain in Cosmo:
> 1. Contracting tab — add the instructor contract row (instructor ID: [X], royalty: [Y]%, delivery: [date])
> 2. Milestones — click through both gates to hand off to production
>
> URL: `https://www.linkedin.com/cosmo/project/<project_id>/`"

---

---

## Key Gotchas

- **Project name — CRITICAL** — must always be written; silent failure leaves record as "Clone of: ..." and blocks publication. fill.py uses `click_confirm()` (✓ button) with focusout fallback. Always prints WRITE or SKIP — if neither appears in output, the field failed silently and needs manual correction.
- **Description + Short Description — CRITICAL** — must contain "TK" so the content team sees them. fill.py intentionally writes "TK" to these fields — do NOT treat "TK" as a blank to skip. Both fields are required for the Content team handoff.
- **Phase IDs are project-specific** — discovered dynamically by clicking tabs; never hardcoded
- **Fresh clone course navigation** — call `nav.acquire_course_page()` before any `/course/{id}/*` URL. On already-visited courses direct nav works; on fresh clones it fails with "An error occur". `/content` may or may not open a new tab — `acquire_course_page()` handles both.
- **Project details tab** — direct nav to `/project/{id}/details` works reliably (live-confirmed). The fill.py/read.py tab-click approach (overview → click details) does NOT change the URL on entered projects and may not render the sentinel. Use `nav.navigate_to_project_details()`.
- **Phase ID discovery** — `nav.discover_phase_ids()` only extracts IDs on `ready` (pre-entry) projects. On entered projects, tab clicks load content inline without URL changes — no phase ID in URL. This is expected; IDs were captured at fill time.
- **Strategy tab** — label elements have no `for` attrs; filling is positional
- **Suggested courses typeahead** — only first 40 chars of the title are reliably matched
- **Note to Content Operations** — appears twice in Contracting tab DOM; fill.py targets the labelled instance
- **Course tabs** — no `data-name` attrs; use `browser_navigate` (not click JS) to switch tabs

---

## Partner Deal Constants

Reference constants needed when building blobs. Add a section per partner as deals close.

### Anaconda

Source project for cloning: `3830001` (course `8155000`)
Partner Drive folder: `1k6gZTxKToyhZmereGv70wj-MeFRYncTW`
All 8 initial courses entered 2026-04-16. Query DB for current state: `cosmo-cli list --partner anaconda`

**Deal constants:**
```json
"instructor_contract": {
  "instructor_id": 22059000,
  "contract_type": "LICENSED",
  "subscription_royalty_rate": 15,
  "content_delivery_due_date": "2026-04-27",
  "exclusive_license": false
}
```

---

## Pre-Close Blobs — Expected Draft State

For partners where the deal has not yet closed, blobs will legitimately sit in `draft`
status because certain fields cannot be populated until post-close actions complete.

**`instructor_id` is always TK for new partners.** Content Ops must create the
LinkedIn Learning author record for the licensor org before this ID is available.
This happens post-deal-close. Do not block blob creation on it — leave
`instructor_contract.instructor_id` as a placeholder and proceed.

**`source_project_id` requires a Cosmo source record.** The first time a partner
appears in Cosmo, there is no source project to clone from. Brian must manually create
the first Cosmo project record for that partner before `set-ids` can succeed.

**`cosmo-cli validate` is the canonical readiness check.** Run it to see exactly which
fields are blocking `set-ids`. Errors are grouped by field path:

```
FAIL — 2 validation error(s):
  source_project_id: Field required
  project → instructor_contract → instructor_id: Field required
```

This is the expected output for a new-partner pre-close blob. When the deal closes and
the instructor ID is created, run `cosmo-cli edit <id> project.instructor_contract.instructor_id <id>`,
get the source project ID, set it, then retry `set-ids`.

**Skilljar LMS — TOC default structure:** Skilljar courses are organized as modules with
one video per unit. Default TOC layout: one chapter per logical course part, one video per
chapter. Do not assume multi-video chapters unless the course structure explicitly shows it.

---

## Future / TBD

- **Full record creation from scratch** — not yet scoped
- **API-based automation** — design spec at `docs/superpowers/specs/`; requires CPS service account. Not blocking.
