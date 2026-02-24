#!/usr/bin/env python3
"""
Crossref REST API client for publisher intelligence.

Usage:
    python crossref.py publisher "Elsevier"
    python crossref.py prefix 10.1016
    python crossref.py compare-publishers "Elsevier" "Springer"
    python crossref.py compare-subjects "Machine Learning" "Deep Learning"

Reads CROSSREF_EMAIL env var for polite-pool access (strongly recommended).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

BASE = "https://api.crossref.org"
DEFAULT_RECENT_YEARS = 5


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _user_agent() -> str:
    email = os.environ.get("CROSSREF_EMAIL", "")
    ua = "publisher-intel/1.0"
    if email:
        ua += f" (mailto:{email})"
    return ua


def _get(path: str, params: dict | None = None) -> dict:
    p = dict(params or {})
    email = os.environ.get("CROSSREF_EMAIL", "")
    if email:
        p.setdefault("mailto", email)
    qs = f"?{urllib.parse.urlencode(p)}" if p else ""
    url = f"{BASE}{path}{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Member / publisher lookup
# ---------------------------------------------------------------------------

def search_members(name: str, rows: int = 5) -> list[dict]:
    data = _get("/members", {"query": name, "rows": rows})
    return data.get("message", {}).get("items", [])


def member_summary(member_id: int) -> dict:
    """Return member record with counts."""
    data = _get(f"/members/{member_id}")
    return data.get("message", {})


def publisher_profile(name: str) -> dict:
    """
    Look up a publisher by name and return:
      - member candidates (first is best match)
      - total_works
      - subjects (sampled from recent works)
      - volume_by_year (past DEFAULT_RECENT_YEARS years)
    """
    candidates = search_members(name)
    if not candidates:
        return {"error": f"No Crossref member found for '{name}'"}

    member = candidates[0]
    member_id = member["id"]
    primary_name = member.get("primary-name", "?")
    prefixes = member.get("prefixes", [])

    # Total works (no rows needed, just the count)
    total_data = _get("/works", {
        "filter": f"member:{member_id}",
        "rows": 0,
    })
    total_works = total_data.get("message", {}).get("total-results", 0)

    # Publication volume by year via facet
    facet_data = _get("/works", {
        "filter": f"member:{member_id}",
        "rows": 0,
        "facet": "published:*",
    })
    facets = facet_data.get("message", {}).get("facets", {})
    year_values = facets.get("published", {}).get("values", {})
    current_year = date.today().year
    volume_by_year = {
        k: v
        for k, v in sorted(year_values.items())
        if k.isdigit() and 1900 <= int(k) <= current_year
    }

    # Subject areas: sample recent works
    sample_data = _get("/works", {
        "filter": f"member:{member_id}",
        "sort": "indexed",
        "order": "desc",
        "rows": 100,
        "select": "subject",
    })
    subject_counter: Counter = Counter()
    for item in sample_data.get("message", {}).get("items", []):
        for s in item.get("subject") or []:
            subject_counter[s] += 1
    top_subjects = [s for s, _ in subject_counter.most_common(10)]

    return {
        "member_id": member_id,
        "primary_name": primary_name,
        "prefixes": prefixes,
        "total_works": total_works,
        "top_subjects": top_subjects,
        "volume_by_year": volume_by_year,
        "other_candidates": [
            {"id": m["id"], "name": m.get("primary-name")}
            for m in candidates[1:]
        ],
    }


# ---------------------------------------------------------------------------
# DOI prefix: most-cited recent works
# ---------------------------------------------------------------------------

def prefix_top_cited(prefix: str, rows: int = 10, years_back: int = 3) -> dict:
    """
    Return the most-cited recent works for a DOI prefix.
    prefix: e.g. '10.1016' (with or without leading '10.')
    """
    prefix = prefix.strip().rstrip("/")
    from_date = (date.today() - timedelta(days=365 * years_back)).strftime("%Y-%m-%d")

    data = _get(f"/prefixes/{prefix}/works", {
        "filter": f"from-pub-date:{from_date}",
        "sort": "is-referenced-by-count",
        "order": "desc",
        "rows": rows,
        "select": "DOI,title,author,is-referenced-by-count,published,container-title,subject",
    })
    msg = data.get("message", {})
    items = msg.get("items", [])

    works = []
    for w in items:
        title = (w.get("title") or [""])[0]
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in (w.get("author") or [])[:3]
        ]
        parts = (w.get("published") or {}).get("date-parts", [[None]])
        year = parts[0][0] if parts else None
        works.append({
            "doi": w.get("DOI"),
            "title": title,
            "authors": authors,
            "year": year,
            "citations": w.get("is-referenced-by-count", 0),
            "journal": (w.get("container-title") or [""])[0],
            "subjects": w.get("subject") or [],
        })

    return {
        "prefix": prefix,
        "from_date": from_date,
        "total_in_period": msg.get("total-results", 0),
        "works": works,
    }


# ---------------------------------------------------------------------------
# Comparisons
# ---------------------------------------------------------------------------

def _member_year_volumes(member_id: int) -> dict[str, int]:
    data = _get("/works", {
        "filter": f"member:{member_id}",
        "rows": 0,
        "facet": "published:*",
    })
    values = (
        data.get("message", {})
            .get("facets", {})
            .get("published", {})
            .get("values", {})
    )
    current_year = date.today().year
    return {
        k: v
        for k, v in sorted(values.items())
        if k.isdigit() and 1900 <= int(k) <= current_year
    }


def compare_publishers(name_a: str, name_b: str) -> dict:
    """Compare total works and year-by-year volume for two publishers."""
    results = {}
    for name in (name_a, name_b):
        candidates = search_members(name)
        if not candidates:
            results[name] = {"error": f"No member found for '{name}'"}
            continue
        m = candidates[0]
        mid = m["id"]
        total_data = _get("/works", {"filter": f"member:{mid}", "rows": 0})
        total = total_data.get("message", {}).get("total-results", 0)
        volumes = _member_year_volumes(mid)
        results[name] = {
            "member_id": mid,
            "primary_name": m.get("primary-name"),
            "total_works": total,
            "volume_by_year": volumes,
        }
    return results


def compare_subjects(subject_a: str, subject_b: str, years_back: int = 5) -> dict:
    """
    Compare publication volume for two subject areas over time.
    Uses Crossref query search (no strict subject taxonomy).
    """
    from_date = (date.today() - timedelta(days=365 * years_back)).strftime("%Y-%m-%d")
    results = {}
    for subject in (subject_a, subject_b):
        data = _get("/works", {
            "query": subject,
            "filter": f"from-pub-date:{from_date},has-abstract:true",
            "rows": 0,
            "facet": "published:*",
        })
        msg = data.get("message", {})
        total = msg.get("total-results", 0)
        values = msg.get("facets", {}).get("published", {}).get("values", {})
        current_year = date.today().year
        results[subject] = {
            "total_since": total,
            "from_date": from_date,
            "volume_by_year": {
                k: v
                for k, v in sorted(values.items())
                if k.isdigit() and 1900 <= int(k) <= current_year
            },
        }
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_publisher_profile(result: dict) -> None:
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    print(f"Publisher: {result['primary_name']} (member {result['member_id']})")
    print(f"Prefixes : {', '.join(result['prefixes'][:5])}")
    print(f"Total works: {result['total_works']:,}")
    print(f"Top subjects: {', '.join(result['top_subjects'][:5]) or 'n/a'}")
    print("\nVolume by year (recent):")
    years = sorted(result["volume_by_year"].items())[-10:]
    for yr, count in years:
        bar = "#" * min(50, count // max(1, max(v for _, v in years) // 50))
        print(f"  {yr}: {count:>8,}  {bar}")
    if result["other_candidates"]:
        print("\nOther matches:")
        for c in result["other_candidates"]:
            print(f"  id={c['id']}  {c['name']}")


def _print_prefix_top_cited(result: dict) -> None:
    print(f"Prefix {result['prefix']} — works since {result['from_date']}: "
          f"{result['total_in_period']:,} total")
    print(f"\nTop {len(result['works'])} by citations:\n")
    for i, w in enumerate(result["works"], 1):
        authors_str = ", ".join(w["authors"]) or "?"
        print(f"[{i:02d}] {w['title'][:80]}")
        print(f"     cites={w['citations']}  year={w['year']}  doi={w['doi']}")
        print(f"     {w['journal']!r}  |  {authors_str}")
        if w["subjects"]:
            print(f"     subjects: {', '.join(w['subjects'][:3])}")
        print()


def _print_compare_publishers(result: dict) -> None:
    names = list(result.keys())
    for name in names:
        r = result[name]
        if "error" in r:
            print(f"{name}: {r['error']}")
            continue
        print(f"{r['primary_name']} (id={r['member_id']}): {r['total_works']:,} total works")

    print("\nYear-by-year comparison (last 10 years):")
    all_years = sorted(set(
        yr
        for r in result.values()
        if "volume_by_year" in r
        for yr in r["volume_by_year"]
    ))[-10:]
    col = 12
    header = "Year".ljust(6) + "".join(
        (result[n].get("primary_name") or n)[:col].ljust(col + 2)
        for n in names
        if "volume_by_year" in result[n]
    )
    print(header)
    print("-" * len(header))
    for yr in all_years:
        row = yr.ljust(6)
        for n in names:
            if "volume_by_year" in result[n]:
                v = result[n]["volume_by_year"].get(yr, 0)
                row += str(v).rjust(col) + "  "
        print(row)


def _print_compare_subjects(result: dict) -> None:
    for subj, r in result.items():
        print(f"'{subj}': {r['total_since']:,} works since {r['from_date']}")
    print("\nYear-by-year:")
    all_years = sorted(set(yr for r in result.values() for yr in r["volume_by_year"]))[-10:]
    col = 14
    header = "Year".ljust(6) + "".join(s[:col].ljust(col + 2) for s in result)
    print(header)
    print("-" * len(header))
    for yr in all_years:
        row = yr.ljust(6)
        for r in result.values():
            v = r["volume_by_year"].get(yr, 0)
            row += str(v).rjust(col) + "  "
        print(row)


USAGE = """Usage:
  crossref.py publisher <name>
  crossref.py prefix <doi_prefix>
  crossref.py compare-publishers <name_a> <name_b>
  crossref.py compare-subjects <subject_a> <subject_b>

Env:
  CROSSREF_EMAIL   polite-pool email (strongly recommended)
"""


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(USAGE)
        raise SystemExit(1)

    cmd = args[0]

    if cmd == "publisher" and len(args) >= 2:
        _print_publisher_profile(publisher_profile(args[1]))

    elif cmd == "prefix" and len(args) >= 2:
        _print_prefix_top_cited(prefix_top_cited(args[1]))

    elif cmd == "compare-publishers" and len(args) >= 3:
        _print_compare_publishers(compare_publishers(args[1], args[2]))

    elif cmd == "compare-subjects" and len(args) >= 3:
        _print_compare_subjects(compare_subjects(args[1], args[2]))

    else:
        print(USAGE)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
