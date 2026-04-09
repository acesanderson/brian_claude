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

## Data Privacy — Non-Negotiable

When the user requests **local model inference** (`gpt-oss`, `llama`, `qwen`, etc.), it is because the content is **proprietary or confidential**. This applies to all meeting recordings, partner materials, pipeline data, and internal documents.

- NEVER substitute a cloud model (haiku, gpt-mini, claude, gpt-5, gemini, etc.) as a fallback
- NEVER send proprietary content to any external API, even "just this once"
- If Headwater (AlphaBlue) is unreachable: stop, report the outage, and wait for the user to resolve it
- `conduit query --model gpt-oss` and `conduit batch --model gpt-oss` now route automatically through Headwater — no `--local` flag needed

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
  skills/              # One directory per skill TLM (roadmap.md + catalog XLSX + report)
  context/             # Reference docs — see context/README.md for file-to-trigger map
  projects/            # Parallel workstreams (each has its own subdir + notes.md)
  spec/                # Day specs — one YYYY-MM-DD.md file per working day. Each spec defines
                       # the day's tasks, inputs, constraints, and Claude Code instance assignments.
                       # Checked at session start — read during Session Start Protocol if today's file exists.
  gate_log.json        # Course-level gate decision log — SOT for funnel metrics and CYA (see projects/pipeline-ops/notes.md)
  scripts/             # Python utilities; Classifier: classify.py, classifier_models.py, classifier_prompt.j2
  boilerplate/         # Reusable templates (outreach.md: Template A–E outreach + Elevator Pitch Framework)
  partner-assets/      # PDF assets for partner outreach: Content License Agreement, Instructor Analytics Dashboard,
                       # LinkedIn Learning Content Licensing one-pager, Content Delivery Video Format Guidelines
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
3. Check for a day spec: `~/licensing/spec/YYYY-MM-DD.md` where YYYY-MM-DD is today's date. If it exists, read it and integrate any time-sensitive items into the brief.
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
When a deal stage, last action, or next action changes: update `pipeline.md` immediately —
not at session end. Status is the highest-decay artifact.

**On comms drafted or sent**
When an email or message is drafted or marked as sent: write it to `partners/<name>/notes.md`
AND append to `manifest.md`. Do both, always.

**On drafting any email or boilerplate**
Before generating any email draft, outreach message, or boilerplate text: read
`~/.claude/skills/licensing/writing-style.md` and apply exactly. No exceptions.

**On new partner introduced**
When a partner is mentioned with no existing file and no pipeline entry: create
`partners/<name>/notes.md` using the template at `~/.claude/skills/licensing/templates/partner-notes.md`
and add a row to `pipeline.md` in the same action. Never leave a partner floating in
conversation without landing in both places.

**On Google Doc opened in browser**
When asked to open a Google Doc, Sheet, or Drive file in the browser: use `Bash` to run
`open "<url>"` — never use Playwright for this. Playwright hits Google's sign-in wall.

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
Trigger phrases: "email history [partner]", "check correspondence", "pull emails",
"have we emailed", "what's our email history with", "correspondence with".

1. Read `partners/<slug>/notes.md` to extract the partner domain from the **Website** field
   (e.g., `anaconda.com` from `https://anaconda.com`).
2. Run all three queries in parallel:
   ```bash
   # Inbound
   uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --from "*.domain.com" --limit 50
   # Outbound
   uv run --directory /Users/bianders/vibe/outlook-email-project email-query list --to "*@domain.com" --limit 50
   # Broad text search (catches name variants, forwarded threads, etc.)
   uv run --directory /Users/bianders/vibe/outlook-email-project email-query search "Partner Name" --text --limit 20 --no-noreply --folder inbox
   ```
3. Deduplicate across the three result sets (same subject + date = same message).
   Sort chronologically ascending.
