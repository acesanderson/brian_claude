---
name: deslop
description: >
  Strip AI-generated writing patterns from a blog post draft. Two-step pipeline:
  Gemini judges the draft and flags AI-isms, Opus revises only the flagged items.
  Use as a finishing step after collaboratively writing a post with an LLM.
  Trigger phrases include "deslop this post", "clean up the AI-isms", "run deslop".
---

# deslop

A finishing-step tool for blog posts written collaboratively with an LLM. It runs a
two-pass pipeline: Gemini audits the draft for AI-generated writing patterns, then
Opus revises only the flagged items — nothing else.

The judge looks for: banned vocabulary (delve, leverage, robust, etc.), em-dash abuse,
formulaic sentence patterns, performative tone, and burstiness (unnaturally uniform
sentence lengths). The reviser fixes only what was flagged, matching the surrounding
register and keeping changes minimal.

---

## Prerequisites

- `uv` — [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
- `ask` in PATH — provided by conduit (already installed in this environment)

---

## Usage

**Do NOT use `uv run script.py` directly** — the inline `# /// script` block pulls the
wrong `conduit` from PyPI and crashes. Use the skill's `.venv` directly:

```bash
# Pass a file
~/.claude/skills/deslop/.venv/bin/python ~/.claude/skills/deslop/scripts/deslop.py _posts/my-post.md

# Capture output
~/.claude/skills/deslop/.venv/bin/python ~/.claude/skills/deslop/scripts/deslop.py _posts/my-post.md > cleaned.md
```

The script prints the revised post to stdout. Redirect or diff as needed.

Debug output (API payloads) goes to stdout from the conduit library — suppress with
`2>/dev/null` if needed, though in practice it only affects readability, not the
final output which appears after the last Rich panel.

---

## How it works

1. **Judge** (Gemini): reads the draft, outputs a numbered list of flagged AI-isms
   with exact quoted text, category, and a one-sentence explanation.
2. **Reviser** (Opus): receives the draft + critique, fixes only flagged items,
   returns the full revised post with no commentary.

The prompts live in `~/.claude/skills/deslop/prompts/` and are rendered with Jinja2.

---

## When to use

Run deslop as the last step before publishing, after you've finalized structure and
content. It does not rewrite, reorganize, or add content — it only strips AI tell-signs.
If you want structural changes, make those first.
