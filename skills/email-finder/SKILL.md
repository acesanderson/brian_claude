---
name: email-finder
description: Find likely email addresses for a person given their full name and company. Generates permutations and uses web evidence to rank candidates. Hunter.io verification available on explicit request only.
---

## Overview

You find candidate email addresses for people using a Python script that:
1. Discovers the company domain via Brave search (if not provided)
2. Searches for email pattern evidence in press releases / contact pages
3. Generates all standard permutations against the domain
4. Returns ranked JSON (high / medium / low confidence)

## Running the script

Single person (company name, domain auto-discovered):
```bash
uv run --with httpx ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "FULL_NAME" \
  --company "COMPANY_NAME"
```

Single person with known domain (faster, skips discovery):
```bash
uv run --with httpx ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "FULL_NAME" \
  --domain "example.com"
```

Hunter.io verify — ONLY when user explicitly requests it:
```bash
uv run --with httpx ~/.claude/skills/email-finder/scripts/find_email.py \
  --name "FULL_NAME" \
  --company "COMPANY_NAME" \
  --verify
```

## Batch mode

Loop the script for each person sequentially. Aggregate and present all results together.

## Interpreting output

- `detected_email_evidence`: a real email found in the wild for this domain — indicates the company's format
- `detected_format`: inferred format label (e.g. `first.last`, `flast`) derived from the evidence
- `candidates`: sorted high → medium → low confidence
- Present the top 3-5 candidates, explain why, and note the detected pattern if found

## HARD RULE: Hunter.io

**Never** pass `--verify` unless the user has explicitly asked to verify with Hunter.io in their current message.
Do not suggest it proactively.
Hunter.io integration requires a `HUNTER_API_KEY` — note this as a TBD for the user if they ask about it.

## Prerequisites

- `BRAVE_API_KEY` env var required for all lookups
- `HUNTER_API_KEY` env var required only for `--verify` (user must sign up at hunter.io)
