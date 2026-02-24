---
name: bureau_of_labor_statistics_api
description: >
  Fetch U.S. labor market data from the Bureau of Labor Statistics (BLS) Public Data API.
  Use when the user asks about occupation wages, salary data, employment levels, workforce
  projections, or job growth for specific occupations or industry sectors. Covers OEWS wage
  and employment data by SOC occupation code, Employment Projections (10-year growth outlook),
  payroll employment trends by sector (CES), and education vs. earnings/unemployment (CPS).
  Triggers include "what do [occupation] earn", "salary data for [job title]", "employment
  projections for [occupation]", "how fast is [field] growing", "BLS data for [occupation]",
  "labor market stats", or any request for occupation-level wage/employment data.
---

# Labor Stats

Wraps the BLS Public Data API v2 (graceful v1 fallback). No dependencies beyond stdlib.

## Auth

Check for `BLS_API_KEY` env var before running:
- **Set**: Uses v2 (500 queries/day, 20-year window, catalog metadata)
- **Absent**: Falls back to v1 (25 queries/day, 10-year window, no catalog)

Register free at: `https://data.bls.gov/registrationEngine/`

## Workflow

1. Identify the SOC occupation code (see `references/series_ids.md`)
2. Choose the appropriate command: `wages`, `projections`, or `series`
3. Run `scripts/bls.py` and interpret the output
4. Construct additional series IDs if needed using the builders in `scripts/bls.py`

## Common tasks

### Get wages for an occupation

```bash
# National wages — software developers (SOC 15-1252)
python3 scripts/bls.py wages 151252

# JSON output
python3 scripts/bls.py wages 151252 --json

# State-level (requires state area code from oe.area)
python3 scripts/bls.py wages 151252 --area-type S --area-code 0900000

# Specific datatypes only (faster — fewer series in request)
python3 scripts/bls.py wages 151252 --datatypes mean_annual_wage median_annual_wage employment
```

### Get employment growth projections

```bash
python3 scripts/bls.py projections 151252
```

Note: EP series coverage is incomplete. If empty, the SOC code lacks a dedicated EP series — check `references/series_ids.md` for notes on combined SOC codes.

### Fetch arbitrary series

```bash
# Total nonfarm payroll (sanity check)
python3 scripts/bls.py series CES0000000001

# Multiple series in one request
python3 scripts/bls.py series CES0000000001 LNS14000000 --start 2020 --end 2025
```

## Series ID construction

Use `oews_series_id()` from `scripts/bls.py` to build OEWS series IDs programmatically:

```python
from scripts.bls import oews_series_id, ep_series_id

oews_series_id("151252", "mean_annual_wage")          # national, all industries
oews_series_id("151252", "employment", area_type="S") # state-level
ep_series_id("151252")                                 # projections
```

Format: `OE + U + areatype(1) + area(7) + industry(6) + occ(6) + datatype(2)` = 25 chars total.

## Interpreting OEWS output

- **Employment** values are in thousands (e.g., `4512` = 4,512,000 workers)
- **Wage** values are in USD (e.g., `131490` = $131,490/year)
- Data is sorted descending by year (most recent first)
- OEWS is published once per year, typically in April for the prior survey year
- `footnote code "P"` = preliminary estimate

## References

- **Series IDs, SOC codes, datatype codes**: `references/series_ids.md`
  Read this when: constructing series IDs, looking up SOC codes, or identifying which series to fetch
- **BLS flat lookup files**: Listed at the bottom of `references/series_ids.md` — use these to find area codes for state/metro queries or verify occupation codes
