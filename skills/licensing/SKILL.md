---
name: licensing
description: >
  Persistent assistant for LinkedIn Learning content licensing BD work. Maintains pipeline,
  partner context, and cross-session continuity. Also handles TLM workflows — provider
  discovery, catalog scraping, and DB-backed reports. Use when working in ~/licensing/,
  managing partner relationships, evaluating content opportunities, drafting partner comms,
  running TLMs, or doing any licensing BD task. Triggers on "load licensing", "open licensing",
  "catalog [topic]", "map the [topic] market", "generate a TLM", or any licensing pipeline work.
---

# Licensing

Persistent coordination layer for LinkedIn Learning content licensing BD work. Domain
knowledge lives in `~/licensing/context/licensing_context.md` — read it when you need
heuristics, commercial models, partner taxonomy, or sourcing methodology. This skill is
the state layer.

## Working Directory

```
~/licensing/
  pipeline.md          # Primary artifact — active partner pipeline
  manifest.md          # Append-only action log
  scratchpad.md        # Strategy context, content rubric state, open questions
  notes.md             # Backlog, parked thoughts, future tooling work
  catalog_registry.json  # Registry of all scraped partner catalogs
  training_urls.json   # Output of find-catalogues; training portal URLs per company
  partners/            # One directory per active/prospective partner (notes.md + catalog files)
  skills/              # One directory per skill TLM (roadmap.md + catalog XLSX + report)
  context/             # Read-only reference docs (licensing_context.md, google_docs.json, bd-process.md, funnel-framework.md, library-composition-analysis.md)
  projects/            # Parallel workstreams (each has its own subdir + notes.md); also loose docs licensable-definition.md, licensing-classifier.md
  gate_log.json        # Course-level gate decision log — SOT for funnel metrics and CYA (see projects/pipeline-ops/notes.md)
  scripts/             # Python utilities: lil_stats.py, lil_semantic.py, lil_overlap.py; log_gate.py, funnel_report.py
  database/            # ChromaDB instance used by scripts/lil_semantic.py for vector search over LiL course catalog — do not delete
  boilerplate/         # Reusable templates (outreach.md: Template A InMail, Template B cold email)
  business_context/                    # Business intelligence — hierarchical, domain-organized
    summary.md                         # Omnibus: one paragraph per domain, overall strategic read
    financial_health/
      summary.md                       # Domain synthesis (auto-generated from docs below)
      [dated docs]                     # LinkedIn financials, LLS health, Microsoft earnings
    flagship_feed/
      summary.md
      [dated docs]                     # Feed roadmap, DAU strategy, Knowledge Marketplace
    premium/
      summary.md
      [dated docs]                     # Premium business, consumer thesis, subscriber trends
    talent_solutions/
      summary.md
      [dated docs]                     # Talent Solutions, enterprise L&D, Recruiter/Jobs
    ai_strategy/
      summary.md
      [dated docs]                     # AI features, Copilot intersection, LinkedIn AI Coach
    org_context/
      summary.md
      [dated docs]                     # Leadership, restructures, internal champions/friction
    competitive_landscape/
      summary.md
      [dated docs]                     # Coursera, Udemy, Pluralsight, Indeed/Glassdoor
    member_metrics/
      summary.md
      [dated docs]                     # DAU/MAU, engagement, feed-to-learning conversion
```

Ensure this structure exists on first run:

```bash
mkdir -p ~/licensing/partners ~/licensing/context \
  ~/licensing/business_context/{financial_health,flagship_feed,premium,talent_solutions,ai_strategy,org_context,competitive_landscape,member_metrics}
```

---

## Session Start Protocol

Run this every session, in order:

1. `mkdir -p ~/licensing/partners ~/licensing/context ~/licensing/business_context/{financial_health,flagship_feed,premium,talent_solutions,ai_strategy,org_context,competitive_landscape,member_metrics}` — ensure structure exists
2. Read `~/licensing/pipeline.md` — primary orientation; surface what's active, stale, or needs action
3. Read `~/licensing/scratchpad.md` — strategy context and rubric state
4. If `~/licensing/business_context/summary.md` exists: read it — strategic environment context
5. If this is a partner-focused session: read `~/licensing/partners/<name>/notes.md`
6. If a project workstream is the focus: check `~/licensing/projects/` for a relevant subdir and read its `notes.md`

