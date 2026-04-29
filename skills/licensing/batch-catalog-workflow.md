# Full Batch Catalog Workflow

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

**Step 3 — Spawn workers in batches of 5**:
Spawn workers in batches of **5 at a time** — never all at once. Each worker opens a
Playwright/Chrome instance; dispatching too many simultaneously exhausts system memory.

Dispatch a batch of 5, wait for all 5 to complete, then dispatch the next 5.

Use `run_in_background=true` within each batch so the 5 run in parallel, but wait for
the batch to finish before starting the next one.

Each worker writes its output (catalog.json, catalog.xlsx, report.md) directly to
`~/licensing/partners/{slug}/`. No consolidation step needed — workers have direct
filesystem access.

**Checkpoint / resume pattern** — `catalog.json` presence is the checkpoint. At any
point (including after a context compression or session restart), reconstruct the pending
queue by scanning:
```bash
for slug in <full_partner_list>; do
  [[ ! -f ~/licensing/partners/$slug/catalog.json ]] && echo "$slug"
done
```
Dispatch the next batch of 5 from whatever remains. Completed partners are
self-evidencing — never track progress in conversation context.

**Write permission fallback:** Workers frequently hit Write permission walls and cannot
create files. When a worker returns structured catalog data in its result output instead
of writing a file, write `catalog.json` in the main session using that data. Do not
re-dispatch the worker — the scrape is complete; only the write is blocked. Check which
slugs have files after all workers complete:
```bash
for d in ~/licensing/partners/*/; do
  [[ -f "$d/catalog.json" ]] || echo "$(basename $d)"
done
```

**JS-rendered sites:** Some catalogs (e.g. New Relic, Oracle MyLearn) are JS-rendered
SPAs — static fetch returns no course titles, only page shell. Signal: worker reports
a course *count* but no *titles*, or notes the page is a SPA/requires JS. Fix: dispatch
a follow-up worker with explicit Playwright instructions (use `browser_navigate` +
`browser_evaluate` or `browser_snapshot` to render the catalog). Flag these in the
initial dispatch summary so the follow-up is easy to queue.
