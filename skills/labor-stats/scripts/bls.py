#!/usr/bin/env python3
"""BLS Public Data API client.

Uses API v2 when BLS_API_KEY is set, otherwise falls back to v1.

v2 benefits: 500 queries/day, 20-year windows, calculations, catalog metadata.
v1 limits: 25 queries/day, 10-year windows, no calculations.

CLI:
    python3 bls.py wages 151252              # software developer wages (national)
    python3 bls.py wages 151252 --json       # JSON output
    python3 bls.py projections 151252        # employment projections
    python3 bls.py series CES0000000001      # arbitrary series fetch
    python3 bls.py series OEU --occ 151252   # all OEWS series for an occ code
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

V2_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
V1_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"

# OEWS datatype codes (oe.datatype)
OEWS_DATATYPES: dict[str, str] = {
    "employment": "01",
    "mean_hourly_wage": "03",
    "mean_annual_wage": "04",
    "median_hourly_wage": "08",
    "median_annual_wage": "13",
    "annual_10th_pct": "11",
    "annual_25th_pct": "12",
    "annual_75th_pct": "14",
    "annual_90th_pct": "15",
}

OEWS_DATATYPE_LABELS: dict[str, str] = {
    "employment": "Employment",
    "mean_hourly_wage": "Mean hourly wage",
    "mean_annual_wage": "Mean annual wage",
    "median_hourly_wage": "Median hourly wage",
    "median_annual_wage": "Median annual wage",
    "annual_10th_pct": "Annual 10th percentile",
    "annual_25th_pct": "Annual 25th percentile",
    "annual_75th_pct": "Annual 75th percentile",
    "annual_90th_pct": "Annual 90th percentile",
}


# ---------------------------------------------------------------------------
# Series ID builders
# ---------------------------------------------------------------------------

def oews_series_id(
    occ_code: str,
    datatype: str = "mean_annual_wage",
    area_type: str = "N",
    area_code: str = "0000000",
    industry_code: str = "000000",
    seasonal: str = "U",
) -> str:
    """Build a 25-char OEWS series ID.

    Format: OE + seasonal(1) + areatype(1) + area(7) + industry(6) + occ(6) + datatype(2)

    Args:
        occ_code: 6-digit SOC code without hyphen (e.g. "151252" for software devs).
                  Use "000000" for all occupations.
        datatype: Key from OEWS_DATATYPES dict or a raw 2-digit code string.
        area_type: "N" national, "S" state, "M" metro, "B" non-metro.
        area_code: 7-char BLS area code. "0000000" = national aggregate.
        industry_code: 6-digit code. "000000" = cross-industry.
        seasonal: Always "U" — OEWS has no seasonally adjusted variant.
    """
    dt_code = OEWS_DATATYPES.get(datatype, datatype)
    return f"OE{seasonal}{area_type}{area_code}{industry_code.zfill(6)}{occ_code.zfill(6)}{dt_code}"


def ep_series_id(occ_code: str, industry_code: str = "000000") -> str:
    """Build an Employment Projections (EP) series ID.

    Format: EP + U + occ(6) + industry(6)
    Note: EP data is annual snapshot, not monthly time series. Only a subset
    of occupations have EP series. Use references/series_ids.md for verified IDs.
    """
    return f"EPU{occ_code.zfill(6)}{industry_code.zfill(6)}"


# ---------------------------------------------------------------------------
# API fetch
# ---------------------------------------------------------------------------

def fetch_series(
    series_ids: Sequence[str],
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict:
    """POST to BLS API and return the raw response dict.

    Raises urllib.error.HTTPError / URLError on network failure.
    Does NOT raise on BLS-level errors (check response['status']).
    """
    api_key = os.environ.get("BLS_API_KEY")
    url = V2_URL if api_key else V1_URL

    end = end_year or date.today().year
    # v1 max 10 years; v2 max 20 years
    default_window = 10 if not api_key else 20
    start = start_year or (end - min(3, default_window))

    payload: dict = {
        "seriesid": list(series_ids),
        "startyear": str(start),
        "endyear": str(end),
    }
    if api_key:
        payload["registrationkey"] = api_key
        payload["catalog"] = True

    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _check_response(response: dict) -> None:
    if response.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(
            f"BLS API error: {response.get('status')} — {response.get('message')}"
        )
    for msg in response.get("message", []):
        if msg:
            print(f"[WARNING] BLS: {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# High-level helpers
# ---------------------------------------------------------------------------

def get_occupation_wages(
    occ_code: str,
    area_type: str = "N",
    area_code: str = "0000000",
    industry_code: str = "000000",
    datatypes: list[str] | None = None,
) -> dict[str, list]:
    """Fetch OEWS employment + wage distribution for an occupation.

    Returns dict keyed by OEWS_DATATYPES name, each value a list of
    {year, period, periodName, value, footnotes} dicts (descending by year).
    """
    if datatypes is None:
        datatypes = list(OEWS_DATATYPES.keys())

    series_map = {
        dt: oews_series_id(occ_code, dt, area_type, area_code, industry_code)
        for dt in datatypes
    }
    response = fetch_series(list(series_map.values()))
    _check_response(response)

    id_to_name = {sid: name for name, sid in series_map.items()}
    return {
        id_to_name.get(s["seriesID"], s["seriesID"]): s["data"]
        for s in response["Results"]["series"]
    }


def get_occupation_projections(occ_code: str, industry_code: str = "000000") -> dict:
    """Fetch Employment Projections (EP) series for an occupation.

    Returns the raw series dict from the BLS response.
    Note: Not all SOC codes have EP series. Returns {} if no data found.
    """
    sid = ep_series_id(occ_code, industry_code)
    response = fetch_series([sid])
    _check_response(response)
    series = response.get("Results", {}).get("series", [])
    return series[0] if series else {}


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def _fmt_wages(data: dict[str, list]) -> None:
    emp = data.get("employment", [])
    if emp:
        latest = emp[0]
        print(f"Employment ({latest['year']}): {int(latest['value']):,}")
    print()

    for key in ("mean_annual_wage", "median_annual_wage"):
        rows = data.get(key, [])
        if rows:
            r = rows[0]
            label = OEWS_DATATYPE_LABELS[key]
            print(f"{label} ({r['year']}): ${int(r['value']):,}")

    print("\nAnnual wage distribution:")
    for key in ("annual_10th_pct", "annual_25th_pct", "annual_75th_pct", "annual_90th_pct"):
        rows = data.get(key, [])
        if rows:
            label = OEWS_DATATYPE_LABELS[key].replace("Annual ", "")
            print(f"  {label}: ${int(rows[0]['value']):,}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch BLS labor statistics (OEWS wages, employment projections, raw series)"
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="Output raw JSON"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # wages subcommand
    w = sub.add_parser("wages", help="OEWS wages + employment for an occupation")
    w.add_argument("occ_code", help="6-digit SOC code without hyphen (e.g. 151252)")
    w.add_argument("--area-type", default="N", metavar="TYPE",
                   help="N=national S=state M=metro B=non-metro (default: N)")
    w.add_argument("--area-code", default="0000000", metavar="CODE",
                   help="7-char BLS area code (default: 0000000 = national)")
    w.add_argument("--industry-code", default="000000", metavar="CODE",
                   help="6-digit industry code (default: 000000 = all industries)")
    w.add_argument("--datatypes", nargs="+", choices=list(OEWS_DATATYPES),
                   metavar="TYPE", help="Subset of datatypes to fetch")

    # projections subcommand
    p = sub.add_parser("projections", help="Employment projections (EP series)")
    p.add_argument("occ_code", help="6-digit SOC code without hyphen")
    p.add_argument("--industry-code", default="000000")

    # raw series subcommand
    s = sub.add_parser("series", help="Fetch arbitrary BLS series IDs")
    s.add_argument("series_ids", nargs="+", metavar="SERIES_ID")
    s.add_argument("--start", type=int, metavar="YEAR")
    s.add_argument("--end", type=int, metavar="YEAR")

    args = parser.parse_args(argv)
    api_key = os.environ.get("BLS_API_KEY")
    if not api_key:
        print("[INFO] BLS_API_KEY not set — using v1 (25 queries/day, no catalog).",
              file=sys.stderr)

    try:
        if args.cmd == "wages":
            data = get_occupation_wages(
                args.occ_code,
                args.area_type,
                args.area_code,
                args.industry_code,
                datatypes=args.datatypes,
            )
            if args.as_json:
                print(json.dumps(data, indent=2))
            else:
                _fmt_wages(data)

        elif args.cmd == "projections":
            data = get_occupation_projections(args.occ_code, args.industry_code)
            print(json.dumps(data, indent=2))

        elif args.cmd == "series":
            data = fetch_series(args.series_ids, args.start, args.end)
            print(json.dumps(data, indent=2))

    except urllib.error.HTTPError as exc:
        print(f"HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Network error: {exc.reason}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
