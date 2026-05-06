---
name: licensing
description: >
  Persistent assistant for LinkedIn Learning content licensing BD work. Maintains pipeline,
  partner context, and cross-session continuity. Also handles TLM workflows — provider
  discovery, catalog scraping, and DB-backed reports. Also handles Gartner Peer Insights
  lookups via the gartner-pi subskill — vendor ratings, market segment rankings, competitive
  research. Use when working in ~/licensing/, managing partner relationships, evaluating content
  opportunities, drafting partner comms, running TLMs, or doing any licensing BD task. Triggers
  on "load licensing", "open licensing", "catalog [topic]", "map the [topic] market",
  "generate a TLM", "Gartner rating", "top products in [segment]", "[vendor]'s Gartner profile",
  or any licensing pipeline work.
---

# Licensing

Persistent coordination layer for LinkedIn Learning content licensing BD work. This skill is
the state layer. Full context: `~/licensing/context/licensing_context.md` (partner taxonomy,
sourcing methodology, complete tangibility gates). Key heuristics are inlined below.

## Three Parts of Licensing

| Part | Location | Purpose |
|---|---|---|
| **Skill** | `~/.claude/skills/licensing/` | This file — workflow, hooks, heuristics, session protocol |
| **Knowledge base** | `~/licensing/` (CWD) | Pipeline, partner files, context docs, manifests — the working data |
| **Code project** | `~/vibe/licensing-project/` | Python tooling: catalog DB, classifier, Cosmo, profile generator |

## Data Privacy — Non-Negotiable

When the user requests **local model inference** (`gpt-oss`, `llama`, `qwen`, etc.), it is because the content is **proprietary or confidential**. This applies to all meeting recordings, partner materials, pipeline data, and internal documents.

- NEVER substitute a cloud model (haiku, gpt-mini, claude, gpt-5, gemini, etc.) as a fallback
- NEVER send proprietary content to any external API, even "just this once"
- If Headwater (AlphaBlue) is unreachable: stop, report the outage, and wait for the user to resolve it
- `conduit query --model gpt-oss:latest` and `conduit batch --model gpt-oss:latest` now route automatically through Headwater — no `--local` flag needed

---

## Quick Reference

### Format Gate (Addressable — Gate 1)

A course passes if ALL of these are true:

| Criterion | Pass | Fail |
|---|---|---|
| Format | Standalone video; OR structured text (Word/Google Docs / LiL-FM Markdown); OR mixed video + text | SCORM, interactive labs, platform-dependent, unstructured HTML/PDF |
| Length | 30min–2hr, chunkable to 5–15min segments | Outside range or monolithic |
| Volume | 5+ courses | < 5 (unless exceptional) |
| Availability | Not freely on YouTube; email-gate OK | Freely on YouTube (unless exceptional) |
| Tone | Learner-focused, objective | Sales-y, steers to partner tool without candor |
| Production | Comparable to LiL organic | Webinar recording, AI voice/avatar |

### Alignment Levers (why a partner says yes)

| Lever | Typical Partner | Terms |
|---|---|---|
| Exposure | Tier 1 brands (Google, Adobe, SAP) | 0% royalty — distribution/brand reach is the pitch |
| Revenue | Publishers, niche orgs, influencers | 15% non-exclusive / 20% exclusive |
| Awareness / Sales Enablement | Platforms with their own subscription business | LiL as top-of-funnel for partner's platform |
| Commitment Fulfillment | Brands with public upskilling pledges | Adobe 30M/2030, SAP 12M/2030, Cisco 1M |

### Content Strategy Rubric

**STATUS: UNPOPULATED.** Mary's segment-level go/no-go has not been received. Gate 2 (Topic Relevance) cannot be applied
consistently until this is filled in. Populate `context/topic-priority.yaml` from the next bi-weekly BD/Content Strategy alignment.

Provisional signals (from `funnel-framework.md`):
- Green: AI/ML, cybersecurity, cloud, software development, leadership with cert association
- Red: generic soft skills, long-tail creative, commoditized topics with free alternatives

---

## Working Directory

