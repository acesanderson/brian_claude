from __future__ import annotations

import os
os.environ.setdefault("PYTHON_KEYRING_BACKEND", "keyrings.alt.file.PlaintextKeyring")

import argparse
import sys
from datetime import date

import trino
from trino.auth import OAuth2Authentication


# ── Trino connection ──────────────────────────────────────────────────────────

def get_conn() -> trino.dbapi.Connection:
    return trino.dbapi.connect(
        host=os.environ.get("TRINO_HOST", "trino-holdem.prod.linkedin.com"),
        port=443,
        user=os.environ.get("TRINO_USER", os.environ.get("USER", "")),
        catalog="hive",
        http_scheme="https",
        auth=OAuth2Authentication(),
    )


# ── Queries ───────────────────────────────────────────────────────────────────

FUNNEL_SQL = """
SELECT
    certifier_name,
    content_title,
    MAX(date) AS data_as_of,
    SUM(CASE WHEN status_type != 'COMPLETED' THEN n_learners END) AS uu_content_starts,
    SUM(CASE WHEN status_type = 'COMPLETED'  THEN n_learners END) AS uu_content_completes,
    SUM(CASE WHEN is_assessment_completed = 'completed' THEN n_learners END) AS uu_assessment_completes,
    SUM(CASE WHEN is_cert_earned = 'completed' THEN n_learners END) AS earned_certs,
    SUM(CASE WHEN is_added_profile = 'added'   THEN n_learners END) AS certs_added_to_profile
FROM hive.u_llsdsgroup.profcerts_status_agg
{where}
GROUP BY 1, 2
ORDER BY 1, 2
"""

LIST_SQL = """
SELECT DISTINCT certifier_name
FROM hive.u_llsdsgroup.profcerts_status_agg
ORDER BY 1
"""


def run_query(cur: trino.dbapi.Cursor, sql: str) -> list[dict]:
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


# ── Formatting ────────────────────────────────────────────────────────────────

def pct(num, denom) -> str:
    if not num or not denom:
        return "n/a"
    return f"{num / denom:.1%}"


def fmt_int(v) -> str:
    if v is None:
        return "—"
    return f"{int(v):,}"


def render_report(rows: list[dict], certifier: str | None) -> str:
    if not rows:
        return "No data found."

    lines: list[str] = []
    title = f"Prof Cert Funnel — {certifier}" if certifier else "Prof Cert Funnel — All Partners"
    lines.append(title)
    lines.append(f"Report date: {date.today().isoformat()}  |  Data window: 1-year lookback from table refresh")
    lines.append("")

    # Group by certifier for multi-partner runs
    by_certifier: dict[str, list[dict]] = {}
    for row in rows:
        by_certifier.setdefault(row["certifier_name"], []).append(row)

    for cert_name, cert_rows in by_certifier.items():
        if len(by_certifier) > 1:
            lines.append(f"## {cert_name}")
            lines.append("")

        data_as_of = cert_rows[0].get("data_as_of", "unknown")
        lines.append(f"_Data as of: {data_as_of}_")
        lines.append("")

        # Header (matching Manish's column order)
        header = [
            "Cert Name",
            "UU Content Starts (A)",
            "UU Content Completes (B)",
            "UU Assessment Completes (C)",
            "Earned Certs (D)",
            "Added to Profile (E)",
            "Completion Rate (B/A)",
            "Assessment Pass Rate (C/B)",
            "Start→Cert Rate (D/A)",
            "Add to Profile Rate (E/D)",
        ]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---"] * len(header)) + "|")

        for r in cert_rows:
            a = r["uu_content_starts"]
            b = r["uu_content_completes"]
            c = r["uu_assessment_completes"]
            d = r["earned_certs"]
            e = r["certs_added_to_profile"]
            row_cells = [
                r["content_title"],
                fmt_int(a),
                fmt_int(b),
                fmt_int(c),
                fmt_int(d),
                fmt_int(e),
                pct(b, a),
                pct(c, b),
                pct(d, a),
                pct(e, d),
            ]
            lines.append("| " + " | ".join(row_cells) + " |")

        lines.append("")

    lines.append("---")
    lines.append("Notes:")
    lines.append("  1. LOOKBACK WINDOW: profcerts_status_agg has a 1-year lookback from the refresh date.")
    lines.append("     Certs launched >12 months ago will show significantly lower counts than all-time LP page")
    lines.append("     figures or Manish's Clippy-based tracker (go/profcertsfunnel), which are cumulative since launch.")
    lines.append("     Example: Twilio all-time UU Content Starts = 4,350 (3/1/2026); 1-year new starters = ~634.")
    lines.append("  2. LP PAGE LEARNER COUNT: The publicly visible learner count on a prof cert LP page is an")
    lines.append("     LP-level metric (anyone who enrolled in the LP), not a course-level metric. 'UU Content")
    lines.append("     Starts' here requires actually playing a course video. LP starters who never opened a course")
    lines.append("     are visible on the page but absent from this report.")
    lines.append("  3. ASSESSMENT PASS RATE: Defined here as C/B (assessment completes / content completes),")
    lines.append("     matching the partner-facing monthly report template. The go/profcertsfunnel summary tab")
    lines.append("     uses D/C (earned certs / assessment completes) — a different metric.")
    lines.append("")
    lines.append("Source: hive.u_llsdsgroup.profcerts_status_agg (1-year lookback from refresh date)")

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Prof cert funnel report")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--certifier", metavar="NAME",
                       help="Certifier name to filter (e.g. 'American Marketing Association')")
    group.add_argument("--all", action="store_true",
                       help="Report on all certifiers")
    group.add_argument("--list", action="store_true",
                       help="List available certifier names and exit")
    args = parser.parse_args()

    conn = get_conn()
    cur = conn.cursor()

    try:
        if args.list:
            rows = run_query(cur, LIST_SQL)
            print("Available certifiers:")
            for r in rows:
                print(f"  {r['certifier_name']}")
            return

        if args.certifier:
            where = f"WHERE certifier_name = '{args.certifier}'"
        else:
            where = ""

        rows = run_query(cur, FUNNEL_SQL.format(where=where))
        print(render_report(rows, args.certifier if args.certifier else None))

    finally:
        conn.close()


if __name__ == "__main__":
    main()
