---
name: li-golden-post-finder
description: Use when tasked with finding real, publicly accessible LinkedIn posts for golden dataset construction. Two modes: (1) single-slot — given one slot spec, find one post; (2) batch — given a list of pending slots (or the full golden_dataset.json), fill all of them efficiently in a single agent session without spawning one agent per slot.
---

# li-golden-post-finder

Two modes: **single-slot** (fill one slot) and **batch** (fill all pending slots in one session).

The default for filling multiple slots is batch mode — do NOT spawn one agent per slot. That pattern wastes 10-15x tokens on context overhead for work that is fundamentally a few API calls per slot.

## Prerequisites

- `uv` — https://docs.astral.sh/uv/getting-started/installation/
- `BRAVE_API_KEY` env var
- brave-web-search skill at `~/.claude/skills/brave-web-search/`

## Input

You will receive a slot spec in this format:

```
Slot {N} | {Tier} | {Type} | {Topic category} | {What it tests}
```

Example:
```
Slot 1 | Calibration Anchor | Clear YES | Company News | Major layoff, 1,000+ employees, named company, recent
```

## Output

Write a JSON file to `~/job_application/data/golden_posts/slot_{N:02d}.json`:

```json
{
  "slot": 1,
  "tier": "Calibration Anchor",
  "type": "Clear YES",
  "topic_category": "Company News",
  "url": "https://www.linkedin.com/posts/...",
  "text_preview": "15-20 word preview of the post content",
  "accessible": true,
  "final_label": "YES",
  "notes": "One sentence: why this post fits the slot."
}
```

If no accessible match found after 3 attempts:

```json
{
  "slot": 1,
  "tier": "Calibration Anchor",
  "type": "Clear YES",
  "topic_category": "Company News",
  "url": null,
  "text_preview": null,
  "accessible": false,
  "final_label": null,
  "notes": "No match found. Queries tried: [list them]"
}
```

## Workflow

### Step 1: Construct queries

Use the query strategy for your slot type (see Query Strategies below).
Generate 1-3 queries. Start with the most specific.

### Step 2: Search

```bash
uv run --directory ~/.claude/skills/brave-web-search python conduit.py search "<query>"
```

From the 5 results, identify candidates where:
- URL is a `/posts/` path (not `/pulse/`, `/company/`, `/in/` profile pages)
- Snippet content is consistent with the slot criteria
- Post appears recent (2025 preferred; 2024 acceptable for slow-moving categories like Executive Moves)

### Step 3: Fetch and verify

```bash
uv run --directory ~/.claude/skills/brave-web-search python conduit.py fetch "<url>"
```

Verify:
- `accessible: true` — content returned, not an auth wall or empty page
- Content matches the slot criteria after reading
- For YES slots: Intent passes (informative, not promotional), Quality passes (at least one line of context/analysis beyond a headline), Topic passes (falls into the named category)
- For NO slots: the specific failure mode is present and clear
- For edge case slots: the described tension is genuinely present

If the fetch returns an empty or auth-blocked page, try the next candidate from search results.
Make up to 3 fetch attempts across up to 2 search queries before writing a null result.

### Step 4: Write output file

Create `~/job_application/data/golden_posts/` if it does not exist.
Write the JSON result file as specified above.

---

## Query Strategies

### YES anchors — search for the news event type

| Slot type | Query pattern |
|---|---|
| Layoff (1,000+ employees) | `site:linkedin.com/posts "layoffs" "employees" 2025` |
| CEO/C-suite departure | `site:linkedin.com/posts "CEO" "steps down" OR "resigns" 2025` |
| Economic data (Fed, GDP, jobs) | `site:linkedin.com/posts "Federal Reserve" OR "jobs report" OR "GDP" 2025` |
| Major legislation / policy | `site:linkedin.com/posts "signed" OR "passed" legislation industry impact 2025` |
| Market/sector movement | `site:linkedin.com/posts stocks sector "market" tariff OR earnings 2025` |
| Industry trend (AI, automation) | `site:linkedin.com/posts "AI" OR "automation" industry trend reshaping 2025` |
| Startup funding | `site:linkedin.com/posts "Series" funding "million" raised 2025` |
| Research/survey | `site:linkedin.com/posts survey "percent" OR "%" professionals report 2025` |

### NO anchors — search for the failure mode signal

| Slot type | Query pattern |
|---|---|
| Promotional product launch | `site:linkedin.com/posts "thrilled to announce" "new product" OR "new feature"` |
| Employee recognition | `site:linkedin.com/posts "congratulations" "years" "team" OR "anniversary"` |
| Hiring announcement | `site:linkedin.com/posts "we are hiring" OR "we're hiring" "open roles"` |
| Thought leadership / career tips | `site:linkedin.com/posts "5 tips" OR "framework" leadership career advice` |
| Verbatim headline repost | `site:linkedin.com/posts "via" news headline no added text` (then verify on fetch) |
| Career advice / recruiter tips | `site:linkedin.com/posts "tips" interview resume "get noticed" recruiter` |

### Edge cases — search for the tension

The tension is the point: search for content that sits near the boundary described in the slot.