```
~/licensing/
  pipeline.md          # Primary artifact — active partner pipeline
  manifest.md          # Append-only action log
  partners/            # One directory per active/prospective partner (notes.md, pitch.md, catalog files)
  topics/              # One directory per topic; may contain research artifacts (brief, scope, tmz),
                       # TLM outputs (catalog XLSX, report), roadmap, or any combination depending on lifecycle stage
  context/             # Reference docs — see context/README.md for file-to-trigger map
  projects/            # Parallel workstreams (each has its own subdir + notes.md)
  daily/               # Day specs — one YYYY-MM-DD.md file per working day. Each spec defines
                       # the day's tasks, inputs, constraints, and Claude Code instance assignments.
                       # Checked at session start — read during Session Start Protocol if today's file exists.
  gate_log.json        # Course-level gate decision log — SOT for funnel metrics and CYA (see projects/pipeline-ops/notes.md)
  scripts/             # Python utilities; Classifier: classify.py, classifier_models.py, classifier_prompt.j2
  boilerplate/         # Reusable templates (outreach.md: Template A–E outreach + Elevator Pitch Framework)
  partner-assets/      # PDF assets for partner outreach: Content License Agreement, Instructor Analytics Dashboard,
                       # LinkedIn Learning Content Licensing one-pager, Content Delivery Video Format Guidelines
  meta/                # Architecture session artifacts only — SDD docs, hook audits, roadmaps. Read-only in operational sessions.
  USAGE.md             # Human-readable onboarding doc for new collaborators — keep at root, do not move
```

Ensure this structure exists on first run:

```bash
mkdir -p ~/licensing/partners ~/licensing/context \
  ~/licensing/context/business/{financial_health,flagship_feed,premium,talent_solutions,ai_strategy,org_context,competitive_landscape,member_metrics}
```

---

## Session Start Protocol

Run this every session, in order:

1. `mkdir -p ~/licensing/partners ~/licensing/context ~/licensing/context/business/{financial_health,flagship_feed,premium,talent_solutions,ai_strategy,org_context,competitive_landscape,member_metrics}` — ensure structure exists
2. Read `~/licensing/state.md` — synthesized dashboard; produces the opening brief directly
3. Check for a day spec: `~/licensing/daily/YYYY-MM-DD.md` where YYYY-MM-DD is today's date. If it exists, read it and integrate any time-sensitive items into the brief.
4. If this is a partner-focused session: read `~/licensing/partners/<name>/notes.md`
5. If a project workstream is the focus: check `~/licensing/projects/` for a relevant subdir and read its `notes.md`

Note: `manifest.md` is append-only — consult on demand ("when did we last contact X?"), not at session start. `pipeline.md` and `context/business/summary.md` are available on demand but not read at startup — state.md synthesizes their actionable content.

Then open with a grounded brief derived from state.md — not "what do you want to do?" but a synthesis:

> "[N] partners need action. [Partner X] is overdue — [next action]. [Time-sensitive item]. What's your focus today?"

If `state.md` does not exist (first run): read `pipeline.md` and `context/business/summary.md` in order, then write `state.md` using the canonical structure before proceeding. Initialize other files using templates in `~/.claude/skills/licensing/templates/` if needed.

---

## Session Types

Three session types. The first two are operational — daily driving. The third is architectural.

**Pipeline session** — overview mode. Manages the full pipeline, updates `pipeline.md`,
coordinates across partners, handles strategy questions.

**Partner branch session** — focused on one partner. Same full context as a pipeline
session. Reads the partner's file. Can draft comms, update status, reason about deal
strategy, chase tangents without polluting the pipeline context. Updates `partners/<name>/notes.md`
and `manifest.md` freely.

**Architecture session** — the only session type that may write to `~/licensing/meta/`.
Declared explicitly at session open: "this is an architecture session." Used for: skill
redesign, roadmap updates, hook audits, information architecture changes. Do NOT write
to meta/ in pipeline or partner branch sessions — meta/ is read-only during operational
work.

Both operational session types read the same files. Both update shared state.

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


---

## Hooks

Conditional rules that fire automatically when specific events occur. These are not
optional — treat them as invariants of the workflow.

**On partner mention**
When a partner name appears that you haven't already read a file for this session:
check if `partners/<name>/notes.md` exists and read it before responding. Never advise on
a partner without first loading their file.

**On status change**
When a deal stage changes: update `pipeline.md` immediately — not at session end. Status is the highest-decay artifact.

