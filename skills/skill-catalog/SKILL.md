---
name: skill-catalog
description: Build a cross-provider course catalog for a given skill or tool. Discovers relevant training providers via web search, scrapes new ones, queries the catalog DB, and produces a filtered XLSX + markdown report. Use when asked to "catalog [topic]", "map the [topic] market", "find courses on [topic] across providers", or "generate a [topic] TLM". NOTE: will be merged into licensing-catalog skill in a future session.
---

# Skill Catalog

Builds a market map of available training content for a given topic across all known
and discovered providers. Stores everything in the catalog database on Caruana.
End artifacts: filtered XLSX (all matching courses across the full DB) + markdown report.

## Tooling

- **Brave search**: `uv run --directory ~/.claude/skills/brave-web-search python conduit.py search "QUERY"`
- **Catalog CLI**: `uv run --directory ~/vibe/licensing-project/catalog python -m catalog <command>`
- **Catalog-scraper**: invoke the `catalog-scraper` skill for each new provider
- **Subagent dispatch**: one `catalog-scraper-worker` subagent per provider URL (per CLAUDE.md rules)


---

## Data Sources (Three Lakes)

The catalog DB draws from three complementary data sources. Each has its own ingest
workflow. All are stored in postgres on Caruana (`catalog` database).

### Lake 1: Direct Catalog Scrapes

**What**: Course listings scraped from provider training portals.
**Tables**: `providers`, `courses`
**CLI**: `catalog ingest`, `catalog search`, `catalog merge-export`
**Ingest**: via catalog-scraper subagents → `catalog ingest <json_file>`
**When to refresh**: per TLM run (scrape new providers, re-run merge-export)

### Lake 2: Platform Creator Sourcing

**What**: Udemy instructor and Coursera institutional partner data from LinkedIn's internal
platform acquisition sheets (`~/licensing/Udemy_Courses.xlsx`, `~/licensing/Coursera_Courses.xlsx`).
**Tables**: `platform_courses`, `platform_creators`, `platform_course_creators`
**CLI**: `catalog platform-ingest`, `catalog platform-search`
**Ingest**: `uv run --project ~/vibe/licensing-project/catalog python scripts/load_platform_data.py`
**When to refresh**: when updated XLSXes are available from the platform team

### Lake 3: Interest Form

**What**: Professional Certificate interest form submissions — orgs who want LinkedIn to
distribute their certificate programs. Also the best inbound demand signal for which
topics are underserved. Sourced from `u_leadgen.lead_record` in LinkedIn's Trino warehouse.
**Tables**: `interest_form_submissions`
**CLI**: `catalog interest-form-ingest`, `catalog interest-form-search`, `catalog interest-form-stats`
**Query**: `~/.claude/skills/skill-catalog/queries/interest_form.sql` (run via `execute_trino_query` MCP)
**Ingest**: See "Lake 3 Refresh Workflow" below
**When to refresh**: monthly, or before any TLM run where inbound demand signal is relevant

#### Lake 3 Refresh Workflow

1. Run the Trino query via `execute_trino_query` MCP tool (server: `holdem`):
   ```
   -- paste content of ~/.claude/skills/skill-catalog/queries/interest_form.sql
   ```
2. Write the returned rows to a JSON file:
   ```
   ~/licensing/interest_form_YYYY-MM-DD.json
   ```
3. Run the ingest script:
   ```bash
   uv run --project ~/vibe/licensing-project/catalog python scripts/load_interest_form.py \
     ~/licensing/interest_form_YYYY-MM-DD.json
   ```
4. Verify with: `catalog interest-form-stats`

Key fields:
- `certificate_topic` — structured topic selection (AI/ML, Management, Marketing, etc.)
- `preferred_content` — contains "partnership model" for the 32 inbound BD leads
- `other_topic` — free-text when "Other" selected (niche/emerging topics)
- `company` + `role` — context for qualifying inbound leads

---

## Phase 1: Topic Classification and Mapping

### Step 1 — Classify: SKILL or TOOL?

Before anything else, determine the input type:

**TOOL** — a specific technology, framework, product, or platform.
Examples: Kubernetes, Terraform, Python, LangChain, Docker, Redis, Salesforce, Ansible.
Rule: one canonical name, narrow scope, course titles typically include the name verbatim.