4. Overwrite the `## Correspondence Log` section in `partners/<slug>/notes.md`:
   ```markdown
   ## Correspondence Log
   _Last pulled: YYYY-MM-DD_

   | Date | Dir | Subject | Contact |
   |---|---|---|---|
   | 2026-03-01 | inbound | Re: LinkedIn Learning partnership | jess@anaconda.com |
   | 2026-03-05 | sent | Re: LinkedIn Learning partnership | jess@anaconda.com |
   ```
   - **Dir**: `inbound` (folder=inbox) or `sent` (folder=sent)
   - **Contact**: the external party's address (from for inbound, to for sent)
   - If a message is part of a thread worth reading, note the conversation_id in a trailing comment
5. Append to `manifest.md`:
   `- YYYY-MM-DD | correspondence-pull | partners/<slug>/notes.md | N emails (X inbound, Y sent)`
6. Surface a brief summary: total count, date range, most recent exchange, any open threads
   (sent with no reply, or reply awaiting response).

**On Team Tracker snapshot request** — explicit only. Pull via `read_google_sheets_by_id`, overwrite `context/team_tracker_snapshot.md`, append to `manifest.md`. Never proactive.

**On "summarize [domain]"**
When the user says "summarize [domain]" or "refresh [domain] summary" (where domain is
one of: financial_health, flagship_feed, premium, talent_solutions, ai_strategy,
org_context, competitive_landscape, member_metrics):
1. List all files in `context/business/[domain]/` excluding `summary.md`
2. Read each one
3. Write a synthesis to `context/business/[domain]/summary.md` — key facts, trends,
   strategic reads, sources with dates, and a staleness note (oldest source date)
4. Append to `manifest.md`
Do not summarize if the domain directory has no docs yet — flag it as unpopulated instead.

IMPORTANT: Execute this in the MAIN session, not as a subagent. Summarization is
read-then-write on local files — subagents cannot write files without explicit Write
permission grants, which defeats the purpose of delegation. Subagents are for research
(external I/O); summarization is for the main thread.

**On "summarize business"** (also: "refresh business summary", "update business context")
When the user triggers a full business summary refresh:
1. Read every `context/business/[domain]/summary.md` that exists
2. Write `context/business/summary.md` using this schema:
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

**On "sync gate log"** — sync `gate_log.json` to Google Sheet. See `~/.claude/skills/licensing/tooling-reference.md` for full procedure.

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

**Step 2 — Update SKILL.md:**
Review the current conversation for meaningful improvements to this skill. Update only if there are substantive changes to workflow, conventions, hooks, or tooling. Do NOT update for minor, session-specific, or speculative details. A "resolve" that produces no SKILL.md changes is fine — use judgment. Scope is limited to this skill only; do not update other skills.

