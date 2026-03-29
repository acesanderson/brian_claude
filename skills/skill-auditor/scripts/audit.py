#!/usr/bin/env python3
# /// script
# dependencies = []
# ///
"""
Skill auditor: analyze ~/.claude/skills/ for golden path friction.

Produces a JSON report ranking skills by friction signals drawn from:
  1. Git churn (commit count, troubleshooting-keyword commits)
  2. Static SKILL.md analysis (size, flag count, structural gaps)

Usage:
    uv run python scripts/audit.py [--skill SKILL_NAME] [--since YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

SKILLS_ROOT = Path.home() / ".claude" / "skills"
CLAUDE_ROOT = Path.home() / ".claude"

FRICTION_KEYWORDS = {
    "troubleshoot", "troubleshooting", "fix", "fixes", "fixed",
    "debug", "broken", "patch", "revert", "workaround", "hotfix",
    "mismatch", "failing", "failure", "broke", "broken",
}


# ---------------------------------------------------------------------------
# Git churn
# ---------------------------------------------------------------------------

def get_git_churn(since: str | None = None) -> dict[str, dict]:
    """
    Returns per-skill aggregated git churn data.

    {
      "conduit": {
        "commit_count": 5,
        "friction_commits": 2,
        "last_changed": "2026-03-05",
        "commit_messages": ["updates to conduit to reflect...", ...]
      },
      ...
    }
    """
    cmd = [
        "git", "-C", str(CLAUDE_ROOT),
        "log", "--name-only", "--format=%COMMIT%h|%ad|%s", "--date=short",
        "--", "skills/",
    ]
    if since:
        cmd += [f"--since={since}"]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {}

    churn: dict[str, dict] = defaultdict(lambda: {
        "commit_count": 0,
        "friction_commits": 0,
        "last_changed": None,
        "commit_messages": [],
        "_seen_hashes": set(),
    })

    current_commit: dict | None = None

    for line in result.stdout.splitlines():
        if line.startswith("%COMMIT"):
            parts = line[len("%COMMIT"):].split("|", 2)
            if len(parts) == 3:
                commit_hash, commit_date, message = parts
                current_commit = {"hash": commit_hash, "date": commit_date, "message": message.strip()}
        elif line.startswith("skills/") and current_commit:
            # Extract skill name from path like "skills/conduit/SKILL.md"
            parts = line.split("/")
            if len(parts) >= 2:
                skill_name = parts[1]
                entry = churn[skill_name]
                # Count each commit once per skill (multiple files in same commit = 1 commit)
                if current_commit["hash"] not in entry["_seen_hashes"]:
                    entry["_seen_hashes"].add(current_commit["hash"])
                    entry["commit_count"] += 1
                    if entry["last_changed"] is None or current_commit["date"] > entry["last_changed"]:
                        entry["last_changed"] = current_commit["date"]
                    msg_lower = current_commit["message"].lower()
                    if any(kw in msg_lower for kw in FRICTION_KEYWORDS):
                        entry["friction_commits"] += 1
                    if current_commit["message"] not in entry["commit_messages"]:
                        entry["commit_messages"].append(current_commit["message"])

    # Strip internal dedup set before returning
    clean = {}
    for skill, data in churn.items():
        d = dict(data)
        d.pop("_seen_hashes", None)
        clean[skill] = d
    return clean


# ---------------------------------------------------------------------------
# Static SKILL.md analysis
# ---------------------------------------------------------------------------

def analyze_skill(skill_dir: Path) -> dict:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return {"error": "missing SKILL.md"}

    content = skill_md.read_text()
    lines = content.splitlines()

    # Flag count: lines matching |`--foo` or | `--foo` table rows
    flag_pattern = re.compile(r"^\s*\|\s*`?--")
    flag_count = sum(1 for l in lines if flag_pattern.match(l))

    # Bare python usage (using python without uv run is a portability risk)
    has_bare_python = bool(
        re.search(r'(?<!\w)python\s+\S+\.py', content)
        and "uv run" not in content
    )

    # Check for prerequisites / env var sections
    has_prerequisites = bool(re.search(r'prerequisite|prereq|env var|required.*env|SKILL.*requires', content, re.IGNORECASE))

    # Check description pushiness (skill-creator recommends "pushy" descriptions)
    frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    description = ""
    if frontmatter_match:
        fm = frontmatter_match.group(1)
        desc_match = re.search(r'^description:\s*(.+)', fm, re.MULTILINE | re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()
    description_word_count = len(description.split())

    # Script hygiene
    scripts_dir = skill_dir / "scripts"
    scripts = list(scripts_dir.glob("*.py")) if scripts_dir.exists() else []

    # Check if scripts use inline metadata (# /// script blocks)
    scripts_missing_metadata = []
    for script in scripts:
        script_content = script.read_text()
        if "# /// script" not in script_content:
            scripts_missing_metadata.append(script.name)

    # Trigger ambiguity: description is very short (under-specified)
    trigger_vague = description_word_count < 15

    return {
        "line_count": len(lines),
        "over_500_lines": len(lines) > 500,
        "flag_count": flag_count,
        "flag_heavy": flag_count > 10,
        "has_bare_python": has_bare_python,
        "has_prerequisites": has_prerequisites,
        "description_word_count": description_word_count,
        "trigger_vague": trigger_vague,
        "script_count": len(scripts),
        "scripts_missing_metadata": scripts_missing_metadata,
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def friction_score(churn: dict, static: dict) -> int:
    score = 0
    score += churn.get("friction_commits", 0) * 4
    score += min(churn.get("commit_count", 0), 10)  # cap raw commit count contribution
    if static.get("over_500_lines"):
        score += 3
    if static.get("flag_heavy"):
        score += 2
    if static.get("has_bare_python"):
        score += 3
    if not static.get("has_prerequisites"):
        score += 1
    if static.get("trigger_vague"):
        score += 2
    if static.get("scripts_missing_metadata"):
        score += len(static["scripts_missing_metadata"]) * 2
    return score


def build_signals(static: dict) -> list[str]:
    """Human-readable friction signals for a skill."""
    signals = []
    if static.get("over_500_lines"):
        signals.append(f"SKILL.md is {static['line_count']} lines (>500 — consider progressive disclosure)")
    if static.get("flag_heavy"):
        signals.append(f"{static['flag_count']} CLI flags documented — high cognitive load, prune unused ones")
    if static.get("has_bare_python"):
        signals.append("Uses bare `python script.py` instead of `uv run` — portability risk")
    if not static.get("has_prerequisites"):
        signals.append("No prerequisites/env-var section — setup friction for new machines")
    if static.get("trigger_vague"):
        signals.append(f"Description is only {static['description_word_count']} words — may under-trigger")
    if static.get("scripts_missing_metadata"):
        signals.append(f"Scripts missing `# /// script` inline metadata: {', '.join(static['scripts_missing_metadata'])}")
    return signals


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Audit skill golden path friction")
    parser.add_argument("--skill", help="Audit only this skill (directory name)")
    parser.add_argument("--since", help="Only count git commits since YYYY-MM-DD")
    parser.add_argument("--top", type=int, default=10, help="Show top N skills by friction score")
    parser.add_argument("--min-score", type=int, default=0, help="Only show skills above this friction score")
    args = parser.parse_args()

    # Determine which skills to audit
    if args.skill:
        skill_dirs = [SKILLS_ROOT / args.skill]
    else:
        skill_dirs = [d for d in SKILLS_ROOT.iterdir() if d.is_dir() and not d.name.startswith(".")]

    git_churn = get_git_churn(since=args.since)

    results = []
    for skill_dir in skill_dirs:
        name = skill_dir.name
        churn = git_churn.get(name, {"commit_count": 0, "friction_commits": 0, "last_changed": None, "commit_messages": []})
        static = analyze_skill(skill_dir)

        if "error" in static:
            continue

        score = friction_score(churn, static)
        signals = build_signals(static)

        results.append({
            "skill": name,
            "friction_score": score,
            "signals": signals,
            "git": {
                "commit_count": churn["commit_count"],
                "friction_commits": churn["friction_commits"],
                "last_changed": churn["last_changed"],
                "recent_messages": churn["commit_messages"][:3],
            },
            "static": static,
        })

    # Sort by friction score descending
    results.sort(key=lambda r: r["friction_score"], reverse=True)

    # Apply filters
    results = [r for r in results if r["friction_score"] >= args.min_score]
    results = results[: args.top]

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
