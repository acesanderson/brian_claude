#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
# ]
# ///
"""O*NET Web Services CLI — search occupations and analyze competencies.

Commands:
    search <keyword>         Search occupations, return SOC codes + titles
    breakdown <soc_code>     Skills, knowledge, abilities, tech tools (JSON)
    gap-analysis <soc_code>  Course topics ranked by importance (JSON)

Auth (env vars — one pair required):
    ONET_API_KEY                     v2.0  X-API-Key header
    ONET_USERNAME + ONET_PASSWORD    v1.9  HTTP Basic Auth (legacy credentials)
"""
from __future__ import annotations

import json
import os
import sys

import requests

V2_BASE = "https://api-v2.onetcenter.org"
V1_BASE = "https://services.onetcenter.org/ws"


def build_session() -> tuple[requests.Session, str]:
    api_key = os.environ.get("ONET_API_KEY")
    username = os.environ.get("ONET_USERNAME")
    password = os.environ.get("ONET_PASSWORD")

    s = requests.Session()
    if api_key:
        s.headers["X-API-Key"] = api_key
        return s, V2_BASE
    if username and password:
        s.auth = (username, password)
        s.headers["Accept"] = "application/json"
        return s, V1_BASE
    print("Error: set ONET_API_KEY or ONET_USERNAME + ONET_PASSWORD", file=sys.stderr)
    sys.exit(1)


def _get(s: requests.Session, url: str, params: dict | None = None) -> dict:
    r = s.get(url, params=params)
    r.raise_for_status()
    return r.json()


def _importance(el: dict) -> float | None:
    """Extract 0-100 importance from v2.0 or v1.9 element."""
    if "importance" in el:
        return float(el["importance"])
    for scale in el.get("scale", []):
        if scale.get("id") == "IM":
            # v1.9: 1-5 scale -> normalize to 0-100
            return round((float(scale["value"]) - 1) / 4 * 100, 1)
    return None


def _fetch_competency(
    s: requests.Session, base: str, code: str, resource: str
) -> list[dict]:
    data = _get(s, f"{base}/online/occupations/{code}/details/{resource}", {"end": 200})
    return [
        {
            "id": el["id"],
            "name": el["name"],
            "description": el.get("description", ""),
            "importance": _importance(el),
        }
        for el in data.get("element", [])
    ]


def _fetch_tech(s: requests.Session, base: str, code: str) -> list[dict]:
    data = _get(
        s, f"{base}/online/occupations/{code}/summary/technology_skills", {"end": 200}
    )
    tools = []
    for cat in data.get("category", []):
        for ex in cat.get("example", []) + cat.get("example_more", []):
            tools.append(
                {
                    "name": ex["title"],
                    "category": cat["title"],
                    "hot_technology": ex.get("hot_technology", False),
                    "in_demand": ex.get("in_demand", False),
                }
            )
    return tools


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_search(s: requests.Session, base: str, keyword: str) -> None:
    data = _get(s, f"{base}/mnm/search", {"keyword": keyword, "end": 20})
    careers = data.get("career", [])
    out = {
        "keyword": keyword,
        "total": data.get("total", len(careers)),
        "results": [
            {"code": c["code"], "title": c["title"], "tags": c.get("tags", {})}
            for c in careers
        ],
    }
    print(json.dumps(out, indent=2))


def cmd_breakdown(s: requests.Session, base: str, code: str) -> None:
    out = {
        "code": code,
        "breakdown": {
            "knowledge": _fetch_competency(s, base, code, "knowledge"),
            "skills": _fetch_competency(s, base, code, "skills"),
            "abilities": _fetch_competency(s, base, code, "abilities"),
            "technology_skills": _fetch_tech(s, base, code),
        },
    }
    print(json.dumps(out, indent=2))


def cmd_gap_analysis(s: requests.Session, base: str, code: str) -> None:
    competencies: list[dict] = []
    for category in ("knowledge", "skills", "abilities"):
        for item in _fetch_competency(s, base, code, category):
            if item["importance"] is None:
                continue
            competencies.append({**item, "category": category})

    competencies.sort(key=lambda x: x["importance"], reverse=True)

    out = {
        "occupation_code": code,
        "course_topics": competencies,
        "technology_tools": _fetch_tech(s, base, code),
    }
    print(json.dumps(out, indent=2))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    command, arg = sys.argv[1], sys.argv[2]
    s, base = build_session()

    if command == "search":
        cmd_search(s, base, arg)
    elif command == "breakdown":
        cmd_breakdown(s, base, arg)
    elif command == "gap-analysis":
        cmd_gap_analysis(s, base, arg)
    else:
        print(f"Unknown command: {command!r}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