Note: `manifest.md` is an append-only audit trail — consult it on demand (e.g., "when did we last contact X?" or "what changed with Y?"), not at session start.

Then open with a grounded brief — not "what do you want to do?" but a synthesis:

> "[N] active partners. [Partner X] has been idle for [N] days — next action is [Y].
> [Partner Z] needs [specific thing]. What's your focus today?"

If no files exist yet (first run), initialize them (see Bootstrap below) then do goal intake.

---

## Session Types

There is no formal Manager/Worker role distinction. Two natural session types emerge:

**Pipeline session** — overview mode. Manages the full pipeline, updates `pipeline.md`,
coordinates across partners, handles strategy questions.

**Partner branch session** — focused on one partner. Same full context as a pipeline
session. Reads the partner's file. Can draft comms, update status, reason about deal
strategy, chase tangents without polluting the pipeline context. Updates `partners/<name>/notes.md`
and `manifest.md` freely.

Both session types read the same files. Both update shared state.

**When to suggest a branch session:** If a single partner has dominated 20+ turns, or
you've drafted/iterated on comms, flag it: "This is getting deep on [Partner] — worth
spinning a branch session to keep the pipeline context clean."

---

## Shared State: What Gets Updated and When

**`pipeline.md`** — update whenever a partner's stage, last action, or next action changes.

**`partners/<name>/notes.md`** — freeform. Add notes, email drafts, deal context, contact log,
whatever is useful. No required structure — let it evolve from real use.

**`manifest.md`** — append one line per meaningful action (file created/updated, comms
drafted/sent, partner status changed). Format:

```
- YYYY-MM-DD | created|updated|sent | <path or description> | <what changed>
```

**`scratchpad.md`** — update when: content strategy rubric changes, sourcing priorities
shift, open questions resolve, or strategic context needs capturing.

---

## Pipeline.md Format

Keep it scannable. Suggested columns — adapt as the workflow evolves:

```markdown
# Pipeline
Last updated: YYYY-MM-DD

| Partner | Tier | Stage | Last Action | Next Action |
|---|---|---|---|---|
| Anthropic | Tier 1 | Contract | 2026-02-20 sign expected | Track — no action needed |
| Google | Tier 1 | Outreach | 2026-02-10 intro sent | Follow up if no response by Mar 1 |
```

**Stages** (lightweight, not prescriptive): Prospect → Outreach → Evaluation → Negotiation → Contract → Active → Paused → Dead

Add/remove columns as real usage reveals what's actually needed.

---

## Bootstrap (First Run)

If no files exist, create seeds:

**`pipeline.md`**:
```markdown
# Pipeline
Last updated: YYYY-MM-DD

| Partner | Tier | Stage | Last Action | Next Action |
|---|---|---|---|---|
```

**`manifest.md`**:
```markdown
# Manifest
Format: YYYY-MM-DD | created|updated|sent | <path or description> | <what changed>

---
```

**`scratchpad.md`**:
```markdown
# Scratchpad

## Content Strategy Rubric
[Populate from bi-weekly BD/Content Strategy alignment — which segments are green/red for licensing]

## Sourcing Priority
[Current focus: analog-based | gap-based | signal-based | inbound]

## Open Questions
[Things to resolve, track, or raise at next alignment meeting]

## Notes
```

**`partners/{name}/notes.md`** (template for new partners):
```markdown
# {Partner Name}

**Website:** {official site}
**Training Portal:** {catalog/learning URL}
**BD POC:** {Brian|Manish}
**Priority:** {P0|P1|P2|TBD} / {Tier 1|Tier 2|Tier 3|TBD}
**Stage:** {Prospect|Outreach|Evaluation|Negotiation|Contract|Active|Paused|Dead}
**New/Existing:** {New|Existing}
**MOC:** {name or —}
**Library:** {Tech|Biz|Creative|—}
**Subject:** {subject area}
**Content Focus:** {specific topic or tool}

## Status
[Current state — what's happened, where things stand]

## Contact Log
```

Then ask: what partners are currently active, and what stage is each one?

---

## Hooks

Conditional rules that fire automatically when specific events occur. These are not
optional — treat them as invariants of the workflow.

**On partner mention**
When a partner name appears that you haven't already read a file for this session:
check if `partners/<name>/notes.md` exists and read it before responding. Never advise on
a partner without first loading their file.

