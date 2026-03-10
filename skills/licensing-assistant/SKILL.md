---
name: licensing-assistant
description: >
  Persistent assistant for LinkedIn Learning content licensing BD work. Maintains a live
  pipeline of partner deals, per-partner context, and cross-session continuity. Use when
  working in ~/licensing/, managing partner relationships, evaluating content opportunities,
  drafting partner comms, or doing any licensing BD task. Triggers on "load licensing
  assistant", "open licensing", or any licensing pipeline / partner management work.
---

# Licensing Assistant

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
  context/             # Read-only reference docs (licensing_context.md, google_docs.json, team_tracker_snapshot.md)
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
4. Read the **last 15 lines** of `~/licensing/manifest.md` — what changed recently
5. If `~/licensing/business_context/summary.md` exists: read it — strategic environment context
6. If this is a partner-focused session: read `~/licensing/partners/<name>.md`

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
strategy, chase tangents without polluting the pipeline context. Updates `partners/<name>.md`
and `manifest.md` freely.

Both session types read the same files. Both update shared state.

**When to suggest a branch session:** If a single partner has dominated 20+ turns, or
you've drafted/iterated on comms, flag it: "This is getting deep on [Partner] — worth
spinning a branch session to keep the pipeline context clean."

---

## Shared State: What Gets Updated and When

**`pipeline.md`** — update whenever a partner's stage, last action, or next action changes.

**`partners/<name>.md`** — freeform. Add notes, email drafts, deal context, contact log,
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
check if `partners/<name>.md` exists and read it before responding. Never advise on
a partner without first loading their file.

**On status change**
When a deal stage, last action, or next action changes: update `pipeline.md` immediately —
not at session end. Status is the highest-decay artifact.

**On comms drafted or sent**
When an email or message is drafted or marked as sent: write it to `partners/<name>.md`
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
In a partner-focused session: read `partners/<name>.md` fully before saying anything.
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

**On context update request**
When the user asks to save, update, or persist context from the current session:

1. Draft the proposed updates as text — do NOT write files yet.
2. Read `context-review-prompt.md` from this skill's directory.
3. Substitute into the template:
   - `{{ target_files }}`: list of file paths the review subagent should read
     (one per line — the files being updated, not the proposed content)
   - `{{ proposed_updates }}`: the full draft updates, clearly labeled by target file
4. Spawn a review subagent via the Agent tool with the substituted prompt.
   Use `run_in_background=False` — the review must complete before any writes.
5. Present the subagent's verdict to the user. Apply APPROVE items directly.
   For MODIFY items, show the suggested change and apply unless the user objects.
   For REJECT items, surface the reason and ask the user how to proceed.
6. Execute file writes only after the review is complete.
7. Append to `manifest.md` as usual.

This hook fires for any request to update scratchpad.md, context/ files, or SKILL.md.
It does NOT fire for manifest.md (append-only log, no review needed) or partner files
(operational notes, not shared context artifacts).

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

**On context depth warning**
If a single partner has dominated 20+ turns or comms have been iterated multiple times:
flag it proactively — "This is getting deep on [Partner] — worth spinning a branch
session to keep the pipeline context clean." Do this before the context becomes too
loaded to summarize.

---

## Tooling

Skills available for licensing research and catalog collection:

**`find-partner-contacts`** — technique for finding cold outreach targets at external
partner companies. Role hierarchy, source hierarchy (ZoomInfo/RocketReach snippet searches),
query patterns, and what to discard. Reference: `find-partner-contacts.md` in this skill dir.

**`find-catalogues`** — discovers training portal URLs for a given company. Use before
scraping to locate the right catalog URL. Output: `training_urls.json` with
`results.{CompanyName}.primary_url` and `confidence` per company.

**`catalog-scraper`** — scrapes a single training provider's course catalog and produces
structured JSON, XLSX, and markdown reports. Use for evaluating a partner's content depth
and quality. Output goes to `~/licensing/partners/{slug}/` when the licensing dir exists.

When catalog collection is needed across multiple partners at once, use Claude Code's native
subagent dispatch — spawn one `catalog-scraper-worker` subagent per partner URL.

Only invoke these on explicit request. Do not proactively trigger scraping.

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

**Step 3 — Spawn one catalog-scraper-worker subagent per URL**:
Per CLAUDE.md rules, spawn a separate `catalog-scraper-worker` subagent for each URL.
Never run multiple scrapes sequentially in the main thread. Run all workers with
`run_in_background=true`. Each worker writes its output (catalog.json, catalog.xlsx,
report.md) directly to `~/licensing/partners/{slug}/` and updates `catalog_registry.json`.
No consolidation step needed — workers have direct filesystem access.

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

---

## Aquifer: Long-Term Token Optimization Layer

**What it is:** `~/Brian_Code/aquifer-project/` is a Python toolkit Brian built for
automated data collection and multi-model research. It is the eventual production layer
for the business_context/ knowledge base — a cheaper, schedulable replacement for the
Claude Code agent research workflows used to initially populate the knowledge base.

**The paradigm shift it enables:**
- **Phase 1 (now):** Use Claude Code agents + Captain MCP tools to establish research
  patterns — expensive but high-capability. Pave the cowpath.
- **Phase 2 (once patterns harden):** Translate validated patterns into aquifer scripts
  that run against local models (Ollama, etc.) on a schedule. Same output, fraction of
  the token cost.
- **Phase 3:** Aquifer becomes the background refresh layer (RSS monitoring, competitor
  earnings, Slack digests). Claude Code handles edge cases, novel research, and anything
  requiring Confluence/internal-source access.

**Aquifer's current capabilities:**
- `collect/rss` — RSS/Atom feed parsing for continuous monitoring
- `collect/youtube` — YouTube channel metadata into PostgreSQL
- `collect/podcasts` — Bulk podcast collection
- `research/brave` — Brave search + URL fetch
- `research/exa` — Exa semantic search
- `research/perplexity`, `research/openai`, `research/google_deep_research` — multi-model research
- `research/10k` — SEC EDGAR 10-K filing retrieval
- `research/snapshot.py` — fan-out orchestrator: takes structured question list, runs
  parallel async LLM calls via `conduit.batch`, aggregates to markdown
- `research/strategy/main.py` — multi-model: same query through Perplexity + Exa + OpenAI

**What aquifer currently lacks that this system provides:**
- Internal source access (Confluence, Slack, Google Docs) — only Claude Code + Captain MCP
- Hierarchical `business_context/` storage with domain summaries and staleness tracking
- The summarization hooks that roll up to the top-level omnibus summary

**When to reference aquifer:** When Brian asks to operationalize or schedule a research
workflow that has been validated through Claude Code agents. The signal is: "we've done
this 3+ times the expensive way and the output format is stable." That's when a pattern
is ready to be distilled into aquifer.
