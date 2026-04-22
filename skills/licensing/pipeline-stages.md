# Pipeline Stages — Canonical Enum

Single source of truth for valid stage values in `pipeline.md`.
**To evolve:** edit this file only — then grep pipeline.md for old stage name and replace.

_Last updated: 2026-04-21_

---

## Quick Reference

The Google Sheet Inventory uses a sort-key prefix (`A.` / `B.` / `C.` / `D.`) to group stages by track for spreadsheet sorting. The canonical stage name used in `pipeline.md` and `state.md` does **not** include the letter prefix — the letter is a view-layer convention only.

| Sheet Group | Stage | Funnel | Tooling / Subskill |
|---|---|---|---|
| C | `Sourcing — 1 Identified` | Sourcing | TMZ triage Stage 1 sheet → Stage 2 profile review |
| C | `Sourcing — 2 Triage` | Sourcing | `catalog industry-search`, pipeline dedup, catalog-scraper-worker |
| C | `Sourcing — 3 Assessed` | Sourcing | Full portfolio eval; subsidiary routing |
| C | `Sourcing — 4 Vetting` | Sourcing | Human judgment on format, fit, or deal structure |
| C | `Sourcing — 5 Internal Elevator Pitch` | Sourcing | Tiering framework, gate-a-submission.md |
| B | `Internal Approval` | Internal Approval | gate_log.json, Gate A submission doc |
| A | `Acquisition — 1 Deal Prep` | Acquisition | find-partner-contacts, profile.py |
| A | `Acquisition — 2 Outreach` | Acquisition | boilerplate/outreach.md, writing-style.md |
| A | `Acquisition — 3 In Conversation` | Acquisition | email-query, NDA (go/ltsbd-legal) |
| A | `Acquisition — 4 Contracting` | Acquisition | cosmo.md (M1+M2), bd-process.md |
| D | `Publication — Content Delivery` | Publication | partner-assets/ delivery spec |
| D | `Publication — Production Intake` | Publication | Robert / Saya handoff |
| D | `Publication — In Production` | Publication | cosmo.md (M3+) |
| D | `Publication — Live` | Publication | cymbii-links.md |
| — | `Blocked` | Terminal | — |
| — | `Unable to Partner` | Terminal | — |

---

## Per-Stage Hook Behavior

Read the section for the **new** stage when a partner transitions. Surface tooling proactively.

### Sourcing — 1 Identified
Partner is on radar. No catalog work started.
- Create `partners/<slug>/notes.md` from template if it doesn't exist
- Add to `pipeline.md` if absent
- Note which sourcing channel surfaced them (TMZ, inbound, CS rec, etc.)
- **TMZ path:** org enters this stage after Brian approves it in the Stage 1 triage sheet. Profile generation (Stage 2) happens here before advancing to Triage. See `projects/tmz/notes.md → Triage Workflow`.

### Sourcing — 2 Triage
Feasibility check + catalog scrape. Triage and scraping are now a single stage.
- Run `catalog industry-search "<Partner Name>"` — check DB and LPS/Frontier account tiers
- Cross-ref `pipeline.md` for duplicates or prior attempts
- Cross-ref `Unable to Partner` rows — confirm not already dropped
- If LPS strategic: note warm intro opportunity
- Run find-catalogues to locate training portal URL
- If confidence is high/medium: spawn `licensing:catalog-scraper-worker` subagent
- JS-rendered SPAs may need a Playwright follow-up worker
- Once `catalog.json` is written and tiering applied (catalog-post-scrape workflow): advance to `Sourcing — 4 Vetting` or `Sourcing — 5 Internal Elevator Pitch` depending on clarity of fit

### Sourcing — 3 Assessed
Full portfolio swept; subsidiary or deal routing decided.
- Used primarily for holding companies (SEI, large platforms) after all subsidiaries are evaluated
- Note routing decision per subsidiary in `partners/<slug>/notes.md`

### Sourcing — 4 Vetting
Active human evaluation — format, IP, fit, or deal structure unclear.
- Generate partner profile if absent: `uv run --project /Users/bianders/vibe/licensing-project/profile python profile.py "<Partner Name>" --slug <slug>`
- Specific questions to resolve: format viability, production quality, IP ownership, deal structure constraints
- Advance to `Sourcing — 5 Internal Elevator Pitch` once vetting questions resolved and catalog has a clear pitch-worthy cluster

### Sourcing — 5 Internal Elevator Pitch
Course list identified and tiered; building the internal pitch package for CS.
- Confirm tiered catalog sheet exists
- Create `partners/<slug>/gate-a-submission.md` from template if absent
- Pitch package: partner brief, course scope (T1+T2), topic alignment, distribution angle