**On status change**
When a deal stage, last action, or next action changes: update `pipeline.md` immediately —
not at session end. Status is the highest-decay artifact.

**On comms drafted or sent**
When an email or message is drafted or marked as sent: write it to `partners/<name>/notes.md`
AND append to `manifest.md`. Do both, always.

**On new partner introduced**
When a partner is mentioned with no existing file and no pipeline entry: create
`partners/<name>/notes.md` using the Bootstrap template (including Training Portal field)
and add a row to `pipeline.md` in the same action. Never leave a partner floating in
conversation without landing in both places.

**On Google Doc accessed**
Whenever a Google Doc, Sheet, or Drive file is read or accessed in a session:
1. Check if it is already listed in `context/google_docs.json`
2. If not, add it immediately under `"read_only_docs"` with `"permissions": "read-only"` — this is the default for all docs
3. Include: name, id, url, brief description, and owner if known
4. Append to `manifest.md`
Never skip this step. The docs manifest must stay current.

**On Google Doc write attempt**
Before writing to any Google Doc: read `context/google_docs.json` and confirm the doc
is listed as `"permissions": "read-write"`. Do not write to docs listed as `"read-only"`
or absent from the manifest.

**On branch session open**
In a partner-focused session: read `partners/<name>/notes.md` fully before saying anything.
No brief, no analysis, no advice until that read is complete.

**On strategic context shift**
When the content strategy rubric changes, sourcing priority shifts, or a key open
question resolves: update `scratchpad.md` immediately.

**On Team Tracker snapshot request**
Brian may occasionally ask to refresh the Team Tracker snapshot. When he does:
1. Read `context/google_docs.json` to confirm the Team Tracker URL and that it is `"permissions": "read-only"`
2. Pull the sheet using `read_google_sheets_by_id` — never write to it
3. Overwrite `context/team_tracker_snapshot.md` with the pulled data and a timestamp header
4. Append to `manifest.md`
Never pull or refresh the snapshot proactively — only on explicit request.
The snapshot is a local reference artifact; the source Google Sheet is always read-only.

**On "summarize [domain]"**
When the user says "summarize [domain]" or "refresh [domain] summary" (where domain is
one of: financial_health, flagship_feed, premium, talent_solutions, ai_strategy,
org_context, competitive_landscape, member_metrics):
1. List all files in `business_context/[domain]/` excluding `summary.md`
2. Read each one
3. Write a synthesis to `business_context/[domain]/summary.md` — key facts, trends,
   strategic reads, sources with dates, and a staleness note (oldest source date)
4. Append to `manifest.md`
Do not summarize if the domain directory has no docs yet — flag it as unpopulated instead.

IMPORTANT: Execute this in the MAIN session, not as a subagent. Summarization is
read-then-write on local files — subagents cannot write files without explicit Write
permission grants, which defeats the purpose of delegation. Subagents are for research
(external I/O); summarization is for the main thread.

**On "summarize business"** (also: "refresh business summary", "update business context")
When the user triggers a full business summary refresh:
1. Read every `business_context/[domain]/summary.md` that exists
2. Write `business_context/summary.md` using this schema:
   - Header with last-updated date and staleness table (one row per domain)
   - One 2-3 sentence paragraph per domain
   - "Overall Strategic Read" section: 4-6 sentences on what this means for LinkedIn's
     actual situation right now — opinionated, not corporate
   - "Implications for Licensing BD" section: 4-6 bullets of cross-domain insights that
     only emerge from reading all domains together
3. Append to `manifest.md`
Only summarize domains that have a populated summary.md — skip and note empty ones.
This is the top-level orientation artifact read during every session start.

IMPORTANT: Execute in the MAIN session (same reason as above).

**On new business context doc added**
When any file is written to a `business_context/[domain]/` directory (excluding summary.md):
- Append to `manifest.md` as usual
- Add a note: "[domain]/summary.md is now stale — run 'summarize [domain]' to refresh"
Do NOT auto-summarize. Summarization is always explicit.

**On "save context"**
Canonical invocation phrase: Brian says **"save context"**. Also fires when Claude is
about to make any substantive write to `scratchpad.md`, `context/` files, or `SKILL.md`
on its own initiative — defined as more than a single factual correction or pointer update.

