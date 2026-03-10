#!/usr/bin/env python3
# /// script
# dependencies = ["httpx"]
# ///
"""
Email finder script.
Usage:
  uv run --with httpx scripts/find_email.py --name "John Smith" --company "Acme"
  uv run --with httpx scripts/find_email.py --name "John Smith" --domain "acme.com"
  uv run --with httpx scripts/find_email.py --name "John Smith" --company "Acme" --verify
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass


BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")

# Each entry: (format_string, label)
PERMUTATION_FORMATS: list[tuple[str, str]] = [
    ("{first}.{last}", "first.last"),
    ("{f}{last}", "flast"),
    ("{f}.{last}", "f.last"),
    ("{first}{last}", "firstlast"),
    ("{first}", "first"),
    ("{first}{l}", "firstl"),
    ("{last}.{first}", "last.first"),
    ("{last}{first}", "lastfirst"),
    ("{last}{f}", "lastf"),
    ("{last}", "last"),
]


def generate_permutations(first: str, last: str, domain: str) -> list[dict]:
    f = first[0].lower()
    l = last[0].lower()
    first_l = first.lower()
    last_l = last.lower()

    seen: set[str] = set()
    results = []
    for fmt, label in PERMUTATION_FORMATS:
        local = fmt.format(first=first_l, last=last_l, f=f, l=l)
        email = f"{local}@{domain}"
        if email not in seen:
            seen.add(email)
            results.append({"email": email, "format": label, "confidence_tier": "low"})
    return results


def brave_search(query: str) -> list[dict]:
    if not BRAVE_API_KEY:
        return []
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": query, "count": 10}
    try:
        resp = httpx.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("web", {}).get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "description": r.get("description", ""),
                "url": r.get("url", ""),
            }
            for r in results
        ]
    except Exception as e:
        return [{"error": str(e)}]


def company_to_slug(company: str) -> str:
    """Construct a naive domain slug from a company name, e.g. 'Goldman Sachs' -> 'goldmansachs.com'."""
    tokens = re.split(r"\W+", company)
    slug = "".join(t.lower() for t in tokens if t)
    return f"{slug}.com"


def find_domain(company: str) -> str:
    """Return the company's email domain. Uses Brave to confirm; falls back to a slug guess."""
    skip = {"wikipedia", "linkedin", "facebook", "crunchbase", "bloomberg", "twitter", "glassdoor", "yelp"}
    company_tokens = [t.lower() for t in re.split(r"\W+", company) if len(t) > 2]

    results = brave_search(f"{company} official website email")
    preferred: list[str] = []

    for r in results:
        url = r.get("url", "")
        m = re.search(r"https?://(?:www\.)?([^/]+)", url)
        if not m:
            continue
        domain = m.group(1).lower()
        if any(x in domain for x in skip):
            continue
        if any(tok in domain for tok in company_tokens):
            preferred.append(domain)

    if preferred:
        return sorted(preferred, key=lambda d: (d.count("."), len(d)))[0]

    # Fallback: construct from company name
    return company_to_slug(company)


def classify_local(local: str) -> dict:
    """Return structural properties of an email local part."""
    has_dot = "." in local
    parts = local.split(".")
    return {
        "has_dot": has_dot,
        "length": len(local),
        "num_parts": len(parts),
        "part_lengths": [len(p) for p in parts],
    }


def infer_format_label(local: str) -> str | None:
    """Best-effort guess at the format label from a real email's local part structure."""
    cls = classify_local(local)
    has_dot = cls["has_dot"]
    parts = cls["part_lengths"]

    if has_dot and len(parts) == 2:
        if parts[0] == 1:
            return "f.last"
        if parts[1] == 1:
            return "last.f"  # not in our list but close to last.first
        return "first.last" if parts[0] > 1 else "last.first"
    if not has_dot:
        if cls["length"] <= 6 and cls["length"] >= 2:
            return "flast"  # short no-dot: likely initial+last
        return "firstlast"
    return None


def detect_pattern(domain: str, results: list[dict]) -> tuple[str | None, str | None]:
    """Return (example_email, inferred_format_label) from search snippets."""
    email_re = re.compile(r"[a-zA-Z0-9._%+\-]+@" + re.escape(domain))
    found: list[str] = []
    for r in results:
        text = r.get("description", "") + " " + r.get("title", "")
        found.extend(email_re.findall(text))

    if not found:
        return None, None

    example = found[0].lower()
    local = example.split("@")[0]
    fmt_label = infer_format_label(local)
    return example, fmt_label


MEDIUM_FORMATS = {"first.last", "flast", "f.last"}


def apply_confidence(
    candidates: list[dict],
    detected_format: str | None,
) -> list[dict]:
    for c in candidates:
        fmt = c["format"]
        if detected_format and fmt == detected_format:
            c["confidence_tier"] = "high"
        elif fmt in MEDIUM_FORMATS:
            c["confidence_tier"] = "medium"
        # else stays "low"
    return candidates


def hunter_domain_search(domain: str) -> dict:
    if not HUNTER_API_KEY:
        return {"error": "HUNTER_API_KEY not set"}
    url = "https://api.hunter.io/v2/domain-search"
    params = {"domain": domain, "api_key": HUNTER_API_KEY}
    try:
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        return {
            "pattern": data.get("pattern"),
            "emails": [e.get("value") for e in data.get("emails", [])[:5]],
        }
    except Exception as e:
        return {"error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate candidate email addresses for a person.")
    parser.add_argument("--name", required=True, help="Full name, e.g. 'John Smith'")
    parser.add_argument("--company", default="", help="Company name (used to discover domain)")
    parser.add_argument("--domain", default="", help="Known domain (skips discovery)")
    parser.add_argument("--verify", action="store_true", help="Call Hunter.io domain search (requires HUNTER_API_KEY)")
    args = parser.parse_args()

    parts = args.name.strip().split()
    if len(parts) < 2:
        print(json.dumps({"error": "Provide full name with at least first and last name"}))
        sys.exit(1)

    first, last = parts[0], parts[-1]

    domain = args.domain
    if not domain and args.company:
        domain = find_domain(args.company)
    if not domain:
        # Last resort: slug from company name
        domain = company_to_slug(args.company) if args.company else ""
    if not domain:
        print(json.dumps({"error": "Provide --domain or --company"}))
        sys.exit(1)

    search_results = brave_search(f'"@{domain}" email contact')
    detected_email, detected_format = detect_pattern(domain, search_results)

    candidates = generate_permutations(first, last, domain)
    candidates = apply_confidence(candidates, detected_format)

    tier_order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(key=lambda c: tier_order[c["confidence_tier"]])

    output: dict = {
        "domain": domain,
        "detected_email_evidence": detected_email,
        "detected_format": detected_format,
        "candidates": candidates,
    }

    if args.verify:
        output["hunter"] = hunter_domain_search(domain)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
