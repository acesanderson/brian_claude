"""
Google Trends wrapper via pytrends.

Usage:
    uv run --with pytrends python trends.py interest "python course" "rust course" --timeframe "today 12-m"
    uv run --with pytrends python trends.py related "python course"
    uv run --with pytrends python trends.py compare "python course" "rust course" "go course"
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from pytrends.request import TrendReq


def _build(terms: list[str], timeframe: str, geo: str) -> TrendReq:
    pt = TrendReq(hl="en-US", tz=0)
    pt.build_payload(terms, timeframe=timeframe, geo=geo)
    return pt


def interest_over_time(
    terms: list[str],
    timeframe: str = "today 12-m",
    geo: str = "",
) -> dict:
    """Return weekly interest scores for 1-5 terms."""
    if not 1 <= len(terms) <= 5:
        raise ValueError("Provide between 1 and 5 terms.")

    pt = _build(terms, timeframe, geo)
    df = pt.interest_over_time()

    if df.empty:
        return {"terms": terms, "timeframe": timeframe, "geo": geo, "data": []}

    rows = []
    for ts, row in df.iterrows():
        entry: dict = {"date": ts.strftime("%Y-%m-%d")}
        for term in terms:
            entry[term] = int(row[term])
        entry["is_partial"] = bool(row.get("isPartial", False))
        rows.append(entry)

    return {"terms": terms, "timeframe": timeframe, "geo": geo, "data": rows}


def related_queries(
    term: str,
    timeframe: str = "today 12-m",
    geo: str = "",
) -> dict:
    """Return top and rising related queries for a single term."""
    pt = _build([term], timeframe, geo)
    raw = pt.related_queries()

    result: dict = {"term": term, "timeframe": timeframe, "geo": geo, "top": [], "rising": []}

    payload = raw.get(term, {})
    if payload is None:
        return result

    top_df = payload.get("top")
    if top_df is not None and not top_df.empty:
        result["top"] = top_df[["query", "value"]].to_dict(orient="records")

    rising_df = payload.get("rising")
    if rising_df is not None and not rising_df.empty:
        result["rising"] = rising_df[["query", "value"]].to_dict(orient="records")

    return result


def compare(
    terms: list[str],
    timeframe: str = "today 12-m",
    geo: str = "",
) -> dict:
    """Compare terms and show which has the most momentum (highest recent average)."""
    if not 2 <= len(terms) <= 5:
        raise ValueError("Provide between 2 and 5 terms to compare.")

    iot = interest_over_time(terms, timeframe, geo)
    rows = iot["data"]

    if not rows:
        return {**iot, "comparison": {}}

    # Drop partially-complete current week before averaging
    complete_rows = [r for r in rows if not r["is_partial"]]
    if not complete_rows:
        complete_rows = rows

    # Recent momentum: average of last 4 complete weeks
    recent = complete_rows[-4:]
    averages = {
        term: round(sum(r[term] for r in recent) / len(recent), 1)
        for term in terms
    }
    leader = max(averages, key=lambda t: averages[t])

    return {
        **iot,
        "comparison": {
            "averages_last_4_weeks": averages,
            "leader": leader,
        },
    }


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Google Trends CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # interest
    p_int = sub.add_parser("interest", help="Interest over time")
    p_int.add_argument("terms", nargs="+")
    p_int.add_argument("--timeframe", default="today 12-m")
    p_int.add_argument("--geo", default="")

    # related
    p_rel = sub.add_parser("related", help="Related queries")
    p_rel.add_argument("term")
    p_rel.add_argument("--timeframe", default="today 12-m")
    p_rel.add_argument("--geo", default="")

    # compare
    p_cmp = sub.add_parser("compare", help="Compare momentum across terms")
    p_cmp.add_argument("terms", nargs="+")
    p_cmp.add_argument("--timeframe", default="today 12-m")
    p_cmp.add_argument("--geo", default="")

    args = parser.parse_args()

    if args.command == "interest":
        result = interest_over_time(args.terms, args.timeframe, args.geo)
    elif args.command == "related":
        result = related_queries(args.term, args.timeframe, args.geo)
    elif args.command == "compare":
        result = compare(args.terms, args.timeframe, args.geo)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _cli()
