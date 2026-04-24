# Rolodex Enrichment

Enriches a bulk LinkedIn contact list (from Sales Navigator CSV export or similar) with
structured `company` data by fetching each profile's HTML through the authenticated
LinkedIn browser session. Validated 2026-04-23 against 11,506 contacts — 92% overall
hit rate (96% on the second pass after tuning parameters).

---

## When to use

When you have a CSV of LinkedIn contacts with profile URLs but no company field, or a
stale/incomplete company column. Input: `ed_rolodex_raw.csv`. Output:
`ed_rolodex_enriched.csv` (adds `company`, `school`, `method` columns).

---

## Script

**`~/licensing/scripts/run_enrichment.py`** — the canonical enrichment runner. Self-contained.

Key parameters (module-level constants at top of file):

| Constant | Value | Notes |
|---|---|---|
| `CONCURRENCY` | 5 | Proven safe — no 429s at this level |
| `DELAY_MS` | 600 | ms between concurrent rounds (passed into browser JS) |
| `INTER_BATCH_DELAY` | 8 | seconds between 500-profile batches |

**Do not increase CONCURRENCY beyond 5.** At 15, LinkedIn rate-limits within 30 requests.

---

## How it works

The script launches a headless Playwright browser, restores the LinkedIn session via
exported cookies, navigates to the feed, then runs the extraction in 500-profile batches.
Each batch builds a JS IIFE with the profiles embedded, calls `page.evaluate()` with a
5-minute timeout, and saves results to `enrich_part_NNN.json`.

Company extraction uses two methods in order:
1. **`dot`** — looks for `Name · Company` pattern in the profile HTML (high confidence)
2. **`allps`** — scans `<p>` tags after the name paragraph, skipping location/boilerplate

Existing part files are skipped (idempotent — safe to re-run after partial completion).

---

## Cookies

Cookies expire. Before running, verify the session is still valid:

```bash
# Check the MCP browser session (if active)
# browser_evaluate: fetch('/in/me/', {credentials:'include'}).then(r=>r.status)
# Should return 200
```

To refresh cookies: open the Playwright MCP browser, navigate to LinkedIn, then export
via `browser_run_code`:
```javascript
async (page) => {
  const cookies = await page.context().cookies(['https://www.linkedin.com']);
  return { cookies };
}
```

Paste the result into `run_enrichment.py` replacing the `cookies_raw` list in `main()`,
and save to `/tmp/li_cookies.json`.

---

## Running

```bash
# Full run (all remaining profiles, ~1 hour for 6,800 profiles)
uv run --with playwright python3 -u ~/licensing/scripts/run_enrichment.py > /tmp/enrichment_log.txt 2>&1 &

# Monitor
tail -f /tmp/enrichment_log.txt

# Check part count
ls ~/licensing/scripts/enrich_part_*.json | wc -l
```

The script prints per-batch stats: profile count, hit rate, elapsed seconds, method breakdown.
If the sample profile check returns 429, it auto-waits 12 minutes then re-checks.

---

## Input files

| File | Description |
|---|---|
| `scripts/ed_rolodex_raw.csv` | Source — name, headline, profile_url, source, interaction_type |
| `scripts/enrich_remaining.json` | Profiles not yet enriched (url, name, headline) |
| `scripts/enrich_part_001.json` … `enrich_part_NNN.json` | Completed batches |

---

## Merge into final CSV

Run after all parts are written:

```python
import json, glob, csv

all_results = []
for f in sorted(glob.glob('/Users/bianders/licensing/scripts/enrich_part_0*.json')):
    all_results.extend(json.load(open(f)))

raw = {}
with open('/Users/bianders/licensing/scripts/ed_rolodex_raw.csv') as f:
    for row in csv.DictReader(f):
        url_key = row['profile_url'].replace('https://www.linkedin.com','').rstrip('/') + '/'
        raw[url_key] = row

with open('/Users/bianders/licensing/scripts/ed_rolodex_enriched.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['name','company','school','headline','profile_url','source','interaction_type','method'])
    writer.writeheader()
    for r in all_results:
        orig = raw.get(r['url'], {})
        writer.writerow({
            'name': r['name'],
            'company': r.get('company') or '',
            'school': r.get('school') or '',
            'headline': r.get('headline',''),
            'profile_url': 'https://www.linkedin.com' + r['url'].rstrip('/'),
            'source': orig.get('source',''),
            'interaction_type': orig.get('interaction_type',''),
            'method': r.get('method','')
        })
print(f'Wrote {len(all_results)} rows')
```

---

## Known constraints

- **MCP sandbox** — `browser_run_code` has no `require`/`import` in its sandbox and CSP
  blocks `page.addScriptTag` on LinkedIn. The Python Playwright approach is the only working
  path for disk writes.
- **Cookies** — the `li_at` session token drives auth; refresh if you get 401/redirect to login.
- **Rate limiting** — 429s clear within ~12 minutes. The script auto-waits on detection.
- **Profile data is browser-fetched HTML** — not the rendered DOM. Works for LinkedIn's
  SSR pages; won't catch data loaded via XHR after page load.
- **`enrich_remaining.json`** — generated once from the diff of all profiles vs. completed parts.
  If you add new contacts to the raw CSV, regenerate it via set subtraction on profile URLs.
