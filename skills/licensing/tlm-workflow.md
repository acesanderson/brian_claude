# TLM Workflow

Builds a market map of training content for a topic across all known and discovered providers.
Distinct from the batch partner catalog workflow — that starts with a known partner list;
this starts with a topic and discovers who the providers are.

Invoke when asked to "catalog [topic]", "map the [topic] market", or "run a TLM on [topic]".

---

## Phase 1: Classify SKILL or TOOL

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

---

## Phase 2: Provider Discovery

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

---

## Phase 3: Scrape New Providers

For each confirmed new provider, dispatch one `licensing:catalog-scraper-worker` subagent
per URL. All run with `run_in_background=true`. Never process multiple providers sequentially.

While scraping runs, proceed to Phase 4 using the DB as it stands. Re-run the export
step after all subagents finish.

---

## Phase 4: DB Query

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

---

## Phase 5: Output

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
