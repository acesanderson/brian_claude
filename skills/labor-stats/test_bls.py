#!/usr/bin/env python3
"""Smoke test for BLS Public Data API.

Fetches CES0000000001 (total nonfarm payroll employment) for the past 3 years.
Run before implementing the skill to confirm the API is reachable and the
response structure matches expectations.

Usage:
    python3 test_bls.py
    BLS_API_KEY=<key> python3 test_bls.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date

import urllib.request
import urllib.error

SERIES_ID = "CES0000000001"  # Total nonfarm payroll employment (seasonally adjusted)
ENDPOINT_V2 = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
ENDPOINT_V1 = "https://api.bls.gov/publicAPI/v1/timeseries/data/"

END_YEAR = date.today().year
START_YEAR = END_YEAR - 3


def fetch(api_key: str | None) -> dict:
    endpoint = ENDPOINT_V2 if api_key else ENDPOINT_V1
    payload: dict = {
        "seriesid": [SERIES_ID],
        "startyear": str(START_YEAR),
        "endyear": str(END_YEAR),
    }
    if api_key:
        payload["registrationkey"] = api_key
        payload["catalog"] = True
        payload["calculations"] = True

    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    version = "v2" if api_key else "v1"
    print(f"Using API {version}: {endpoint}")
    print(f"Request payload: {json.dumps(payload, indent=2)}\n")

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def validate(response: dict) -> None:
    assert response.get("status") == "REQUEST_SUCCEEDED", (
        f"Unexpected status: {response.get('status')}\n"
        f"Messages: {response.get('message')}"
    )

    series_list = response["Results"]["series"]
    assert series_list, "No series in response"

    series = series_list[0]
    assert series["seriesID"] == SERIES_ID, f"Unexpected seriesID: {series['seriesID']}"

    data = series["data"]
    assert data, "No data points returned"

    # Check structure of first data point
    point = data[0]
    required_keys = {"year", "period", "periodName", "value", "footnotes"}
    missing = required_keys - point.keys()
    assert not missing, f"Data point missing keys: {missing}"

    print(f"Received {len(data)} data points.")
    print(f"Latest: {point['year']} {point['periodName']} -> {point['value']} (thousands)")


def main() -> None:
    api_key = os.environ.get("BLS_API_KEY")
    if not api_key:
        print("BLS_API_KEY not set — using v1 (25 queries/day, no calculations).\n")

    try:
        response = fetch(api_key)
    except urllib.error.HTTPError as exc:
        print(f"HTTP error {exc.code}: {exc.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Network error: {exc.reason}", file=sys.stderr)
        sys.exit(1)

    print("=== Raw JSON response ===")
    print(json.dumps(response, indent=2))
    print("=========================\n")

    try:
        validate(response)
        print("\nAll assertions passed. API is working correctly.")
    except AssertionError as exc:
        print(f"\nValidation failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