### Internal Approval
Package submitted to CS (Mary/Kim); awaiting topic/brand approval.
- Log Gate A submission in `gate_log.json` (Gate 10)
- Confirm `partners/<slug>/gate-a-submission.md` exists
- Note submission date in `partners/<slug>/notes.md`
- In Motion B: often collapses with Deal Prep — advance directly if course scope agreed simultaneously

### Acquisition — 1 Deal Prep
Post-CS-approval prep. Partner doesn't know you're coming yet.
- Generate partner profile if absent: `uv run --project /Users/bianders/vibe/licensing-project/profile python profile.py "<Partner>" --slug <slug>`
- Consider PDF gut check (read `bd-process.md`)
- Identify outreach contacts: use find-partner-contacts skill

### Acquisition — 2 Outreach
First contact sent; awaiting reply.
- Read `writing-style.md` before drafting any message
- Use Elevator Pitch Framework from `boilerplate/outreach.md`
- Log in `partners/<slug>/notes.md` under Correspondence Log

### Acquisition — 3 In Conversation
Active dialogue — calls, NDA, course scope alignment with CS.
- Pull correspondence log: email-query vs. partner domain
- NDA: automated via Conga (go/ltsbd-legal); standard partners only; flag exceptions
- Track call notes and course scope status in `partners/<slug>/notes.md`

### Acquisition — 4 Contracting
Onboarding sent; Cosmo record created; contract in motion.
- Read `cosmo.md` subskill — golden path for record creation
- Milestones 1+2 in Cosmo must complete before contract is sent
- Redlines: read `bd-process.md` → Uta Kreye + Stephanie Goff (Legal)

### Publication — Content Delivery
Contract signed; awaiting content assets from partner.
- Share delivery spec (`partner-assets/`) with partner
- Note expected delivery date in `partners/<slug>/notes.md`

### Publication — Production Intake
Assets received; Robert and Saya managing Production workflow.
- Log handoff in `partners/<slug>/notes.md`
- Cosmo milestone tracking transitions to Production here

### Publication — In Production
QA, format transformation, Cosmo M3+ in progress.
- Read `cosmo.md` for M3+ detail
- No BD action needed unless blockers surface

### Publication — Live
Courses published on LinkedIn Learning.
- Generate CYMBII link: `cymbii-links.md` subskill
- Confirm all Cosmo milestones complete

### Blocked
Stalled — no action without an external trigger.
- Note the blocker and trigger condition in `partners/<slug>/notes.md`

### Unable to Partner
Dropped — format gate fail, partner declined, catalog not fit, or contract failure.
- Note reason in `partners/<slug>/notes.md`

---

## Updating This Taxonomy

1. Add a stage: add a row to Quick Reference + a per-stage section
2. Rename a stage: update Quick Reference, the section header, all `pipeline.md` rows, and the SKILL.md hook
3. Deprecate a stage: move to `## Deprecated` below with the replacement stage noted

## Deprecated

| Stage | Replacement | Notes |
|---|---|---|
| `Sourcing — Classification` | `Sourcing — 4 Vetting` | Retired 2026-04-21. LLM-driven relevance judgment now handled at catalog creation time. |
| `Sourcing — Catalog Scrape` | `Sourcing — 2 Triage` | Retired 2026-04-21. Scraping is now part of the Triage step. |
| `Sourcing — Gate A Prep` | `Sourcing — 5 Internal Elevator Pitch` | Renamed 2026-04-21 for clarity. |
| `Sourcing — Identify` | `Sourcing — 1 Identified` | Renamed 2026-04-21; numbered for stage ordering. |
| `Sourcing — Vetting` | `Sourcing — 4 Vetting` | Renamed 2026-04-21; numbered for stage ordering. |
| `Sourcing — Assessed` | `Sourcing — 3 Assessed` | Renamed 2026-04-21; numbered for stage ordering. |
| `Sourcing — Triage` | `Sourcing — 2 Triage` | Renamed 2026-04-21; numbered for stage ordering. |
| `Acquisition — Deal Prep` | `Acquisition — 1 Deal Prep` | Renamed 2026-04-21; numbered for stage ordering. |
| `Acquisition — Outreach` | `Acquisition — 2 Outreach` | Renamed 2026-04-21; numbered for stage ordering. |
| `Acquisition — In Conversation` | `Acquisition — 3 In Conversation` | Renamed 2026-04-21; numbered for stage ordering. |
| `Acquisition — Contracting` | `Acquisition — 4 Contracting` | Renamed 2026-04-21; numbered for stage ordering. |
| `Internal Approval — Gate A Pending` | `Internal Approval` | Renamed 2026-04-21; simplified. |