**SKILL** — a professional domain, discipline, or competency.
Examples: DevOps, Data Science, Machine Learning, Cloud Computing, Project Management,
AI Engineering, Cybersecurity, Site Reliability Engineering.
Rule: broad scope, sub-topics vary in naming, a course on "Docker Essentials" is a DevOps
course even though it doesn't say "DevOps".

If ambiguous (e.g., "CI/CD" — tool or skill?), state your interpretation and ask the user
to confirm before proceeding.

### Step 2 — Topic mapping (SKILL only)

For a SKILL: propose a sub-topic breakdown before searching. Format:

```
Topic: DevOps
Type: SKILL

Proposed sub-topics (will be used as search terms):
  - Docker / containers
  - Kubernetes / container orchestration
  - CI/CD (Jenkins, GitHub Actions, GitLab CI)
  - Infrastructure as Code (Terraform, Pulumi, Ansible)
  - Monitoring / observability (Prometheus, Grafana, Datadog)
  - GitOps / ArgoCD / Flux
  - Site reliability engineering
  - Platform engineering

Confirm, edit, or add sub-topics before I proceed?
```

Wait for confirmation or edits. The user may expand, trim, or redirect.
This step is skipped for TOOLs — proceed directly to Phase 2.

**Note**: If the user already provided sub-topics or seed providers in their initial
request, incorporate them and skip the back-and-forth — confirm once and move on.

---

## Phase 2: Provider Discovery

### Step 1 — Check what's already in the DB

```bash
uv run --directory ~/vibe/licensing-project/catalog python -m catalog providers
```

Note which existing providers are plausibly relevant to the topic (by name — no deep
catalog check yet). These are "known providers" for the topic.

### Step 2 — Search for new providers

For each search query below, use the brave-web-search skill:
```bash
uv run --directory ~/.claude/skills/brave-web-search python conduit.py search "QUERY"
```

**Queries to run** (adapt to topic):
- `"[topic]" training courses certification provider`
- `"[topic]" online training platform NOT coursera NOT udemy NOT pluralsight`
- `best "[topic]" training vendors enterprise`

For SKILLs, also run queries on 2-3 of the most distinctive sub-topics:
- `"[sub-topic]" official training certification`

**What to look for**: direct content producers — the company whose name is on the courses.
Discard: learning platforms (Coursera, Udemy, Pluralsight, LinkedIn Learning, Skillshare,
edX, Udacity — these are distribution, not producers). Discard: bootcamps, universities
(unless they have a structured catalog clearly accessible for licensing).

Collect: company name + likely training portal URL for each candidate.

### Step 3 — Present the candidate list for confirmation

Show a clear split between known and new:

```
PROVIDERS ALREADY IN DB (will query but not re-scrape):
  - CloudThat (402 courses)
  - Cisco (154 courses)

NEW CANDIDATES FOUND — confirm to scrape:
  [ ] Linux Foundation — training.linuxfoundation.org
  [ ] HashiCorp — developer.hashicorp.com/tutorials
  [ ] KodeKloud — kodekloud.com/courses
  [ ] A Cloud Guru — acloudguru.com/courses

Skip any? Add any not listed?
```

Wait for confirmation. Do NOT begin scraping until approved.
If the user removes a candidate, note it in the final report as "excluded by user".
If the user adds a provider not found via search, add it to the scrape list.

---

## Phase 3: Scraping New Providers

For each confirmed new provider, dispatch a `catalog-scraper-worker` subagent.
Per CLAUDE.md batch scraping rules: one subagent per URL, all run with
`run_in_background=true`. Never process multiple providers sequentially.

Each subagent runs the full catalog-scraper workflow (Phases 0–6), which includes
the `catalog ingest` step to persist to the DB.

While scraping runs, proceed to Phase 4 using the DB as it currently stands.
The query in Phase 4 will automatically include any newly ingested providers once
their subagent completes — re-run the export step after all subagents finish.

---

## Phase 4: DB Query

### Build search terms

**TOOL**: single term — the tool name.
```bash
uv run --directory ~/vibe/licensing-project/catalog python -m catalog search "kubernetes" --limit 10000
```