**On contact research request**
When asked to find outreach contacts for one or more partners: read
`find-partner-contacts.md` (in this skill's directory) before starting. Follow its
role hierarchy and source hierarchy exactly. Record confirmed leads in
`partners/<slug>/notes.md` under an "Outreach Targets" section. Append to `manifest.md`.

**On inbound partner vetting**
When an inbound lead arrives (interest form, cold email, LinkedIn message) from an
organization that is NOT a well-known brand: run a legitimacy check before investing
BD time. Trigger phrases: "they reached out", "submitted the form", "inbound from",
"is this legit", "how real is", "vet this org".

Governance is the primary signal. Use the conduit skill with `conduit batch -m sonar-pro`
to ask these 5 questions in parallel:

1. **Named leadership**: "Who founded [org] and who are the key executives? Are their
   names, LinkedIn profiles, and prior career histories publicly verifiable?"

2. **Board and affiliations**: "Does [org] have a named advisory board or notable outside
   affiliates? Are these individuals independently verifiable with real public profiles?"

3. **Accreditation**: "Is [org] accredited by any recognized external standards body
   (ANSI/ISO 17024, IACET, or similar)? Or are their credentials self-issued?"

4. **Employer recognition**: "Do major employers, job postings, or enterprise L&D programs
   recognize or require [org] certifications/credentials? Are they listed on LinkedIn
   profiles at scale?"

5. **Independent community signal**: "What do independent reviews on Reddit, Trustpilot,
   or professional forums say about [org]? Are there real practitioners discussing them?"

Interpret results using this screening hierarchy:
- **Named CEO/founder with verifiable prior career** → proceed to research
- **Named board with outside affiliates you can independently verify** → meaningful positive signal
- **Elaborate governance language, no named individuals** → flag; require video call with
  multiple team members before investing further
- **Anonymous leadership + negative forum signal** → dead stop; surface to Brian immediately

After running: present a verdict (real / thin but real / red flag), note the strongest
positive and negative signals, and recommend next action. Do NOT add to pipeline or
invest further research until vetting is complete if red flags are present.

Then write the findings to `partners/<slug>/notes.md` under a `## Credibility` section
(create it if absent; skip this step for established brands where vetting wasn't run).
Section format:

```markdown
## Credibility

**Verdict:** real | thin but real | red flag
**Date checked:** YYYY-MM-DD

**Strongest positive signals:**
- [e.g., Named CEO Russell Sarder with verifiable prior company (NetCom Learning)]
- [e.g., Advisory board includes Sunil Prashara, former PMI CEO]

**Strongest negative signals:**
- [e.g., No external accreditation — ISO 17024 "alignment" only]
- [e.g., No employer recognition in job postings or L&D programs]

**Recommended next action:** [e.g., Proceed with outreach / Require video call with multiple
team members before investing further / Dead stop — surface to Brian]
```

Presence of this section = vetting was done. Absence = established brand, no check needed.
Append to `manifest.md`: `- YYYY-MM-DD | vetted | partners/<slug>/notes.md | verdict: <verdict>`

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

**On Researching → Outreach stage transition**
Before updating a partner's stage from `Researching` to `Outreach` in pipeline.md:
confirm that either (a) the partner was pre-approved by Content Strategy (Motion A),
or (b) a Gate A submission doc exists at `partners/<slug>/gate-a-submission.md`.
If neither exists, flag it and offer to generate one before proceeding.

**On catalog scrape complete**
After any catalog scrape writes `partners/<slug>/report.md`:

1. Read `context/google_docs.json` to get `catalog_index.id`.
2. Get the course count from the DB:
   ```bash
   uv run --project ~/vibe/licensing-project/catalog catalog providers
   ```
   Find the row for this provider slug and read the `Courses` column.
3. Create a catalog sheet for this partner:
   - If no catalog sheet exists yet: create one via `create_google_sheets_spreadsheet`
     titled `"[Partner] — Course Catalog ([Month Year])"`. Write a header row
     (provider, title, url, format, level, duration, category, date_scraped).
     `level` must be one of: `Beginner` | `Intermediate` | `Advanced`. Map raw partner values
     to this enum before writing (e.g., "Introductory" → Beginner, "Professional" → Intermediate).
     Register it in `context/google_docs.json` under `"read_write_docs"` with
     `"permissions": "read-write"` and a description noting course count and date.
   - If a sheet already exists (check `google_docs.json`): skip creation.
4. Append one row to the catalog index sheet (`catalog_index.id`) via
   `write_google_sheets_by_id` (mode: append) with columns:
   Partner | Catalog Sheet URL | Context | Courses | Status | Date Scraped | Notes

   Get `Status` from the `report.md` `Scrape status:` line.
   Get `Courses` from the DB (Step 2 above), not from any file.

   **Column C (Context) format:** `[Stage] — [POC]. [1-2 sentence description.]`
   Stage must be one of the official enum values (same as pipeline.md Stage column):
   Pre-intake: `Identified` | `Vetting` | `Propose for Intake`
   Post-intake: `Researching` | `Outreach` | `In Conversation w/Partner` |
   `Approvals/Contracting` | `Project Management` | `In Production` | `Live`
   Terminal: `Blocked` | `Unable to Partner`

   **Column E (Status) enum:** `complete | partial | blocked | pending`
   - `complete` — full catalog captured, no known gaps
   - `partial` — scrape incomplete due to auth/JS walls; more data potentially recoverable
   - `blocked` — structural issue (no catalog, wrong format, MIT-licensed, etc.) — don't retry
   - `pending` — scrape dispatched, not yet complete
5. Append to `manifest.md`:
   `- YYYY-MM-DD | synced | catalog_index → Google Sheet | <Slug>: N courses`

6. Delete temp file if somehow still present:
   ```bash
   rm -f /tmp/scrape_<slug>.json
   ```
7. Delete `scrape_{slug}.py` at `~/licensing/` root if it exists:
   ```bash
   rm -f ~/licensing/scrape_<slug>.py
   ```

**On context depth warning** — if a partner has dominated 20+ turns, flag: "This is getting deep on [Partner] — worth spinning a branch session."

**On pitch requested**
When asked to draft or generate a partner pitch / elevator pitch:
1. Check if `partners/<slug>/pitch.md` already exists — if so, read and offer to update rather than overwrite
2. Read `boilerplate/outreach.md` (Elevator Pitch Framework section) for the 4-part structure
3. Pull scale anchor, gap hook, and tier counts from `partners/<slug>/notes.md`
4. Use `conduit batch -m sonar-pro` for any missing authority or market signals
5. Write to `partners/<slug>/pitch.md`
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

**`find-catalogues`** — discovers training portal URLs for a given company. Use before
scraping to locate the right catalog URL. Output is a JSON object with
`results.{CompanyName}.primary_url` and `confidence` per company.

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

Two scrapers feed Lake 2 (`platform_courses` / `platform_creators`) with data from competing
platforms. Each scraper has an export adapter that writes a catalog-ingestible JSON file, then
calls `catalog platform-ingest` to load it. Use these when you need fresh Coursera or Udemy
data in the DB — e.g., before running `catalog platform-search`.

**Shared export contract** (JSON array, each record):

| Field | Type | Notes |
|---|---|---|
| `platform_id` | str | required |
| `title` | str | required |
| `url` | str | required |
| `platform` | str | required — `'coursera'` or `'udemy'` |
| `is_free` | bool | required |
| `avg_rating` | float\|null | |
| `num_reviews` | int\|null | |
| `enrollments` | int\|null | |
| `product_type` | str\|null | |
| `difficulty` | str\|null | |
| `skills` | str\|null | comma-separated |
| `partners` | str\|null | Coursera only |
| `instructors` | str\|null | Udemy only |
| `headline` | str\|null | Udemy only |
| `num_lectures` | int\|null | Udemy only |
| `duration_hours` | float\|null | Udemy only |
| `ufb` | bool\|null | Udemy only; always null at ingest — set post-ingest by `load_ufb.py` |

Ingest call (same for both platforms):
```bash
uv run --project ~/vibe/licensing-project/catalog catalog platform-ingest <file> <platform>
```

**Do not touch scraping logic in either project.** The export/sync layer is the only integration point.

---

#### Corsair — Coursera (`$BC/corsair-project`)

Scrapes Coursera's full catalog via GraphQL. Saves raw data to `src/corsair/courses.json`.
Export adapter maps `CourseraCourseSearchResult` → shared spec and ingests into Lake 2.

**Manual sync:**
```bash
uv run --project ~/Brian_Code/corsair-project corsair-sync
# or with custom output path:
uv run --project ~/Brian_Code/corsair-project corsair-sync --output /tmp/corsair_export.json
```

**Auto-sync after scrape** (opt-in):
```bash
# In corsair-project/.envrc, set:
export CORSAIR_AUTO_SYNC=1
# Then run the scraper normally — sync fires automatically at the end of main()
uv run --project ~/Brian_Code/corsair-project python -m corsair.search_courses
```
`CORSAIR_AUTO_SYNC` defaults to `0`. The hook is at the bottom of `search_courses.py:main()`.

**Key files:**
- `src/corsair/search_courses.py` — GraphQL scraper; writes `courses.json`
- `src/corsair/export.py` — `to_catalog_json(output_path)` — maps fields, validates, writes export file
- `src/corsair/sync_catalog.py` — `sync()` / `main()` — calls export then platform-ingest

**Field mapping:**

| Coursera field | platform_courses field |
|---|---|
| url path stripped of leading `/` | `platform_id` |
| `name` | `title` |
| `https://www.coursera.org` + url | `url` |
| `avgProductRating` | `avg_rating` |
| `numProductRatings` | `num_reviews` |
| `enrollments` | `enrollments` |
| `productType` | `product_type` |
| `productDifficultyLevel` | `difficulty` |
| `skills` (list → comma-sep) | `skills` |
| `partners` (list → comma-sep) | `partners` |
| hardcoded `False` | `is_free` |
| hardcoded `'coursera'` | `platform` |

---

#### Menuhin — Udemy (`$BC/menuhin-project`)

_Stub — to be filled in by the Menuhin maintainer._

Scrapes Udemy's catalog. Export adapter maps Udemy API fields → shared spec and ingests into Lake 2.

**Manual sync:**
```bash
# TODO: fill in once menuhin-sync entry point is implemented
```

**Auto-sync after scrape** (opt-in):
```bash
# TODO: MENUHIN_AUTO_SYNC env var, same pattern as Corsair
```

**Key files:** _(to be documented)_

**Field mapping:** _(to be documented — see agreed spec in shared contract above)_

---

### Classifier

Two-pass course-level classifier that determines whether a scraped course is a licensing candidate.

**Pass 1 — deterministic pre-filter** (no LLM): reads `context/classifier-blockers.yaml`. Blocks on format, product_type, title, and description patterns. Fast, free.

**Pass 2 — LLM-as-judge**: renders `scripts/classifier_prompt.j2` per course, runs via `ConduitBatchAsync` with `gpt-oss:latest`. Returns a `ClassifierResult` Pydantic model with per-signal verdicts and a `proceed / flag / reject` recommendation.

```bash
# Batch — classify all unclassified courses in a partner catalog
/Users/bianders/Brian_Code/conduit-project/.venv/bin/python scripts/classify.py partners/<slug>/catalog.json

# Single course spot-check (no file write)
/Users/bianders/Brian_Code/conduit-project/.venv/bin/python scripts/classify.py --single 3 partners/<slug>/catalog.json

# Re-classify already-classified courses
/Users/bianders/Brian_Code/conduit-project/.venv/bin/python scripts/classify.py --overwrite partners/<slug>/catalog.json
```

Results written back into `catalog.json` per course under a `classifier` key.

**Living config files** (update these to change classifier behavior — no code changes needed):
- `context/classifier-blockers.yaml` — hard eliminators; add/remove patterns freely
- `context/classifier-quality-signals.yaml` — LLM signal prompts; edit `prompt:` field to change how the LLM evaluates each signal
- `context/topic-priority.yaml` — green/yellow/red topic rubric; update whenever Content Strategy's priorities shift

**Local model constraint**: `gpt-oss:latest` runs via HeadwaterClient on AlphaBlue. Do NOT run Ollama directly on MacBook (saturates memory). On MacBook, `conduit query --model gpt-oss` now routes automatically through Headwater — no special flags needed. If Headwater is unreachable, stop and report; do NOT substitute a cloud model.

### Checking which partners lack catalogs

```bash
for d in ~/licensing/partners/*/; do
  [[ -f "$d/catalog.json" ]] || echo "$(basename $d)"
done
```

### Full batch catalog workflow

When asked to scrape multiple partners:

**Step 1 — Find URLs** (find-catalogues):
Run find-catalogues on the list of partner names.
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
report.md) directly to `~/licensing/partners/{slug}/`.
No consolidation step needed — workers have direct filesystem access.

**Write permission fallback:** Workers frequently hit Write permission walls and cannot
create files. When a worker returns structured catalog data in its result output instead
of writing a file, write `catalog.json` in the main session using that data. Do not
re-dispatch the worker — the scrape is complete; only the write is blocked. Check which
slugs have files after all workers complete: `for d in ~/licensing/partners/*/; do [[ -f "$d/catalog.json" ]] || echo "$(basename $d)"; done`

**JS-rendered sites:** Some catalogs (e.g. New Relic, Oracle MyLearn) are JS-rendered
SPAs — static fetch returns no course titles, only page shell. Signal: worker reports
a course *count* but no *titles*, or notes the page is a SPA/requires JS. Fix: dispatch
a follow-up worker with explicit Playwright instructions (use `browser_navigate` +
`browser_evaluate` or `browser_snapshot` to render the catalog). Flag these in the
initial dispatch summary so the follow-up is easy to queue.

### Course Tiering Framework

After a catalog is scraped, assign every course a tier before sending to partners or CS. This
replaced the old gap-first approach (avoid overlap with LiL library). The new approach: include
everything, let CS decide on overlap. Tier is a signal of expected impact, not a pass/fail gate.

| Tier | Definition | Typical signals |
|---|---|---|
| **T1** | Super foundational — highest guaranteed ALs | Intro/overview courses; CS priority domains (risk mgmt, cybersecurity, cloud, leadership); topics with proven LiL demand |
| **T2** | Complementary — not in library, compelling | Critical coverage gaps; niche-but-relevant topics; courses with no LiL equivalent |
| **T3** | Licensable long tail | Viable but more specialized; CS decides whether to include |
| **T4 (SKIP)** | Clearly not wanted | Exam prep, youth/teen programs, retake exams, product tool training, EN-AU locale duplicates, generic soft skills with no construction/domain anchor |

**Workflow:** Assign tiers in `catalog.json` (add a `"tier"` key per course), write a tiered
Google Sheet sorted T1 → T2 → T3 → T4 (SKIP), register in `google_docs.json`, append to catalog
index. Update partner `notes.md` and `pipeline.md` with sheet URL and tier counts.

**When sending to partners:** Share T1+T2 as the proposed licensing scope. T3 is available but
not leading with it. T4 (SKIP) rows stay off partner-facing docs.

**When sending to CS for Gate A:** Share full tiered sheet (T1–T3). Overlap with existing LiL
library is not a disqualifier — CS makes that call.

---

### CS-Approval Catalog Format

When generating a Google Sheet for CS review, use this exact structure:

**Tab 1 — "Tier Definitions"**

| Tier | What it means | Typical signals |
|---|---|---|
| T1 | Review first — highest structural fit | Foundational/overview courses; proven LiL demand topics; priority domains (AI/ML, cybersecurity, cloud, leadership, finance) |
| T2 | Review second — complementary fit | Clear coverage gaps; niche-but-relevant; no LiL equivalent |
| T3 | Review if bandwidth — licensable long tail | Viable but specialized; CS decides |
| T4 (SKIP) | Structurally ineligible — do not review | Exam prep, retake exams, product tool training (platform-locked), locale duplicates, youth/teen programs |

This tier taxonomy is structural only — it signals review order based on observable criteria. It does not predict CS decisions or reflect editorial quality judgments.

**Tab 2 — "Course catalog"**

Columns (in order):

| Column | Header | Notes |
|---|---|---|
| A | `tier (descriptions in first tab)` | T1 / T2 / T3 / T4 (SKIP) |
| B | `title` | Cleaned title — see series handling below |
| C | `description` | From catalog; for series parts, append "Part N of the [Series Name]." sentence |
| D | `level` | Strict enum: `Beginner` \| `Intermediate` \| `Advanced` |
| E | `duration` | Prefix with `~` — all values are estimates (e.g., `~30 min`, `~1 hour`) |
| F+ | partner-specific | e.g., `price`, `url`, `date_scraped` |
| last-1 | `license? (x)` | CS marks with x |
| last | `CS notes` | CS freeform |

Sort order: T1 → T2 → T3 → T4 (SKIP). The "T4 (SKIP)" label sorts correctly after T3 lexicographically.

**Level enum mapping** (normalize raw partner values before writing):
- "Introductory", "Beginner", "Foundational", "101", "Basic" → `Beginner`
- "Professional", "Intermediate", "Practitioner", "200-level" → `Intermediate`
- "Advanced", "Expert", "300-level" → `Advanced`

**Series handling:** When course titles follow the pattern `"Topic -- Series Name (Part N)"`:
- Strip the ` -- Series Name (Part N)` from the title — keep only the topic name
- Append `"Part N of the Series Name."` as a sentence at the end of the description

**Deduplication rules:**
- Online vs. non-online: normalize title by stripping `" - Online"` / `": Online"` suffix (case-insensitive). Keep the online variant when both exist; drop the offline duplicate.
- Locale variants (`--- EN-AU`, `--- EN-CA`, `--- EN-GB`, `--- ZH-SG`, `--- DE-DE`, etc.): drop all locale variants. If no base English version exists for a locale variant, include it but flag in CS notes.
- Professional certificate bundles: manually verify that courses listed individually are not also counted as part of a bundle row. Do not double-count content.

**Duration sources (in priority order):**
1. CPE credits in description field (`CPE Credits: N` → `~N hours`)
2. Scraped from course page (look for clock icon pattern in HTML)
3. Median placeholder for the partner's catalog (label clearly, e.g., `~30 min`)

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

**`gartner-pi/`** — Scrapes Gartner Peer Insights for segment rankings and vendor profiles. Use when asked to look up Gartner ratings, find top products in a market segment, or pull a vendor's Gartner profile as part of competitive research.

**`generate-tocs.md`** — Full golden path for producing PTOC Cosmo Template Google Sheets for a partner's submitted courses. Use when asked to generate TOCs, create TOC sheets, or populate chapter/video structure for a licensed partner. Covers: Playwright scraper (Thinkific + other LMS patterns), row computation, Apps Script template copy, Captain MCP write + move, and `google_docs.json` registration.

**`professional_certificates.md`** — Context and tooling for the Professional Certificates BD program. **Invoke rarely** — only when the task is specifically about Prof Cert strategy or operations. Contains: business context pointer (Obsidian note), key sheet/Trino coordinates, and the golden path for adding a new LP to the Prof Cert Partner Tracker (automated Trino query + sheet append, plus HITL steps for row positioning, formatting, and course verification).

---

## Meeting Recordings

Workflow for transcribing and summarizing meeting recordings (all-hands, team meetings, 1:1s, etc.).

**Privacy rule:** Recordings contain proprietary content. Always use `gpt-oss:latest` via Headwater. Never use cloud models.

### Golden Path

**Step 1 — Transcribe** (siphon CLI):
```bash
siphon extract <recording.mp3>
```
Output is a plain-text transcript (speaker-labeled if diarization is available).

**Step 2 — Write summary prompt** (Write tool → `/tmp/<slug>_summary_prompt.txt`):
```
You are summarizing a meeting transcript. Extract:
- Key decisions made
- Action items (owner, what, by when if stated)
- Main topics discussed (3–7 bullets per topic)
- Notable quotes or data points

Transcript:
<paste transcript>
```

**Step 3 — Summarize via HeadwaterClient** (Python, using pre-existing headwater-client venv):
```python
from __future__ import annotations
import asyncio
from pathlib import Path
from headwater_client.client.headwater_client_async import HeadwaterAsyncClient
from headwater_api.classes import BatchRequest
from conduit.domain.request.generation_params import GenerationParams
from conduit.domain.config.conduit_options import ConduitOptions

async def main() -> None:
    prompt = Path("/tmp/<slug>_summary_prompt.txt").read_text()
    params = GenerationParams(model="gpt-oss:latest", temperature=0.3)
    options = ConduitOptions(project_name="siphon-summary", include_history=False)
    batch_req = BatchRequest(prompt_strings_list=[prompt], params=params, options=options)
    async with HeadwaterAsyncClient() as client:
        response = await client.conduit.query_batch(batch_req)
    msg = response.results[0].last
    content = msg.content
    if isinstance(content, str):
        print(content)
    elif isinstance(content, list):
        print("".join(c if isinstance(c, str) else c.text for c in content))
    else:
        print(str(content))

asyncio.run(main())
```
Run with: `/Users/bianders/Brian_Code/headwater/headwater-client/.venv/bin/python /tmp/summarize.py`

**Step 4 — Save to Obsidian** (Write tool):
- Path: `$MORPHY/MEET-YYYY-MM-DD-<slug>.md`
- Use the summary output directly as the note body
- Slug: lowercase, hyphen-separated, descriptive (e.g., `company-connect`, `cm-ai-research-tools`)
