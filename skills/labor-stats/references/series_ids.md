# BLS Series ID Reference — Education & Workforce Analysis

## Table of Contents
1. [Series ID anatomy](#series-id-anatomy)
2. [OEWS — Occupational wages & employment](#oews)
3. [Employment Projections (EP)](#employment-projections)
4. [CES — Payroll employment by sector](#ces)
5. [CPS — Education & earnings](#cps)
6. [Verified spot-check series](#verified-spot-check-series)

---

## Series ID anatomy

| Survey | Prefix | Format | Notes |
|---|---|---|---|
| Occupational Employment & Wage Statistics | OE | `OE{S}{AT}{AREA7}{IND6}{OCC6}{DT2}` | S=seasonal(U), AT=areatype |
| Employment Projections | EP | `EPU{OCC6}{IND6}` | Annual; not all SOC codes covered |
| Current Employment Statistics (payroll) | CE / CES | `CES{SUPERIND6}{DT2}` | Monthly seasonally adj. |
| Current Population Survey | LN | `LN{S}{DT6}` | Household survey |
| Local Area Unemployment Statistics | LA | `LA{S}CN{FIPS11}00{MT}` | State/county unemployment |

---

## OEWS

**Survey:** Occupational Employment and Wage Statistics
**Frequency:** Annual (released each April for prior-year survey)
**Series length:** ~3 years usable via v1 API; up to 20 via v2

### Series ID format
```
OE  U  N  0000000  000000  151252  04
^   ^  ^  ^        ^       ^       ^
|   |  |  |        |       |       datatype (2 chars)
|   |  |  |        |       occupation SOC (6 chars, no hyphen)
|   |  |  |        industry NAICS (6 chars, "000000" = all)
|   |  |  area code (7 chars, "0000000" = national)
|   |  areatype: N=national S=state M=metro B=non-metro
|   seasonal: always U (no seasonal adjustment for OEWS)
survey prefix
```

### OEWS datatype codes

| Code | Name | Unit |
|---|---|---|
| 01 | Employment | thousands |
| 03 | Mean hourly wage | USD |
| 04 | Mean annual wage | USD |
| 08 | Median hourly wage | USD |
| 11 | Annual 10th percentile | USD |
| 12 | Annual 25th percentile | USD |
| 13 | Median annual wage | USD |
| 14 | Annual 75th percentile | USD |
| 15 | Annual 90th percentile | USD |

### OEWS areatype codes

| Code | Meaning |
|---|---|
| N | National |
| S | State |
| M | Metropolitan Statistical Area |
| B | Non-metropolitan area |

### High-value occupation codes for workforce/L&D analysis

| SOC Code | Occupation |
|---|---|
| 000000 | All occupations (aggregate) |
| 110000 | Management (all) |
| 130000 | Business & financial operations (all) |
| 150000 | Computer & mathematical (all) |
| 151221 | Computer & information systems managers |
| 151251 | Computer programmers |
| 151252 | Software developers |
| 151254 | Web developers |
| 151255 | Web & digital interface designers |
| 151256 | Software quality assurance analysts |
| 151261 | Computer systems analysts |
| 151299 | Computer occupations, all other |
| 151311 | Computer network architects |
| 151321 | Data scientists |
| 151322 | Computer network support specialists |
| 152011 | Actuaries |
| 152031 | Operations research analysts |
| 152051 | Data scientists (alternate SOC mapping) |
| 172061 | Computer hardware engineers |
| 193011 | Economists |
| 251000 | Postsecondary teachers (all) |
| 251199 | Postsecondary teachers, all other |
| 432011 | Switchboard operators |
| 531011 | Aircraft pilots and flight engineers |

> **Tip:** Use `bls.py wages 000000` for aggregate national figures, then drill into a specific SOC.

### Building a national wage series ID

```python
from scripts.bls import oews_series_id

# National mean annual wage for software developers
sid = oews_series_id("151252", datatype="mean_annual_wage")
# -> "OEUN000000000000151252004"  (area_type=N, area=0000000, industry=000000)
```

To verify a constructed ID, run:
```bash
python3 scripts/bls.py series OEUN000000000000151252004
```

---

## Employment Projections

**Survey:** Employment Projections (EP)
**Frequency:** Annual snapshot; 10-year outlook. Released each September.
**Coverage:** National only. Not all SOC codes have EP series.

### Series ID format
```
EP  U  151252  000000
^   ^  ^       ^
|   |  |       industry (6 chars; "000000" = all industries)
|   |  SOC occupation code (6 chars, no hyphen)
|   seasonal: always U
survey prefix
```

Example: `EPU151252000000` — Software developer projections, all industries.

### Caveats
- EP data is a projection snapshot, not a monthly time series. The "year" field reflects the base and target years.
- Not all SOC codes have series. If `bls.py projections <occ_code>` returns empty, the code is not directly covered.
- Some occupations use combined/aggregated SOC codes in EP that differ from OEWS codes.

### Growth projection occupations (high-value for L&D)

| SOC | Occupation | 10-yr outlook |
|---|---|---|
| 151252 | Software developers | Much faster than avg |
| 151321 | Data scientists | Much faster than avg |
| 113021 | Computer and IS managers | Faster than avg |
| 172061 | Computer hardware engineers | Avg |
| 292010 | Clinical laboratory technologists | Faster than avg |
| 113011 | Administrative services managers | Avg |

> Projected growth rates change with each EP release cycle. Always pull fresh data.

---

## CES

**Survey:** Current Employment Statistics (establishment survey)
**Frequency:** Monthly, seasonally adjusted
**Series ID format:** `CES{SUPERIND6}{DT2}`

### Useful CES series

| Series ID | Description |
|---|---|
| CES0000000001 | Total nonfarm payroll (SA), thousands |
| CES0500000001 | Total private employment (SA) |
| CES6000000001 | Professional and business services |
| CES6054000001 | Professional, scientific, tech services |
| CES6561000001 | Educational services (private) |
| CES7000000001 | Leisure and hospitality |

### CES datatype codes

| Code | Description |
|---|---|
| 01 | All employees (thousands, SA) |
| 06 | Average weekly hours |
| 11 | Average hourly earnings |
| 30 | Women employees (thousands) |

---

## CPS

**Survey:** Current Population Survey (household survey)
**Frequency:** Monthly
**Useful for:** Education level vs. employment/earnings, labor force participation.

### High-value CPS series for education analysis

| Series ID | Description |
|---|---|
| LNS11300000 | Labor force participation rate (16+) |
| LNS14000000 | Unemployment rate (seasonally adj.) |
| LNS14027659 | Unemployment rate — bachelor's degree+ |
| LNS14027660 | Unemployment rate — some college / assoc. |
| LNS14027689 | Unemployment rate — high school diploma only |
| LNS14027662 | Unemployment rate — less than high school |

---

## Verified spot-check series

These were confirmed working as of 2026-02:

| Series ID | Description | Last tested |
|---|---|---|
| CES0000000001 | Total nonfarm payroll | 2026-02 |
| LNS14000000 | Unemployment rate | — |

To add a verified series after testing:
```bash
python3 scripts/bls.py series <SERIES_ID> --end 2025
```
If `status` is `REQUEST_SUCCEEDED` and `data` is non-empty, it's valid.

---

## External reference files (for constructing series IDs)

BLS publishes flat lookup files for OEWS:
- Area codes: `https://download.bls.gov/pub/time.series/oe/oe.area`
- Occupation codes: `https://download.bls.gov/pub/time.series/oe/oe.occupation`
- Industry codes: `https://download.bls.gov/pub/time.series/oe/oe.industry`
- Datatype codes: `https://download.bls.gov/pub/time.series/oe/oe.datatype`
- Full series list: `https://download.bls.gov/pub/time.series/oe/oe.series`
