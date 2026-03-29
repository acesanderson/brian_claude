# Email Finder Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Claude skill that generates ranked candidate email addresses for a person given their name and company, with optional Hunter.io verification only on explicit user request.

**Architecture:** Hybrid — a Python script handles all deterministic work (Brave searches, permutation generation, Hunter.io calls) and returns structured JSON. Claude (via SKILL.md) orchestrates the script, interprets results, and presents ranked candidates with reasoning. Batch mode loops the script per person.

**Tech Stack:** Python 3.11+, httpx, Brave Search API, Hunter.io API (optional), uv

---

### Task 1: Scaffold the skill directory

**Files:**
- Create: `~/.claude/skills/email-finder/scripts/find_email.py` (empty)
- Create: `~/.claude/skills/email-finder/SKILL.md` (empty)

**Step 1: Create directories**

```bash
mkdir -p ~/.claude/skills/email-finder/scripts
touch ~/.claude/skills/email-finder/scripts/find_email.py
touch ~/.claude/skills/email-finder/SKILL.md
```

**Step 2: Verify structure**

```bash
ls ~/.claude/skills/email-finder/
# Expected: docs/  scripts/  SKILL.md
```

---

### Task 2: Write `find_email.py`

**Files:**
- Create: `~/.claude/skills/email-finder/scripts/find_email.py`

**Step 1: Write the script**

```python
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

PERMUTATION_FORMATS = [
    "{first}.{last}",
    "{f}{last}",
    "{first}{last}",
    "{first}",
    "{first}{l}",
    "{f}.{last}",
    "{last}.{first}",
    "{last}{first}",
    "{last}{f}",
    "{last}",
]


def generate_permutations(first: str, last: str, domain: str) -> list[dict]:
    f = first[0].lower()
    l = last[0].lower()
    first = first.lower()
    last = last.lower()

    seen = set()
    results = []
    for fmt in PERMUTATION_FORMATS:
        local = fmt.format(first=first, last=last, f=f, l=l)
        email = f"{local}@{domain}"
        if email not in seen:
            seen.add(email)
            results.append({"email": email, "format": fmt, "confidence_tier": "low"})
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
        return [{"title": r.get("title", ""), "description": r.get("description", ""), "url": r.get("url", "")} for r in results]
    except Exception as e:
        return [{"error": str(e)}]


def find_domain(company: str) -> str:
    results = brave_search(f"{company} official website")
    for r in results:
        url = r.get("url", "")
        m = re.search(r"https?://(?:www\.)?([^/]+)", url)
        if m:
            domain = m.group(1)
            # Skip generic domains
            if not any(x in domain for x in ["wikipedia", "linkedin", "facebook", "crunchbase", "bloomberg", "twitter"]):
                return domain
    return ""


def detect_pattern(domain: str, results: list[dict]) -> str | None:
    """Extract email pattern from search result snippets."""
    email_re = re.compile(r"[a-zA-Z0-9._%+\-]+@" + re.escape(domain))
    found_emails: list[str] = []
    for r in results:
        text = r.get("description", "") + " " + r.get("title", "")
        found_emails.extend(email_re.findall(text))

    if not found_emails:
        return None

    # Infer format from found emails
    pattern_counts: dict[str, int] = {}
    for email in found_emails:
        local = email.split("@")[0].lower()
        for fmt in PERMUTATION_FORMATS:
            # We can't reverse-map without a name, so just return the raw evidence
            pass

    # Return the most common local part structure as a hint
    return found_emails[0] if found_emails else None


def apply_confidence(candidates: list[dict], detected_email: str | None, domain: str) -> list[dict]:
    MEDIUM_FORMATS = {"{first}.{last}", "{f}{last}", "{f}.{last}"}
    for c in candidates:
        if detected_email:
            detected_local = detected_email.split("@")[0].lower()
            candidate_local = c["email"].split("@")[0]
            # Try to infer pattern from detected email structure
            if len(detected_local) == len(candidate_local):
                c["confidence_tier"] = "high"
                continue
        if c["format"] in MEDIUM_FORMATS:
            c["confidence_tier"] = "medium"
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--company", default="")
    parser.add_argument("--domain", default="")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    parts = args.name.strip().split()
    if len(parts) < 2:
        print(json.dumps({"error": "Provide full name (first and last)"}))
        sys.exit(1)

    first, last = parts[0], parts[-1]

    domain = args.domain
    if not domain and args.company:
        domain = find_domain(args.company)
    if not domain:
        print(json.dumps({"error": f"Could not determine domain for '{args.company}'"}))
        sys.exit(1)

    # Search for email pattern evidence
    search_results = brave_search(f'"@{domain}" email contact press release')
    detected_email = detect_pattern(domain, search_results)

    candidates = generate_permutations(first, last, domain)
    candidates = apply_confidence(candidates, detected_email, domain)

    # Sort: high > medium > low
    tier_order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(key=lambda c: tier_order[c["confidence_tier"]])

    output: dict = {
        "domain": domain,
        "detected_email_evidence": detected_email,
        "candidates": candidates,
    }

    if args.verify:
        output["hunter"] = hunter_domain_search(domain)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
```

