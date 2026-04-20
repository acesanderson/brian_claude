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