**SKILL**: run one search per sub-topic, collect all results, deduplicate by (provider, title).
```bash
uv run --directory ~/vibe/licensing-project/catalog python -m catalog search "docker" --limit 10000
uv run --directory ~/vibe/licensing-project/catalog python -m catalog search "kubernetes" --limit 10000
uv run --directory ~/vibe/licensing-project/catalog python -m catalog search "terraform" --limit 10000
# ... one per confirmed sub-topic
```

After deduplication, export to XLSX:
```bash
uv run --directory ~/vibe/licensing-project/catalog python -m catalog export "[primary-term]" \
  --output ~/licensing/catalogs/[topic-slug]_catalog_[YYYY-MM-DD].xlsx
```

For SKILLs with multiple search terms, the export command covers only the primary term.
Generate the combined XLSX programmatically by merging results from each sub-topic search
and deduplicating on `(provider_slug, title)` before writing with pandas.

**Output location**: `~/licensing/catalogs/` (create if needed).

---

## Phase 5: Output

### 5a — New providers summary

Report what was added to the DB as a result of this run:

```
NEW PROVIDERS ADDED TO CATALOG DB:
  - Linux Foundation: 87 courses ingested
  - HashiCorp: 43 courses ingested
  - KodeKloud: 210 courses ingested
  - A Cloud Guru: [auth-gated — 0 courses; see dark matter note]

DB now contains [N] total providers and [M] total courses.
```

### 5b — XLSX

Path: `~/licensing/catalogs/[topic-slug]_catalog_[YYYY-MM-DD].xlsx`

Columns: provider, title, url, description, duration, level, format, price, category,
instructor, date_scraped. For SKILLs, add a `matched_subtopic` column indicating which
sub-topic search term returned this course.

### 5c — Markdown report

Save to: `~/licensing/catalogs/[topic-slug]_report_[YYYY-MM-DD].md`

Structure:

```markdown
# [Topic] Course Catalog Report
**Date**: YYYY-MM-DD
**Type**: SKILL | TOOL
**Total courses**: N (across M providers)

## Coverage Summary
| Provider | Courses matched | Notes |
|---|---|---|
| Linux Foundation | 52 | ... |
| KodeKloud | 38 | ... |

## Sub-topic Coverage (SKILL only)
| Sub-topic | Courses | Providers |
|---|---|---|
| Kubernetes | 91 | CloudThat, KodeKloud, Linux Foundation |
| Terraform | 34 | CloudThat, HashiCorp |

## Methodology
[Brief description of how providers were found and what was scraped.
Focus on what's notable: unusual catalog structure, scraping limitations,
anything that affected coverage. Skip routine details.]

## Dark Matter
[Providers where content is known to exist but was inaccessible:
auth walls, login gates, incomplete scrapes, or providers explicitly
excluded from search scope. Example: "A Cloud Guru requires login
for full catalog — current scrape shows 0 courses; actual catalog
is ~400+ courses. Credential access would unlock this."]

## Excluded Providers
[Any providers found during discovery that were not scraped, and why:
excluded by user, low confidence, learning platform (not a producer), etc.]

## Self-Optimization Notes
[What worked well. What searches were fruitless. What queries should
be added or changed for future runs. What providers should be
investigated more deeply.]

## Future: Content Fit Classifier
A planned LLM-based classifier will score each course for licensing
fit against the LinkedIn Learning content rubric. Not yet implemented.
When available, it will add a `fit_score` and `fit_rationale` column
to the XLSX and a ranked shortlist to this report.
```

---

## Conventions

**Topic slug**: lowercase, hyphenated. "DevOps" → `devops`. "Site Reliability Engineering" → `site-reliability-engineering`.

**Output directory**: `~/licensing/skills/{slug}/`. Create with `mkdir -p` if it doesn't exist.
A `roadmap.md` should exist here before the run (created during planning). If it doesn't,
create it from the topic mapping step before proceeding.

**Manifest**: append to `~/licensing/manifest.md`:
```
- YYYY-MM-DD | created | ~/licensing/catalogs/[slug]_catalog_YYYY-MM-DD.xlsx | [N] courses, [M] providers, SKILL|TOOL
- YYYY-MM-DD | created | ~/licensing/catalogs/[slug]_report_YYYY-MM-DD.md | [topic] catalog report
```

**Re-running**: if a catalog for this topic already exists in `~/licensing/catalogs/`,
note it and ask whether to overwrite or create a new dated version.