**Step 2: Verify script is syntactically valid**

```bash
uv run --with httpx python ~/.claude/skills/email-finder/scripts/find_email.py --help
# Expected: usage message with --name, --company, --domain, --verify
```

---

### Task 3: Write `SKILL.md`

**Files:**
- Create: `~/.claude/skills/email-finder/SKILL.md`

**Step 1: Write the skill**

```markdown
---
name: email-finder
description: Find likely email addresses for a person given their full name and company. Generates permutations and uses web evidence to rank candidates. Hunter.io verification available on explicit request only.
---

## Overview

You find candidate email addresses for people using a Python script that:
1. Discovers the company domain via Brave search
2. Searches for email pattern evidence in press releases / contact pages
3. Generates all standard permutations
4. Returns ranked JSON

## Running the script

Single person:
```bash
uv run --with httpx ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "FULL_NAME" \
  --company "COMPANY_NAME"
```

With known domain (skip discovery):
```bash
uv run --with httpx ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "FULL_NAME" \
  --domain "example.com"
```

Hunter.io verify (ONLY when user explicitly asks):
```bash
uv run --with httpx ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "FULL_NAME" \
  --company "COMPANY_NAME" \
  --verify
```

## Batch mode

Loop the script for each person. Run them sequentially. Aggregate results.

## Interpreting output

- `detected_email_evidence`: a real email found in the wild for this domain — use it to reason about the company's format
- `candidates`: sorted high → medium → low confidence
- Present the top 3-5 candidates, explain confidence, note the detected pattern if found

## HARD RULE: Hunter.io

Never pass `--verify` unless the user has explicitly asked to verify with Hunter.io in this message. Do not suggest it proactively.

## Prerequisites

- `BRAVE_API_KEY` env var required
- `HUNTER_API_KEY` env var required only for `--verify`
```

---

### Task 4: Test — single person lookup

**Step 1: Run against a known public figure at a well-known company**

```bash
BRAVE_API_KEY=$BRAVE_API_KEY uv run --with httpx \
  ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "Sundar Pichai" --company "Google"
```

Expected: valid JSON with `domain` like `google.com`, `candidates` list with confidence tiers, possibly `detected_email_evidence`.

**Step 2: Confirm JSON is well-formed and candidates look correct**

```bash
BRAVE_API_KEY=$BRAVE_API_KEY uv run --with httpx \
  ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "Sundar Pichai" --domain "google.com" | python3 -m json.tool
```

Expected: clean JSON, 10 candidates, at least some marked `medium`.

---

### Task 5: Test — batch (two people)

**Step 1: Run twice and confirm both work**

```bash
BRAVE_API_KEY=$BRAVE_API_KEY uv run --with httpx \
  ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "Tim Cook" --company "Apple"

BRAVE_API_KEY=$BRAVE_API_KEY uv run --with httpx \
  ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "Satya Nadella" --company "Microsoft"
```

Expected: valid JSON for each, different domains inferred correctly.

---

### Task 6: Test — verify flag (Hunter.io)

**Step 1: Run with --verify**

```bash
BRAVE_API_KEY=$BRAVE_API_KEY HUNTER_API_KEY=$HUNTER_API_KEY \
  uv run --with httpx ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "Tim Cook" --domain "apple.com" --verify
```

Expected: JSON includes `hunter` key with `pattern` and `emails` fields.

---
