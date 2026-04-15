---
name: morgan
description: Personal finance assistant for the morgan-project. Use when the user wants to update financial data, run a snapshot, discuss retirement assumptions, or analyze purchases. Invocable by user only.
---

# Morgan — Personal Finance Assistant

## Project location
`$BC/morgan-project` (`/Users/bianders/Brian_Code/morgan-project`)

## What morgan does
- **Purchase impact analysis**: `morgan <amount>` — shows time cost, opportunity cost, retirement delay, and lifestyle context for a given purchase
- **Financial snapshot**: `morgan` (no args) — shows current FIRE status, target portfolio, projection with current plan
- **Verbose mode**: add `-v` for explanations of each metric

## Key assumptions (see `~/wellville/finances/finances.yaml`)
- Withdrawal rate: **3.25%** — conservative for a 35-40 year retirement horizon (retiring at 50)
- Return rate: **7% nominal / 4% real** (3% inflation subtracted)
- Projections are in **today's dollars** (real returns)
- Retirement expenses: **$55,200/yr** = $42k base + $13,200 ACA premiums (pre-Medicare until 65)
- Target portfolio is **derived** from retirement expenses / withdrawal rate (~$1.70M)

## Update process
Run periodically (quarterly or after major market moves). Requires downloading:

| Source | File | How |
|---|---|---|
| Fidelity | `Portfolio_Positions_<date>.csv` | Portfolio > Positions > Download CSV |
| Vanguard | `Holdings _ Vanguard.pdf` | Portfolio > Holdings > Print/Save PDF |
| Ally | `Snapshot _ Ally.pdf` | Dashboard > Print/Save PDF |
| Paycheck | `Payslip_<date>.pdf` | Workday > Pay > latest payslip |
| I Bonds | manual entry | Check balance at treasurydirect.gov |

See `NOTES_FOR_UPDATING.md` in project root for full field mapping.

After downloading, tell Claude Code: "update morgan from downloads" — it will extract values, propose changes to `finances.yaml`, and insert a new snapshot into postgres.

## Postgres snapshots
Historical data lives in the `morgan` database on Caruana (requires WireGuard VPN).

Schema: `snapshots` → `holdings` + `income_snapshots`

Each snapshot can include:
- **notes**: source files used, any caveats about the data
- **outlook**: qualitative take on economic/career context at the time — market conditions, career risk, evolving retirement views. Optional but encouraged. This is your longitudinal record of how your thinking evolved.

To run the seed script (first time or after wiping):
```bash
cd ~/Brian_Code/morgan-project
uv run scripts/seed.py
```

To apply new migrations:
```bash
psql -d morgan -f migrations/002_add_outlook_to_snapshots.sql
```

## What NOT to include in assets
- Ally checking/savings (liquid cash, not investment assets)
- Home equity (inflates spendable retirement cash estimates)
- ESPP shares (immediately sold; proceeds land in Ally checking)

## Open TODOs
See `TODO.md` in project root. Key item: add expense tracking via credit card statement CSV exports.