After updating the stage: read `pipeline-stages.md` (in this skill's directory). Find the new stage's section and surface its tooling and next-step guidance to Brian proactively. Do not wait to be asked.

Canonical stage enum + per-stage hook behavior: `~/.claude/skills/licensing/pipeline-stages.md`.

**On deal moved to Internal Approval**
When a partner's stage is updated to `Internal Approval`: flag the following before closing the topic.

Brian must own the CS review prep end-to-end — handing Kim a sheet is not a handoff.
The failure mode: Brian sends the CS Review sheet to Kim and assumes she'll reconstruct the pitch for Mary.
She won't have the deal context. The review lands cold and doesn't advance.

Required before marking a deal as submitted for CS review:
1. Brief Kim directly — walk her through the pitch angle, the key course clusters, and any caveats (cannibalization concern, format question, co-brand flags, etc.)
2. Confirm she has what she needs to present confidently to Mary — not just the sheet, but the *why*
3. If Brian won't be in the room: write a one-paragraph brief for Kim summarizing the deal angle and what a "yes" looks like

Surface this as a checklist item whenever the stage transitions, not after the fact.

**On comms drafted or sent**
When an email or message is drafted or marked as sent: write it to `partners/<name>/notes.md`
AND append to `manifest.md`. Do both, always.

**On drafting any email or boilerplate**
Before generating any email draft, outreach message, or boilerplate text: read
`~/.claude/skills/licensing/writing-style.md` and apply exactly. No exceptions.

**On partner onboarding — two-step process**
Onboarding boilerplate is two steps; never skip ahead.

- **Step 1 (Template F):** When a deal is waiting on CS approval or content alignment but
  onboarding hasn't started, offer to send the parallel kickoff ask to the BD contact.
  This asks for consent and identifies the accounting contact. Do not send the primer yet.
- **Step 2 (Template F2):** Only after the BD contact consents. Give them the primer to
  forward to their accounting/billing contact before Mallory's DocuSign arrives. Timing is
  the entire value — it must go before the DocuSign, not after the first follow-up bounces.

Both templates are in `boilerplate/outreach.md`.

**On "add [X] as a partner"**
Triggers: "add [name] as a partner", "add [name] to the pipeline", or any explicit intent to onboard a new partner.

Four-step workflow — all steps required, in order, without waiting for the user to ask:

1. **Create subdirectory + notes** — `mkdir -p ~/licensing/partners/<slug>` and create `partners/<slug>/notes.md` using the template at `~/.claude/skills/licensing/templates/partner-notes.md`
2. **Update pipeline.md** — add a row for this partner (default stage: `Sourcing — Research` if not specified)
3. **Generate profile** — run immediately:
   ```bash
   uv run --directory /Users/bianders/vibe/licensing-project/profile python profile.py "<Partner Name>" --slug <slug>
   ```
   Output auto-saves to `partners/<slug>/profile.md`. Read it after generation.
4. **Scrape catalog** — if no URL provided, run `find-catalogues` first; then spawn one `licensing:catalog-scraper-worker` subagent with `run_in_background=true`

Append to `manifest.md` after all steps complete.

Always check the contacts DB for any known contacts at this org:

```bash
uv run --directory ~/vibe/licensing-project/catalog catalog contacts-search --company "<Partner Name>"
```

Surface any matches with their source (ce_slack / interest_form / partner_research) in the notes file.

**On new partner introduced** (passive — no explicit "add" command)
When a partner name appears in conversation with no existing file and no pipeline entry:
create `partners/<name>/notes.md` and add a row to `pipeline.md`. Then follow the same
four-step workflow above. Never leave a partner floating in conversation without landing
in both places.

**On Google Doc opened in browser**
When asked to open a Google Doc, Sheet, or Drive file in the browser: use `Bash` to run
`open "<url>"` — never use Playwright for this. Playwright hits Google's sign-in wall.

**On navigating LinkedIn Learning in Playwright**
LinkedIn Learning triggers an account chooser on every new navigation when the Playwright browser has multiple LinkedIn accounts. Bypass it by appending `?accountId=0&u=0` to any `linkedin.com/learning/...` URL. Screenshots save to `~/licensing/.playwright-mcp/` by default.

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

After reading, check if a `## Correspondence Log` section exists in the notes. If it does,
surface the most recent entry date and count. If it doesn't, note that no correspondence
has been pulled yet — offer to run a lookup before drafting any outreach.

**Ad-hoc email search — available flags**
`email-query search` supports these filters for BD research queries:
- `--before YYYY-MM-DD` / `--since YYYY-MM-DD` — date bounds
- `--from-domain domain.com` — only emails from that domain
- `--exclude-domain domain.com` — exclude a domain (repeatable: `--exclude-domain a.com --exclude-domain b.com`)
- `--no-noreply` — strip noreply/donotreply senders
- `--folder inbox|sent` — scope to a folder (default: all)

Example — external partners expressing licensing interest before a date:
```bash
email-query search "partner interested in licensing" --before 2025-08-01 \
  --exclude-domain linkedin.com --exclude-domain microsoft.com --no-noreply --folder inbox
```

**On partner correspondence lookup**
Triggers: "email history [partner]", "check correspondence", "pull emails", "have we emailed", "correspondence with".
Full procedure: `~/.claude/skills/licensing/correspondence-lookup.md`

**On Team Tracker snapshot request** — explicit only. Pull via `read_google_sheets_by_id`, overwrite `context/team_tracker_snapshot.md`, append to `manifest.md`. Never proactive.

**On "summarize [domain]"** / **"summarize business"**
Triggers: "summarize [domain]", "refresh [domain] summary", "summarize business", "refresh business summary", "update business context".
Full procedure (including MAIN-session constraint): `~/.claude/skills/licensing/summarize-business.md`

**On new business context doc added** — append to `manifest.md`; note that `[domain]/summary.md` is now stale. Do NOT auto-summarize.

**On "save context"**
Canonical invocation phrase: Brian says **"save context"**. Also fires when Claude is
about to make any substantive write to `context/` files or `SKILL.md`
on its own initiative — defined as more than a single factual correction or pointer update.

Scope:
- FIRES: context/[any].md, SKILL.md
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

**On gate decision / gate report / sync gate log**
Triggers: course passing/failing a gate mentioned in conversation; "gate report"; "funnel summary"; "sync gate log".
Full procedure: `~/.claude/skills/licensing/gate-workflow.md`

**On "resolve"**
When the user says "resolve": first update `state.md`, then review the skill.

**Step 1 — Update `state.md`:**
1. Read current `state.md`
2. Update `## Active Pipeline — Needs Attention` for any partners touched this session (stage, last action, next action)
3. Update `## Active Projects` for any workstreams touched (status line, current state)
4. Move resolved Time-Sensitive items out; add any new ones with dates
5. Carry forward unchecked Todos; remove any checked off this session
6. Update the header `_Last updated_` line with today's date and a one-phrase session description
7. Write `state.md`

If any partner with Last Action > 60 days and no substantive Next Action is found during the update, add it to `## Stale — Review`.

**Step 2 — Refresh sourcing dispatch table (conditional):**
If any sourcing subproject was touched this session, update the affected row(s) in
`projects/sourcing/notes.md`. Pull the current status and next action from the subproject's
`notes.md` — do not invent content. Update the `_Last refreshed_` date.

Sourcing subprojects: `devops-licensing-strategy`, `ai-strategy`, `ai-engineer`,
`competitive_sourcing`, `platform-sourcing`, `skill-catalog`, `tmz`, `verticals`,
`business-and-creative`. If no sourcing work happened this session, skip this step.

The dispatch table is a pull-only index — never write project narrative into it directly.

**Step 3 — Update SKILL.md:**
Review the current conversation for meaningful improvements to this skill. Update only if there are substantive changes to workflow, conventions, hooks, or tooling. Do NOT update for minor, session-specific, or speculative details. A "resolve" that produces no SKILL.md changes is fine — use judgment. Scope is limited to this skill only; do not update other skills.

**Step 4 — Root cleanup audit:**
Run `ls ~/licensing/` and diff against the canonical allowlist:

- **Files:** `pipeline.md`, `manifest.md`, `state.md`, `gate_log.json`, `CLAUDE.md`, `USAGE.md`, `README.md`, `diagram.svg`
- **Dirs:** `partners/`, `topics/`, `context/`, `projects/`, `daily/`, `scripts/`, `boilerplate/`, `partner-assets/`, `meta/`, `queue/`, `.claude/`, `.git/`, `.cache/`, `.pytest_cache/`

For each item not on the allowlist, classify and surface a one-line entry:

| Item | Type | Recommended action |
|---|---|---|
| `scrape_cisco.py` | temp script | delete |
| `snapshot_2026-04-02.xlsx` | snapshot | move → `context/library/` |
| `funnel.excalidraw` | stale diagram | delete |

Do not delete or move anything automatically. Present the table and wait for confirmation. If the root is clean, note it in one line and skip the table.

**Step 5 — Email sweep (HITL):**
Run `email-query` to check sent + inbox for active pipeline partners touched this session. For each thread where status may have changed (reply received, meeting scheduled, deal advanced), surface a brief table:

| Partner | Date | Dir | Subject | Implied status change |
|---|---|---|---|---|

Present to Brian: "Any status updates to write back from these threads?" Wait for confirmation before updating pipeline.md or partner notes. This is the same HITL pattern as the root cleanup audit — surface and confirm, don't auto-apply.

**On contact research request**
When asked to find outreach contacts for one or more partners: first query the contacts DB:

```bash
uv run --directory ~/vibe/licensing-project/catalog catalog contacts-search --company "<Partner Name>"
```

This searches across all sources (CE Slack, interest form, prior partner research). Surface any
matches — note their source so Brian knows the provenance. CE Slack matches are warm leads.

Then read `find-partner-contacts.md` (in this skill's directory) for cold outreach sources.
Follow its role hierarchy and source hierarchy for any gaps.

After identifying confirmed outreach targets: write each to the contacts DB with `source=partner_research`:

```bash
uv run --directory ~/vibe/licensing-project/catalog catalog contacts-add \
  --email "<email>" --source partner_research --partner "<slug>" \
  --name "<Full Name>" --title "<Title>" --company "<Company>"
```

Record confirmed leads in `partners/<slug>/notes.md` under an "Outreach Targets" section.
Append to `manifest.md`.

**On inbound partner vetting**
Triggers: "they reached out", "submitted the form", "inbound from", "is this legit", "how real is", "vet this org".
Full procedure (5 conduit questions, screening hierarchy, notes format): `~/.claude/skills/licensing/vetting-workflow.md`

**On internal Confluence research**
When researching an internal LinkedIn topic without a known page ID (e.g., a BD process,
team wiki, product area, or policy): run `mcp__glean_default__search` with `app="confluence"`
before reaching for Captain MCP. Glean is the discovery layer; Captain is for fetching known
pages. If Glean returns relevant results, use the URL with `mcp__glean_default__read_document`
for full content, or extract the page ID from the URL and use Captain `get_confluence_page`.

**On "Content Strategy deep dive" reference**
When Brian mentions "Content Strategy deep dive", "EN Courses deep dive", "subject-level
data", "the deep dive", or any similar reference to LiL engagement data by subject:
read `~/licensing/context/business/talent_solutions/en_courses_data_deep_dive_bd_brief_2026-03-11.md`
before responding. This is the pre-analyzed BD brief derived from the EN Courses Data
Deep Dive (February 2026) — 36 subjects, GREEN/YELLOW/RED ratings, format guidance,
pipeline gap analysis, and cross-cutting strategic findings. The raw source file is at
`~/licensing/context/business/talent_solutions/EN Courses Data Deep Dive.md` (14K lines)
— only read this if Brian asks for data not present in the brief.

**On Deal Prep → Outreach stage transition**
Before updating a partner's stage from `Deal Prep` to `Outreach` in pipeline.md:
confirm that either (a) the partner was pre-approved by Content Strategy (Motion A),
or (b) a Gate A submission doc exists at `partners/<slug>/gate-a-submission.md`,
or (c) the partner appears on a content manager's sourcing hitlist (e.g. Megan Leatham's B+C hitlist) — a named CM's explicit recommendation constitutes Gate A partner-name approval and does not require a separate CS submission.
If none of these apply, flag it and offer to generate a Gate A submission before proceeding.

**On catalog scrape complete**
Fires after any catalog scrape writes `partners/<slug>/report.md`.
Full procedure (DB course count, sheet creation, index row, cleanup): `~/.claude/skills/licensing/catalog-post-scrape.md`

**On context depth warning** — if a partner has dominated 20+ turns, flag: "This is getting deep on [Partner] — worth spinning a branch session."

**On pitch requested**
When asked to draft or generate a partner pitch / elevator pitch:
1. Check if `partners/<slug>/pitch.md` already exists — if so, read and offer to update rather than overwrite
2. Check if `partners/<slug>/profile.md` exists:
   - If yes: read it — primary source for brand identity, authority signals, alignment lever, and key risks
   - If no: generate via `uv run --project /Users/bianders/vibe/licensing-project/profile python profile.py "<Partner Name>" --slug <slug>`, save output to `partners/<slug>/profile.md`, then read it
3. Read `boilerplate/outreach.md` (Elevator Pitch Framework section) for the structure and format constraint
4. Pull scale anchor and topic scope from `partners/<slug>/notes.md`; use profile.md for brand identity and authority signal. Do not frame as filling LiL gaps — describe what the content covers, not what we lack
5. Write ONE paragraph (~100-150 words). No headers, no caveats, no alignment lever section. Internal deal risks stay in notes.md. Write to `partners/<slug>/pitch.md`
6. Append to `manifest.md`

**On catalog classified as primarily cert prep**
When a provider's catalog is primarily certification preparation — exam prep, study guides,
practice tests for professional credentials — do NOT route to standard licensing BD.
Route to Aishwarya instead.

This applies even when the credential topic is P0 in the sourcing map. The skills being
certified may be high-priority; the delivery format (cert prep) is out of scope for the
licensed library. These are not the same question.

- Cert-prep-primary orgs: DASA, DevOps Institute, FinOps Foundation → Aishwarya
- Mixed-catalog orgs: Linux Foundation, KodeKloud — evaluate practitioner training courses
  for standard licensing; flag cert-prep tracks separately for Aishwarya routing

**On TMZ catalog dispatch**
Trigger: Brian says "run catalogs for TMZ approvals", "dispatch TMZ scrapes", "process REQUEST CATALOG", or similar. Also fires when Brian asks to advance Step 5 of the TMZ triage workflow.

1. Read `tmz_triage_stage1` sheet via `read_google_sheets_by_id` (id from `context/google_docs.json`)
2. Filter rows where REQUEST CATALOG = `y` (case-insensitive)
3. Extract unique org names; run `find-catalogues` to get catalog URLs
4. Dispatch one `licensing:catalog-scraper-worker` per URL with `run_in_background=true`
5. For each org dispatched: create `partners/<slug>/notes.md` if absent (using partner-notes template); update pipeline to `Sourcing — Catalog Scrape`
6. After all workers complete: report which slugs have `catalog.json` and which need manual follow-up. Update sheet with SCRAPE STATUS if a column exists.

Full catalog dispatch mechanics: see "Full batch catalog workflow" in the Tooling section.

---

## Tooling

### Course Performance Data — Trino

Use `mcp__captain__execute_trino_query` for engagement questions. Also invoke the `trino` skill for live table/schema status before querying.

**Primary table:** `u_llsdsgroup.courseperformance_sc_dash`
- Enterprise AL: `SUM(subs_paid_nonlibrary_skill_credits_uu_l7d_v2)`
- Total AL: `SUM(skill_credits_uu_l7d_v2)`
- Filter by content type: `authorcontracttype IN ('LICENSED', 'NON_LICENSED', 'STAFF')`

Full column reference, grain, date range, and query patterns: `~/licensing/context/metrics-definitions.md`. Detailed table notes: `~/.claude/skills/licensing/tooling-reference.md`.

---

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

**`rolodex-enrichment`** — bulk LinkedIn contact enrichment: fetches profile HTML via an
authenticated Playwright browser session to extract company/school data. Script:
`~/licensing/scripts/run_enrichment.py`. Proven parameters: CONCURRENCY=5, DELAY_MS=600.
Full procedure (cookie refresh, merge script, rate limit handling): `rolodex-enrichment.md`
in this skill dir. Invoke when asked to "enrich the rolodex", "run enrichment", or when
`ed_rolodex_raw.csv` has been updated with new contacts.

**`find-catalogues`** — discovers training portal URLs for a given company. Use before
scraping to locate the right catalog URL. Output is a JSON object with
`results.{CompanyName}.primary_url` and `confidence` per company.

**Portal discovery — always do this before treating a URL as complete:**

1. **Probe subdomain + path patterns** — even if find-catalogues returns a URL, check these
   directly before scraping:
   ```
   academy.[company].com        learn.[company].com
   learning.[company].com       education.[company].com
   training.[company].com       university.[company].com
   [company].com/academy        [company].com/learn
   [company].com/training       [company].com/university
   ```

2. **Scrape the company homepage** — fetch the main site and check nav/footer for links to
   learning, academy, training, or education sections. Many providers link their portals from
   the footer or a secondary nav item that find-catalogues won't surface.

3. **ILT bundled-content flag** — if a scrape returns ILT-only content or zero courses,
   check whether the ILT listing mentions a bundled self-paced component ("lifetime access
   to [Academy]", "online courses included", "access to all material after training"). If so,
   locate and scrape that portal separately — it is often a distinct, licensable product.
   Do not close a partner on ILT evidence alone until this check is complete.

**`licensing:catalog-scraper`** — scrapes a single training provider's course catalog and
produces structured JSON, XLSX, and markdown reports. Use for evaluating a partner's content
depth and quality. Output goes to `~/licensing/partners/{slug}/` when the licensing dir exists.

Spawn one `licensing:catalog-scraper-worker` subagent per URL. Never process multiple
providers sequentially in the main thread.

Only invoke on explicit request. Do not proactively trigger scraping.

For TLM workflows (topic market maps), see the **TLM Workflow** section below.

### kramer CLIs — LiL Course Tools

Three CLIs for LiL course lookup, cert BD research, and curriculum design. All invoked via:
```bash
uv run --project /Users/bianders/Brian_Code/kramer-project <cli> <subcommand> [args]
```
CLIs: `linkedin-catalog` (course lookup/search), `certs` (cert partner + topic research), `curriculum` (LP and capstone generation).

Full parameter reference, flag tables, and usage guidance: `~/.claude/skills/licensing/kramer-reference.md` — read it before using these tools.

---

### Catalog DB

The postgres `catalog` database on Caruana holds all sourcing data across three lakes:

- **Lake 1** — direct catalog scrapes (`providers`, `courses` tables)
- **Lake 2** — Udemy instructor / Coursera institutional partner data (`platform_courses`, `platform_creators`)
- **Lake 3** — Professional Certificate interest form submissions (`interest_form_submissions`) — inbound BD signal

Project: `~/vibe/licensing-project/catalog/`
CLI: `uv run --project ~/vibe/licensing-project/catalog catalog <command>`

Key commands:
```bash
catalog interest-form-search --partnership-only   # 33 inbound partnership leads
catalog interest-form-search --topic "AI"         # demand signal by topic
catalog platform-search "kubernetes"              # top Udemy instructors (excl. UfB by default)
catalog platform-search "kubernetes" --ufb only   # UfB-only benchmark: what the best content looks like
catalog platform-search "kubernetes" --ufb include  # all results + UfB course count column
catalog search "topic"                            # Lake 1 course search
catalog stats                                     # DB overview
catalog industry-search "Cisco"                  # cross-ref prospect vs LPS/Frontier accounts
catalog industry-search --tier lps_strategic     # list all 63 LPS strategic accounts
catalog industry-search                          # tier summary (company counts per tier)
```

`industry_courses` table has five tiers (lps_strategic, lps_targeted, frontier, research, skills). UfB flag marks ~11,989 Udemy for Business courses — treat as soft blocker. For tier details, UfB handling, and refresh procedures: see `~/.claude/skills/licensing/tooling-reference.md`.

### Platform Scrapers — Lake 2 Ingest

Before syncing Coursera or Udemy data to Lake 2: read `~/.claude/skills/licensing/platform-scrapers.md`. Covers shared export contract, Corsair (Coursera) and Menuhin (Udemy) sync procedures, field mappings, and ingest commands.

---

### Checking which partners lack catalogs

```bash
for d in ~/licensing/partners/*/; do
  [[ -f "$d/catalog.json" ]] || echo "$(basename $d)"
done
```

### Full batch catalog workflow

For multi-partner batch scraping: read `~/.claude/skills/licensing/batch-catalog-workflow.md`. Covers URL discovery, dispatch list building, subagent spawning, write permission fallbacks, and JS-rendered site handling.

### Course Tiering Framework

Before tiering a partner catalog: read `~/.claude/skills/licensing/tiering-framework.md`. T1–T4 definitions, workflow, and what to share with partners vs. CS.

### CS-Approval Catalog Format

Before generating a Google Sheet for CS review: read `~/.claude/skills/licensing/cs-catalog-format.md`. Covers tab structure, column specs, level enum mapping, series handling, and dedup rules.

---

### TLM Workflow

Builds a market map of training content for a topic across all known and discovered providers.
Distinct from the batch partner catalog workflow — that starts with a known partner list; this
starts with a topic and discovers who the providers are.

Invoke when asked to "catalog [topic]", "map the [topic] market", or "run a TLM on [topic]".
Full 5-phase workflow: `~/.claude/skills/licensing/tlm-workflow.md` — read it before starting.

---

## Domain Knowledge

Before reasoning about partner fit, deal structure, or content evaluation: read `~/licensing/context/licensing_context.md`

Before sourcing strategy, BD process design, or BHAG planning: read `~/licensing/context/funnel-framework.md`

Before evaluating the existing library or benchmarking partner content: read `~/licensing/context/library-composition-analysis.md`

Before reasoning about deal stage, BD motion strategy, or internal process: read `~/licensing/context/bd-process.md`

For the full file-to-trigger-condition map, Confluence page IDs, and Google Doc registry: read `~/licensing/context/README.md`.

## Pipeline SOTs

Three canonical sources of truth for pipeline and sourcing data — never use ad-hoc sheets:

| What | SOT | Notes |
|---|---|---|
| Active deal state (partner stages, next actions) | `~/licensing/pipeline.md` | Brian's working view; update in-session |
| Org-wide intake + prioritization | Team Tracker (google_docs.json `id: 1k9vwInz_...`) | Read-only; pull snapshot on explicit request |
| Catalog / sourcing data | `catalog-cli` + postgres `catalog` DB on Caruana | Query via `catalog` CLI; see Catalog DB section |

---

## Aquifer

See `~/.claude/skills/licensing/aquifer.md` for details on the long-term token optimization
layer — when and how to operationalize validated research workflows into scheduled scripts.

---

## Subskills

**`vetting-workflow.md`** — Inbound partner vetting procedure (conduit batch queries, screening hierarchy, notes format). Read on "vet this org" triggers.

**`catalog-post-scrape.md`** — Post-scrape catalog index sync (DB course count, sheet creation, index row append, temp file cleanup). Read after any catalog scrape.

**`correspondence-lookup.md`** — Partner email history pull (three-query pattern, dedup, correspondence log format). Read on "check correspondence" triggers.

**`gate-workflow.md`** — Gate decision logging, gate reports, and gate log sync to Google Sheet. Read when gate decisions or reports are mentioned.

**`summarize-business.md`** — Domain and full business context summarization (main-session constraint, output schema). Read on "summarize [domain]" triggers.

**`cosmo.md`** — Cosmo record creation automation. Use for all Cosmo work: building blobs, running fill.py, managing the record lifecycle. **SOT: postgres `cosmo_blobs` table in `catalog` DB — not JSON files.** Covers: cosmo-cli CRUD, blob lifecycle (draft → ready → entered), golden path for new course records, Anaconda deal constants, and remaining 5 Anaconda courses.

**`gartner-pi/`** — Scrapes Gartner Peer Insights for segment rankings and vendor profiles. Use when asked to look up Gartner ratings, find top products in a market segment, or pull a vendor's Gartner profile as part of competitive research.

**`cymbii-links.md`** — URL format for CYMBII (Courses You May Be Interested In) feed cards. Use when asked for a CYMBII link for a course: `https://www.linkedin.com/feed/update/urn:li:lyndaCourse:{COURSE_ID}/`

**`generate-tocs.md`** — Full golden path for producing PTOC Cosmo Template Google Sheets for a partner's submitted courses. Use when asked to generate TOCs, create TOC sheets, or populate chapter/video structure for a licensed partner. Covers: Playwright scraper (Thinkific + other LMS patterns), row computation, Apps Script template copy, Captain MCP write + move, and `google_docs.json` registration.

**`professional_certificates.md`** — Context and tooling for the Professional Certificates BD program. **Invoke rarely** — only when the task is specifically about Prof Cert strategy or operations. Contains: business context pointer (Obsidian note), key sheet/Trino coordinates, and the golden path for adding a new LP to the Prof Cert Partner Tracker (automated Trino query + sheet append, plus HITL steps for row positioning, formatting, and course verification).

---

## Inter-Agent Citation Protocol

When operating in a multi-agent conversation (e.g. via agent-mail), tag claims by epistemic
status so the receiving agent can calibrate rather than accept everything as established fact.

| Tag | Use when |
|-----|----------|
| `[KB: file/path]` | Claim is directly traceable to a loaded pipeline, partner file, or context doc |
| `[inference]` | Derived from KB content but not explicitly stated there |
| `[open question]` | Acknowledged gap in current KB coverage |

**On receiving claims from another agent:** treat untagged claims as inference, not KB-grounded.
If a claim contradicts your KB, flag it explicitly rather than deferring.

**Post-conversation ingest:** treat multi-agent exchange outputs as tentative until a human
reviews and any relevant updates are written back to pipeline.md or a partner file.

---

## Meeting Recordings

When asked to transcribe or summarize a meeting recording: read `~/.claude/skills/licensing/meeting-recordings.md`. **Privacy rule: always use `gpt-oss:latest` via Headwater — never cloud models.**

---

## Evals

The `evals` CLI lives at `~/vibe/licensing-project/evals/`. It measures skill token usage and hook behavior against real session traces.

**Run it when asked** ("run evals", "check hook misses", "how are the hooks doing"):

```bash
uv --directory ~/vibe/licensing-project/evals run evals analyze --last 60 --weekdays-only
```

**Interpreting the output — Hook Flags column:**

- Empty → no hooks triggered that turn (normal for most turns)
- `[HOOK MISS: name]` → a trigger pattern matched the user's message but the expected tool call wasn't made in that turn window

**Known false positive: the SKILL.md injection.** When the skill loads, Claude Code injects the full SKILL.md as a user text entry. The evals code filters this out (`preceded_by_user` guard in `analyzer.py`), but if new injection types appear, a wave of hook misses at turn 1 across all sessions is the signal.

**Acting on real misses:**
1. Look at which hook and which session/turn
2. Check what the user actually typed and what tool calls were made
3. If the hook pattern is too broad (matching unrelated messages) → tighten the trigger regex in `src/evals/hooks.yaml`
4. If the hook fired correctly but the skill didn't respond → investigate the skill's hook logic in this SKILL.md's `## Hooks` section

**Other commands:**

```bash
# Token breakdown by SKILL.md section (requires ANTHROPIC_API_KEY)
uv --directory ~/vibe/licensing-project/evals run evals tokens

# Run synthetic hook tests against a live claude subprocess
uv --directory ~/vibe/licensing-project/evals run evals test

# Unified dashboard from most recent results
uv --directory ~/vibe/licensing-project/evals run evals report
```

Results are written to `~/vibe/licensing-project/evals/results/` (git-ignored).