Scope:
- FIRES: scratchpad.md, context/[any].md, SKILL.md
- DOES NOT FIRE: manifest.md (append-only, no review needed), partners/[any]/notes.md
  (operational notes, not shared context artifacts)

Process:
1. Draft all proposed updates as text — do NOT write files yet.
2. Read `context-review-prompt.md` from this skill's directory.
3. Substitute into the template:
   - `{{ target_files }}`: files being updated (one path per line)
   - `{{ proposed_updates }}`: full draft content, labeled by target file
4. Spawn a review subagent via the Agent tool with the substituted prompt.
   `run_in_background=False` — review must complete before any writes.
5. Present the verdict to Brian:
   - APPROVE → apply directly
   - MODIFY → show the suggested change, apply unless Brian objects
   - REJECT → surface the reason, ask how to proceed
6. Write files only after review is complete.
7. Append to `manifest.md`.

**On gate decision**
When a course passing or failing a gate is mentioned in conversation — e.g., "CS rejected the
Fortinet FortiGate course, SCORM format" or "Anaconda Docker Engineering passed topic review":

1. Extract all available fields: partner_slug, course_title, gate number, decision, reason_code,
   reason_detail, decided_by, submitted_date, decided_date. Ask for any missing required fields
   (partner, course, gate, decision) before writing. Infer reason_code from the taxonomy in
   `projects/pipeline-ops/notes.md` if not explicitly stated — confirm with Brian if ambiguous.
2. Read `gate_log.json`. Compute next sequential ID (gl-NNN). Compute velocity_days if both
   dates are available. Append the new entry. Write `gate_log.json`.
3. Append a one-line note to `partners/<slug>/notes.md` under a "## Gate Log" section
   (create the section if absent): `- YYYY-MM-DD | Gate N | decision | reason_code | course_title`
4. Append to `manifest.md`:
   `- YYYY-MM-DD | gate-decision | gate_log.json | <id>: <partner> / "<course>" / Gate N / <decision>`

Use `log_gate.py` only for programmatic/batch logging. In-session logging always goes through
this hook directly (read → mutate → write gate_log.json).

**On "gate report" / "funnel summary"**
When asked for a gate report, funnel summary, conversion rates, or rejection breakdown:

1. Read `gate_log.json`.
2. Compute and display inline — no script needed:
   - Per gate: total decisions, pass/reject/pending/withdrawn counts and rates, avg velocity,
     rejection reason breakdown (count + %)
   - Partner summary table: submitted, pass, reject, pending, pass rate
3. Apply any filters mentioned (--partner, --gate, --since).

If the log is empty, say so and remind Brian the hook fires automatically when gate decisions
are mentioned in session.

**On "sync gate log"**
When Brian says "sync gate log" (or "sync gate log to sheet"):

1. Read `gate_log.json`.
2. Read `context/google_docs.json` to find the gate log sheet ID under `"gate_log_sheet"`.
   - If the sheet is not yet registered: create a new Google Sheet named
     "Licensing — Gate Log" via `create_google_sheets_spreadsheet`, register it in
     `context/google_docs.json` under `"gate_log_sheet"` with `"permissions": "read-write"`,
     and append to `manifest.md`.
3. Build the sheet payload: header row + one data row per entry, columns matching the
   gate_log.json schema (id, partner_slug, partner_display, course_title, course_url,
   gate, gate_name, submitted_date, decided_date, velocity_days, decision, reason_code,
   reason_detail, decided_by, logged_date, notes).
4. Write to the sheet via `write_google_sheets_by_id` — full overwrite of tab "Gate Log"
   (create tab if absent). gate_log.json remains the SOT; the sheet is always derived.
5. Append to `manifest.md`:
   `- YYYY-MM-DD | synced | gate_log.json → Google Sheet | <N> entries`

**On "resolve"**
When the user says "resolve": review the current conversation for meaningful improvements
to this skill. Update only if there are substantive changes to workflow, conventions,
hooks, or tooling. Do NOT update for minor, session-specific, or speculative details.
A "resolve" that produces no changes is fine — use judgment. Scope is limited to this
skill only; do not update other skills.

