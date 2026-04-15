# prof-cert-report

Generates LinkedIn Learning professional certificate funnel reports for BD partner reporting.
Pulls from `hive.u_llsdsgroup.profcerts_status_agg` (Marrion-Yna Macandog's dataset).

## Prerequisites

- `uv` installed: https://docs.astral.sh/uv/getting-started/installation/
- VPN connected (required to reach trino-holdem.prod.linkedin.com)
- First run opens a browser tab for LNKDPROD SSO login — token is cached after that

## Invocation

```bash
# List available certifier names (find the exact string for a partner)
uv run --directory ~/.claude/skills/prof-cert-report python scripts/report.py --list

# Report for a specific partner
uv run --directory ~/.claude/skills/prof-cert-report python scripts/report.py --certifier "American Marketing Association"

# Report for all partners
uv run --directory ~/.claude/skills/prof-cert-report python scripts/report.py --all
```

## Output

Markdown table matching Manish's Twilio Performance Tracker format:

| Metric | Definition |
|---|---|
| UU Content Starts (A) | Learners whose status is not COMPLETED (in-progress) |
| UU Content Completes (B) | Learners whose status = COMPLETED |
| UU Assessment Completes (C) | Learners who completed the exam |
| Earned Certs (D) | Learners who earned the certificate |
| Added to Profile (E) | Learners who added cert to LinkedIn profile |
| Completion Rate (B/A) | Content completion rate |
| Assessment Pass Rate (C/B) | Of completers, fraction who passed assessment |
| Start→Cert Rate (D/A) | End-to-end funnel rate |
| Add to Profile Rate (E/D) | Of cert earners, fraction who posted to profile |

## Data notes

- **1-year lookback only**: `profcerts_status_agg` covers the trailing 12 months from refresh date.
  Manish's cumulative report covers all time from launch — numbers will differ for older certs.
- **AMA gap explained**: The publicly visible learner count on the prof cert LP page counts
  anyone who viewed/enrolled in the LP (including pre-content-start). "UU Content Starts"
  only counts learners who actually began content. The gap = enrolled-but-not-started.
- **Source table**: `hive.u_llsdsgroup.profcerts_status_agg` — built by Marrion-Yna Macandog
  (CIA DS team), LILA-12224. Weekly variant: `profcerts_status_week_agg`.

## Scheduling

To run monthly via Claude Code cron (first of each month):

```
/cron 0 9 1 * * uv run --directory ~/.claude/skills/prof-cert-report python scripts/report.py --certifier "American Marketing Association"
```
