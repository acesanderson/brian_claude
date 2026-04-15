# Wellville — Finances Subskill

## Project structure
```
~/wellville/finances/          ← financial facts vault
  finances.yaml                ← canonical state: income, retirement targets, account list
  todos.md                     ← quarterly update checklist + open items
  log/                         ← quarterly update notes, major financial events
  accounts/                    ← per-institution reference docs
    fidelity.md
    vanguard.md
    ally.md
    ibonds.md

~/Brian_Code/morgan-project/   ← computational engine (CLI, Postgres, ingest scripts)
```

## Current state
Read `~/wellville/finances/finances.yaml` for live numbers. Key figures as of 2026-04-10:
- Portfolio: **$1,509,600**
- Target: **$1,700,000** (retirement expenses $55,200 / SWR 3.25%)
- FIRE coverage: **0.89x**
- Years to retirement: **4** (target age 50)

## Morgan — computational engine

`$BC/morgan-project` (`/Users/bianders/Brian_Code/morgan-project`):

- **Purchase impact**: `morgan <amount>` — time cost, opportunity cost, retirement delay
- **FIRE snapshot**: `morgan` (no args) — current status, target, projection
- **Config:** `src/morgan/finances.yaml` — keep in sync with `~/wellville/finances/finances.yaml`
- **Historical data:** Postgres `morgan` database on Caruana (WireGuard VPN required)

Schema: `snapshots` → `holdings` + `income_snapshots`. Each snapshot has an optional `outlook` field for qualitative notes on market conditions and career context.

## Update process (quarterly or after major market moves)

Download these files, then say: **"update morgan from downloads"**

| Source | File | How |
|---|---|---|
| Fidelity | `Portfolio_Positions_<date>.csv` | Portfolio > Positions > Download CSV |
| Vanguard | `Holdings _ Vanguard.pdf` | Portfolio > Holdings > Print/Save PDF |
| Ally | `Snapshot _ Ally.pdf` | Dashboard > Print/Save PDF |
| Paycheck | `Payslip_<date>.pdf` | Workday > Pay > latest payslip |
| I Bonds | manual | treasurydirect.gov — current value on dashboard |

Claude will extract values, propose changes to both `finances.yaml` files, and insert a new snapshot into Postgres.

See `$BC/morgan-project/NOTES_FOR_UPDATING.md` for full field mapping.

## Key assumptions
- Withdrawal rate: **3.25%** — conservative for a 35-40 year retirement horizon
- Return rate: **7% nominal / 4% real** (3% inflation subtracted)
- Projections are in **today's dollars**
- Retirement expenses: **$55,200/yr** = $42k base + $13,200 ACA premiums (until Medicare at 65)

## What NOT to count as investment assets
- Ally checking/savings (liquid cash)
- Home equity
- ESPP shares (immediately sold; land in Ally checking)
- Kids' savings accounts (Jaime, Ingrid, Ella)

## Open TODOs
See `~/wellville/finances/todos.md`. Key open item: expense tracking via credit card CSV exports (see `$BC/morgan-project/TODO.md`).