**On contact research request**
When asked to find outreach contacts for one or more partners: read
`find-partner-contacts.md` (in this skill's directory) before starting. Follow its
role hierarchy and source hierarchy exactly. Record confirmed leads in
`partners/<slug>/notes.md` under an "Outreach Targets" section. Append to `manifest.md`.

**On internal Confluence research**
When researching an internal LinkedIn topic without a known page ID (e.g., a BD process,
team wiki, product area, or policy): run `mcp__glean_default__search` with `app="confluence"`
before reaching for Captain MCP. Glean is the discovery layer; Captain is for fetching known
pages. If Glean returns relevant results, use the URL with `mcp__glean_default__read_document`
for full content, or extract the page ID from the URL and use Captain `get_confluence_page`.

**On scrape script cleanup**
After any catalog scrape completes, check for `scrape_*.py` files at `~/licensing/` root.
These are one-time artifacts generated by catalog-scraper subagents and should be deleted
once the catalog files are confirmed in `partners/<slug>/`. Delete them immediately —
do not leave them to accumulate at root.

**On context depth warning**
If a single partner has dominated 20+ turns or comms have been iterated multiple times:
flag it proactively — "This is getting deep on [Partner] — worth spinning a branch
session to keep the pipeline context clean." Do this before the context becomes too
loaded to summarize.

---

## Tooling

### Glean MCP — Internal Knowledge Discovery

Glean indexes LinkedIn's internal Confluence, Google Docs, Slack, and code repositories.
Use it when researching an internal topic where you don't already have a Confluence page ID.

**Tool routing:**

| Need | Tool |
|---|---|
| Find Confluence pages by keyword | `mcp__glean_default__search` with `app="confluence"` |
| Fetch a known page (have the ID) | Captain `get_confluence_page` |
| Fetch full page content by URL | `mcp__glean_default__read_document` |
| Synthesize across multiple sources | `mcp__glean_default__chat` (use sparingly — see below) |
| People / org lookups | Do not use Glean (`employee_search` unreliable) |

**Behavioral rules:**
- Always set `app="confluence"` for licensing BD research unless cross-source synthesis is needed.
- `chat` output can exceed 100K chars — invoke only for specific, targeted questions. Not for broad exploratory queries.
- `read_document` is a reliable fallback when Captain's `get_confluence_page` fails or you have a URL but no page ID.
- `code_search` is irrelevant to licensing BD — do not use.

**High-value Confluence areas confirmed accessible via Glean:**
- BD Legal Resources (go/ltsbd-legal): NDA process, Conga deal-tracking, purchase request flow
- Content Partner Integration docs (GSO space): pre-call checklist, cert call process, SFTP setup
- Royalties infohub (go/royalty): royalties calculation mechanics, Content Ops contacts
- go/lls team wiki: LLS product areas, team structure, focus areas

---

### Skills available for licensing research and catalog collection:

**`find-partner-contacts`** — technique for finding cold outreach targets at external
partner companies. Role hierarchy, source hierarchy (ZoomInfo/RocketReach snippet searches),
query patterns, and what to discard. Reference: `find-partner-contacts.md` in this skill dir.

**`find-catalogues`** — discovers training portal URLs for a given company. Use before
scraping to locate the right catalog URL. Output: `training_urls.json` with
`results.{CompanyName}.primary_url` and `confidence` per company.

**`licensing:catalog-scraper`** — scrapes a single training provider's course catalog and
produces structured JSON, XLSX, and markdown reports. Use for evaluating a partner's content
depth and quality. Output goes to `~/licensing/partners/{slug}/` when the licensing dir exists.

Spawn one `licensing:catalog-scraper-worker` subagent per URL. Never process multiple
providers sequentially in the main thread.

Only invoke on explicit request. Do not proactively trigger scraping.

For TLM workflows (topic market maps), see the **TLM Workflow** section below.

### Catalog DB

The postgres `catalog` database on Caruana holds all sourcing data across three lakes:

- **Lake 1** — direct catalog scrapes (`providers`, `courses` tables)
- **Lake 2** — Udemy instructor / Coursera institutional partner data (`platform_courses`, `platform_creators`)
- **Lake 3** — Professional Certificate interest form submissions (`interest_form_submissions`) — inbound BD signal

Project: `~/vibe/licensing-project/catalog/`
CLI: `uv run --project ~/vibe/licensing-project/catalog catalog <command>`

Key commands for licensing sessions (without running a full TLM):
```bash
catalog interest-form-search --partnership-only   # 33 inbound partnership leads
catalog interest-form-search --topic "AI"         # demand signal by topic
catalog platform-search "kubernetes"              # top Udemy instructors by topic
catalog search "topic"                            # Lake 1 course search
catalog stats                                     # DB overview
```

Refresh Lake 3 (interest form) monthly: run the Trino query at
`~/.claude/skills/licensing/queries/interest_form.sql` via `execute_trino_query` MCP,
write result to `~/licensing/interest_form_YYYY-MM-DD.json`, then run
`uv run --project ~/vibe/licensing-project/catalog python /Users/bianders/vibe/licensing-project/catalog/scripts/load_interest_form.py ~/licensing/interest_form_YYYY-MM-DD.json`.

### Checking which partners lack catalogs

To identify partners without catalog data:
```bash
for d in ~/licensing/partners/*/; do
  [[ -f "$d/catalog.json" ]] || echo "$(basename $d)"
done
```

Partners with a `notes.md` but no `catalog.json` are candidates for scraping.

### Full batch catalog workflow

When asked to scrape multiple partners:

**Step 1 — Find URLs** (find-catalogues):
Run find-catalogues on the list of partner names. It produces `training_urls.json`.
Only pass partners where `confidence` is `high` or `medium` to the next step.
Skip partners where confidence is `low` or `none` — flag those for manual review.

**Step 2 — Build dispatch list**:
Filter find-catalogues output to high/medium confidence partners:
```python
inputs = [
    {"provider": company, "url": data["primary_url"]}
    for company, data in results.items()
    if data["confidence"] in ("high", "medium")
]
```

**Step 3 — Spawn one licensing:catalog-scraper-worker subagent per URL**:
Spawn a separate `licensing:catalog-scraper-worker` subagent for each URL.
Never run multiple scrapes sequentially in the main thread. Run all workers with
`run_in_background=true`. Each worker writes its output (catalog.json, catalog.xlsx,
report.md) directly to `~/licensing/partners/{slug}/` and updates `catalog_registry.json`.
No consolidation step needed — workers have direct filesystem access.

### TLM Workflow

Builds a market map of training content for a topic across all known and discovered providers.
Distinct from the batch partner catalog workflow above — that starts with a known partner list;
this starts with a topic and discovers who the providers are.

Invoke when asked to "catalog [topic]", "map the [topic] market", or "run a TLM on [topic]".

#### Phase 1: Classify SKILL or TOOL

**TOOL** — specific technology, framework, or product (Kubernetes, Terraform, Salesforce).
Course titles typically include the name verbatim. Use a single search term.

**SKILL** — professional domain or competency (DevOps, Data Science, Cybersecurity).
Broad scope; requires sub-topic breakdown before searching. Propose sub-topics and confirm:

```
Topic: DevOps  |  Type: SKILL

Proposed sub-topics:
  - Docker / containers
  - Kubernetes / container orchestration
  - CI/CD (Jenkins, GitHub Actions, GitLab CI)
  - Infrastructure as Code (Terraform, Ansible)
  - Monitoring / observability (Prometheus, Grafana)

Confirm, edit, or add sub-topics?
```

Wait for confirmation. Skip this step for TOOLs — proceed directly to Phase 2.

#### Phase 2: Provider Discovery

**Step 1 — Check what's already in the DB:**
```bash
uv run --directory ~/vibe/licensing-project/catalog python -m catalog providers
```
Note existing providers plausibly relevant to the topic.

**Step 2 — Search for new providers** (use brave-web-search skill):
```bash
uv run --directory ~/.claude/skills/brave-web-search python conduit.py search "QUERY"
```
Queries to run:
- `"[topic]" training courses certification provider`
- `"[topic]" online training platform NOT coursera NOT udemy NOT pluralsight`
- `best "[topic]" training vendors enterprise`

For SKILLs, also run 2-3 queries on the most distinctive sub-topics.

Look for: direct content producers (the company whose name is on the courses).
Discard: learning platforms (Coursera, Udemy, Pluralsight, LinkedIn Learning — distribution, not producers).

**Step 3 — Present the candidate list and wait for confirmation:**
```
PROVIDERS ALREADY IN DB:
  - CloudThat (402 courses)
  - Cisco (154 courses)

NEW CANDIDATES — confirm to scrape:
  [ ] Linux Foundation — training.linuxfoundation.org
  [ ] HashiCorp — developer.hashicorp.com/tutorials

Skip any? Add any?
```

Do NOT begin scraping until approved.

#### Phase 3: Scrape New Providers

For each confirmed new provider, dispatch one `licensing:catalog-scraper-worker` subagent
per URL. All run with `run_in_background=true`. Never process multiple providers sequentially.

While scraping runs, proceed to Phase 4 using the DB as it stands. Re-run the export
step after all subagents finish.

#### Phase 4: DB Query

**TOOL** (single term):
```bash
uv run --directory ~/vibe/licensing-project/catalog python -m catalog search "kubernetes" --limit 10000
```

**SKILL** (one query per sub-topic, deduplicate on `(provider_slug, title)`):
```bash
uv run --directory ~/vibe/licensing-project/catalog python -m catalog search "docker" --limit 10000
uv run --directory ~/vibe/licensing-project/catalog python -m catalog search "kubernetes" --limit 10000
```

Export to XLSX:
```bash
uv run --directory ~/vibe/licensing-project/catalog python -m catalog export "[topic]" \
  --output ~/licensing/catalogs/[topic-slug]_catalog_[YYYY-MM-DD].xlsx
```

For SKILLs with multiple terms, merge results from each sub-topic search and deduplicate
with pandas before writing the combined XLSX.

#### Phase 5: Output

**XLSX**: `~/licensing/catalogs/[topic-slug]_catalog_[YYYY-MM-DD].xlsx`
Columns: provider, title, url, description, duration, level, format, price, category,
instructor, date_scraped. For SKILLs, add a `matched_subtopic` column.

**Markdown report**: `~/licensing/catalogs/[topic-slug]_report_[YYYY-MM-DD].md`
Sections: Coverage Summary table, Sub-topic Coverage (SKILL only), Methodology,
Dark Matter (auth-walled providers with estimated catalog size), Excluded Providers,
Self-Optimization Notes.

**Manifest entry**:
```
- YYYY-MM-DD | created | ~/licensing/catalogs/[slug]_catalog_YYYY-MM-DD.xlsx | [N] courses, [M] providers, SKILL|TOOL
```

**Conventions**: topic slug = lowercase hyphenated (`Site Reliability Engineering` →
`site-reliability-engineering`). Output directory: `~/licensing/catalogs/` (create if needed).

---

## Domain Knowledge

**`~/licensing/context/licensing_context.md`** — primary reference for heuristics,
commercial models, partner taxonomy, sourcing methodology, and the tangibility gates
(Addressable / Aligned / Acceptable). Read this file when reasoning about partner
fit, deal structure, or content evaluation.

**`~/licensing/context/`** — read-only reference docs specific to this role. Check this
directory for any relevant docs before doing research Claude can't do alone (e.g., internal
rubric docs, partner-specific notes from colleagues, role context).

