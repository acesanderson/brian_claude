# Pipeline Stages — Canonical Enum

Single source of truth for valid stage values in `pipeline.md`.
**To evolve:** edit this file only — then grep pipeline.md for old stage name and replace.

_Last updated: 2026-04-17_

---

## Quick Reference

| Stage | Funnel | Tooling / Subskill |
|---|---|---|
| `Sourcing — Identify` | Sourcing | TMZ triage Stage 1 sheet → Stage 2 profile review |
| `Sourcing — Triage` | Sourcing | `catalog industry-search`, pipeline dedup |
| `Sourcing — Catalog Scrape` | Sourcing | find-catalogues + catalog-scraper-worker |
| `Sourcing — Classification` | Sourcing | `classify.py` (Pass 1 + 2), classifier YAMLs |
| `Sourcing — Gate A Prep` | Sourcing | Tiering framework, gate-a-submission.md |
| `Internal Approval — Gate A Pending` | Internal Approval | gate_log.json, Gate A submission doc |
| `Internal Approval — Scope Sign-off` | Internal Approval | (collapses with Gate A in Motion B) |
| `Acquisition — Deal Prep` | Acquisition | find-partner-contacts, profile.py |
| `Acquisition — Outreach` | Acquisition | boilerplate/outreach.md, writing-style.md |
| `Acquisition — In Conversation` | Acquisition | email-query, NDA (go/ltsbd-legal) |
| `Acquisition — Contracting` | Acquisition | cosmo.md (M1+M2), bd-process.md |
| `Publication — Content Delivery` | Publication | partner-assets/ delivery spec |
| `Publication — Production Intake` | Publication | Robert / Saya handoff |
| `Publication — In Production` | Publication | cosmo.md (M3+) |
| `Publication — Live` | Publication | cymbii-links.md |
| `Blocked` | Terminal | — |
| `Unable to Partner` | Terminal | — |

---

## Per-Stage Hook Behavior

Read the section for the **new** stage when a partner transitions. Surface tooling proactively.

### Sourcing — Identify
Partner is on radar. No catalog work started.
- Create `partners/<slug>/notes.md` from template if it doesn't exist
- Add to `pipeline.md` if absent
- Note which sourcing channel surfaced them (TMZ, inbound, CS rec, etc.)
- **TMZ path:** org enters this stage after Brian approves it in the Stage 1 triage sheet. Profile generation (Stage 2) happens here before advancing to Catalog Scrape. See `projects/tmz/notes.md → Triage Workflow`.

### Sourcing — Triage
Feasibility check before investing scrape resources.
- Run `catalog industry-search "<Partner Name>"` — check DB and LPS/Frontier account tiers
- Cross-ref `pipeline.md` for duplicates or prior attempts
- Cross-ref `Unable to Partner` rows — confirm not already dropped
- If LPS strategic: note warm intro opportunity

### Sourcing — Catalog Scrape
URL discovery and catalog scraping.
- Run find-catalogues to locate training portal URL
- If confidence is high/medium: spawn `licensing:catalog-scraper-worker` subagent
- JS-rendered SPAs may need a Playwright follow-up worker
- Do not advance to Classification until `catalog.json` is written to `partners/<slug>/`

### Sourcing — Classification
Two-pass classifier on the scraped catalog.
- Confirm `partners/<slug>/catalog.json` exists
- Generate partner profile if absent: `uv run --project /Users/bianders/vibe/licensing-project/profile --directory /Users/bianders/vibe/licensing-project/profile python profile.py "<Partner Name>" --slug <slug>` — read it before evaluating the catalog; it surfaces IP risks, alignment lever, and licensability signal
- Pass 1 (deterministic): auto-applied via `classifier-blockers.yaml`
- Pass 2 (LLM): `scripts/classify.py partners/<slug>/catalog.json`
- After classification: apply tiering (T1–T4), create tiered Google Sheet, register in `google_docs.json`

### Sourcing — Gate A Prep
Course list identified and tiered; building the Gate A package for CS.
- Confirm tiered catalog sheet exists
- Create `partners/<slug>/gate-a-submission.md` from template if absent
- Gate A package: partner brief, course scope (T1+T2), topic alignment, distribution angle

### Internal Approval — Gate A Pending
Package submitted to CS (Mary/Kim); awaiting topic/brand approval.
- Log Gate A submission in `gate_log.json` (Gate 10)
- Confirm `partners/<slug>/gate-a-submission.md` exists
- Note submission date in `partners/<slug>/notes.md`

### Internal Approval — Scope Sign-off
Topic approved; agreeing with CS on which specific courses to license.
- Track CS course list feedback in `partners/<slug>/notes.md`
- In Motion B: often collapses with Gate A Pending — advance directly to Deal Prep if course scope agreed simultaneously

### Acquisition — Deal Prep
Post-CS-approval prep. Partner doesn't know you're coming yet.
- Generate partner profile if absent: `uv run --project /Users/bianders/vibe/licensing-project/profile python profile.py "<Partner>" --slug <slug>`
- Consider PDF gut check (read `bd-process.md`)
- Identify outreach contacts: use find-partner-contacts skill

### Acquisition — Outreach
First contact sent; awaiting reply.
- Read `writing-style.md` before drafting any message
- Use Elevator Pitch Framework from `boilerplate/outreach.md`
- Log in `partners/<slug>/notes.md` under Correspondence Log

### Acquisition — In Conversation
Active dialogue — calls, NDA, course scope alignment with CS.
- Pull correspondence log: email-query vs. partner domain
- NDA: automated via Conga (go/ltsbd-legal); standard partners only; flag exceptions
- Track call notes and course scope status in `partners/<slug>/notes.md`

### Acquisition — Contracting
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

_(none yet)_
