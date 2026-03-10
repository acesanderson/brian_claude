# Email Finder Skill — Design

**Date:** 2026-03-09

## Purpose

Given a person's full name and company, generate ranked candidate email addresses. Optionally verify against Hunter.io only when explicitly requested by the user.

## Architecture

Hybrid: Python script handles deterministic work (permutations, Brave API calls, Hunter.io calls). LLM orchestrates, interprets results, and ranks candidates with reasoning.

## Interface

- **Single:** `find email for <Full Name> at <Company>`
- **Batch:** `find emails for: [list of name/company pairs]`
- **Verify (explicit only):** `verify with hunter` — triggers Hunter.io domain search

Hunter.io is NEVER called automatically. It must be explicitly requested by the user after candidates are shown.

## Script (`scripts/find_email.py`)

Responsibilities:
- Accept `--name`, `--company`, `--domain` (optional), `--verify` (only when user explicitly requests)
- Discover company domain via Brave search if not provided
- Search Brave for email pattern evidence (`"@domain.com"` in press releases, contact pages, team pages)
- Generate all standard permutations against the domain
- Return structured JSON: `{domain, detected_pattern, candidates: [{email, confidence_tier}]}`
- `--verify` calls Hunter.io domain search API and appends results

## Permutation Formats

Standard formats generated for `John Smith` @ `company.com`:
- john.smith, jsmith, john, johns, j.smith, johnsmith, smithjohn, smith.john, smithj

## Confidence Tiers

1. **high** — format matches pattern detected from web evidence
2. **medium** — common formats (first.last, flast, f.last)
3. **low** — less common formats

## LLM Role (SKILL.md)

- Run script per person (loop for batch)
- Interpret JSON output
- Reason about pattern confidence from web evidence
- Present ranked candidates with brief explanation
- For verify: highlight Hunter.io match against candidate list

## Environment Variables

- `BRAVE_API_KEY` — required
- `HUNTER_API_KEY` — optional, only needed if user requests verification

## Dependencies

- `httpx` (Brave + Hunter API calls)
- Python 3.11+, invoked via `uv run`
