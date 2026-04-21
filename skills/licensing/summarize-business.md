# Business Context Summarization

## Summarize a single domain

Triggers: "summarize [domain]", "refresh [domain] summary" where domain is one of:
`financial_health`, `flagship_feed`, `premium`, `talent_solutions`, `ai_strategy`,
`org_context`, `competitive_landscape`, `member_metrics`.

1. List all files in `context/business/[domain]/` excluding `summary.md`
2. Read each one
3. Write a synthesis to `context/business/[domain]/summary.md` — key facts, trends,
   strategic reads, sources with dates, and a staleness note (oldest source date)
4. Append to `manifest.md`

Do not summarize if the domain directory has no docs yet — flag it as unpopulated instead.

**IMPORTANT:** Execute in the MAIN session, not as a subagent. Summarization is
read-then-write on local files — subagents cannot write files without explicit Write
permission grants. Subagents are for research (external I/O); summarization is for the
main thread.

## Summarize all business context

Triggers: "summarize business", "refresh business summary", "update business context".

1. Read every `context/business/[domain]/summary.md` that exists
2. Write `context/business/summary.md` using this schema:
   - Header with last-updated date and staleness table (one row per domain)
   - One 2-3 sentence paragraph per domain
   - **"Overall Strategic Read"** section: 4-6 sentences on what this means for LinkedIn's
     actual situation right now — opinionated, not corporate
   - **"Implications for Licensing BD"** section: 4-6 bullets of cross-domain insights that
     only emerge from reading all domains together
3. Append to `manifest.md`

Only summarize domains that have a populated `summary.md` — skip and note empty ones.
This is the top-level orientation artifact read during every session start.

**IMPORTANT:** Execute in the MAIN session (same reason as above).

**On new business context doc added** — append to `manifest.md`; note that `[domain]/summary.md`
is now stale. Do NOT auto-summarize.