Examples:
- Intent tension (company announcement as news): `site:linkedin.com/posts "industry is changing" "we built" OR "we launched"`
- Quality floor (barely passes): `site:linkedin.com/posts "this matters because" OR "what this means" news brief`
- Executive Moves threshold: `site:linkedin.com/posts "VP" OR "director" "leaves" OR "joins" company 2025`
- Tariff political/business split: `site:linkedin.com/posts "tariffs" "impact on" industry OR sector 2025`
- RTO recency tension: `site:linkedin.com/posts "return to office" data percent employees 2025`
- Research methodology opacity: `site:linkedin.com/posts "study" "percent" OR "%" professionals "according to" 2025`
- General news thin tie: `site:linkedin.com/posts "Super Bowl" OR "Olympics" business OR economic impact`

### Genuine ambiguity slots — search for the specific ambiguous scenario

Use keywords that surface content exhibiting the specific multi-dimensional tension described. Accept the first accessible post that genuinely exhibits the stated ambiguity — do not hold out for a "perfect" example.

---

## Verification Criteria Reference

**Intent PASS:** Primary purpose is to inform. May contain some promotional language but that is not the dominant purpose.

**Intent FAIL:** Post is primarily promoting a product, service, company, or the author. News is used as a hook, not as the substance.

**Quality PASS:** Provides at least one line of context or analysis beyond restating the headline. Source (if linked) is not spammy or unreliable.

**Quality FAIL:** Verbatim headline repost, zero added context, or clearly unreliable/spammy source.

**Topic PASS:** Content falls into one of: Company News, Industry News & Trends, Executive Moves, Economy & Jobs, Markets & Stocks, Work & Career Trends, General News with Professional Tie, Policy & Legislation with Business Impact, Research & Surveys, Other.

**Topic FAIL:** Career/job-search advice, pure personal stories, entertainment/celebrity, party politics without economic tie, local news without business impact.

---

## Part 2: Batch Mode

Use this when filling multiple pending slots. **One agent, one context window, all slots sequentially.** This is ~10-15x cheaper than spawning one agent per slot, and avoids Brave API rate-limit collisions (429s) caused by parallel agents hammering the same endpoint simultaneously.

### When to use batch vs. single-slot

| Situation | Mode |
|---|---|
| Filling one specific slot or retrying one failure | Single-slot (Part 1) |
| Initial fill of the full 50-slot dataset | Batch — single agent |
| Retry pass after a batch run (nulls only) | Batch — single agent, filtered |
| You explicitly want parallelism and accept rate-limit risk | Batch — parallel (see below) |

### Step 1: Load the slot list

Read `~/job_application/data/golden_dataset.json`. Build the work queue by filtering for slots where:
- `url` is `null` (not yet filled), OR
- `accessible` is `false` (previous attempt failed — retry mode)

Slots with a non-null `url` are already done — skip them.

### Step 2: Use `query_hint` — do not regenerate queries

Each slot in `golden_dataset.json` has a `query_hint` field. Use it directly as your first search query. Do not spend tokens regenerating what is already there. Only fall back to the Query Strategies table (Part 1) if the `query_hint` returns zero useful candidates.

### Step 3: Process slots sequentially

For each pending slot, run the single-slot workflow (Steps 2-4 from Part 1):
1. Search using `query_hint`
2. Fetch and verify the best candidate
3. Write the slot file to `~/job_application/data/golden_posts/slot_{N:02d}.json` **immediately** — do not batch writes
4. Move to the next slot

Write each slot file before moving on. If the agent is interrupted mid-run, completed slots are already persisted and the next run skips them.

### Rate limiting

Brave API has per-second limits. When running sequentially, add a 1-2 second pause between search calls to avoid 429 errors. If a 429 occurs, wait 5 seconds and retry once before logging a null.

```bash
# Between search calls, pause briefly:
sleep 2  # or handle in your loop if scripting
```

In practice: the sequential single-agent approach naturally spaces calls enough that 429s are rare. The rate-limit problem in prior runs came from 50+ agents firing simultaneously.

### Step 4: Null handling

If a slot fails after 3 attempts (across 2 queries), write the null-format JSON (see Part 1) with `"notes"` listing the queries tried. Continue to the next slot — do not stop the batch.

### Parallel batch option (use only if speed is the priority)

If you want to parallelize, split the pending slots into **groups of 8-10**, spawn one agent per group (5-6 agents total for a 50-slot dataset). Each agent handles its cohort sequentially. This gives a ~5x wall-clock speedup at ~5x the single-agent cost — still 5-10x cheaper than one-agent-per-slot.

**Do not** fire one agent per slot. That is what was done in the first run and it caused 43/75 rate-limit errors and paid full context overhead for 3 API calls per agent.

### Persistence format reference

The slot files and master index are the source of truth:

```
~/job_application/data/
  golden_dataset.json          # master index — 50 slot specs with query_hint, status
  golden_posts/
    slot_01.json               # individual result per slot
    slot_02.json
    ...
```

A completed slot file (filled by batch run, not yet human-annotated):
```json
{
  "slot": 21,
  "tier": "gold_question",
  "type": "yes_edge",
  "topic_category": "Industry News & Trends",
  "url": "https://www.linkedin.com/posts/...",
  "text_preview": "15-20 word preview",
  "accessible": true,
  "final_label": "YES",
  "notes": "One sentence: why this post fits the slot."
}
```

Human annotation (added by `data/scorer.py` after manual review) adds an `"annotation"` key to the slot file. The batch agent does not write this key — that is the human's step.

### End-of-batch summary

After processing all pending slots, report:
- Slots filled (url found, accessible): N
- Slots null (no match after 3 attempts): list slot numbers
- Any rate-limit errors encountered and how handled

This lets the operator decide whether to run a retry pass or fill nulls manually.