**`~/licensing/context/funnel-framework.md`** — the 10-gate licensing funnel: gate definitions,
classifier signals, pass rate estimates, bottlenecks, and market expansion levers. Also contains
funnel math (TLM → BHAG), deal archetype model (boutique vs. anchor), format tractability tiers
(A/B/C), portfolio tier model (Tier 1/2/3), and World Catalog concept. Read for sourcing strategy,
BD process design, or BHAG planning sessions.

**`~/licensing/context/library-composition-analysis.md`** — empirical analysis of the existing
licensed library (data as of 2026-02-01). Key findings: engagement concentration (top 1% of courses
= 98.9% of all engagement; 19.7% of courses = zero engagement), partner roster profile (116 licensors,
historically small studios not institutional vendors), Madecraft structural outlier (424 courses/deal),
ratings uniformity (no discriminating power). Read when evaluating existing library, benchmarking
new partner content, or making the internal case for licensing investments.

**`~/licensing/context/bd-process.md`** — operational and political model for how licensing BD
works day-to-day. Covers: two BD motions (CM-initiated Motion A vs BD-initiated Motion B), pipeline
stage taxonomy (Sourcing → Gate A → Outreach → In Conversation → Gate B → Contracting → Onboarding →
Production → Partnership Management), Gate A as the binding throughput constraint, and the political
layer (Brian/Mary peer relationship, dogsbody risk, how to manage Gate A submissions). Read when
reasoning about deal stage, BD motion strategy, or internal process questions.

---

## Aquifer

See `~/.claude/skills/licensing/aquifer.md` for details on the long-term token optimization
layer — when and how to operationalize validated research workflows into scheduled scripts.
