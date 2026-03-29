---
name: skill-auditor
description: Diagnose and improve a specific skill's golden path. Use when the user asks to audit, optimize, fix, or improve a skill — "what's wrong with the conduit skill", "tighten up sec-filings", "audit brave-web-search", "the deslop skill keeps breaking". Runs a structured diagnostic and proposes concrete edits.
---

# Skill Auditor

You've been asked to assess and improve a specific skill. Run a structured diagnostic, then propose and make targeted changes.

## Step 1: Identify the skill

Extract the skill name from the user's request. If ambiguous, list matching dirs from `~/.claude/skills/` and ask.

## Step 2: Run the audit script

```bash
uv run python ~/.claude/skills/skill-auditor/scripts/audit.py --skill SKILL_NAME
```

Parse the JSON output. Note `friction_score`, `signals`, `git.friction_commits`, and `git.recent_messages`.

## Step 3: Read the skill's current SKILL.md

Read `~/.claude/skills/SKILL_NAME/SKILL.md` in full. You're looking for:
- Where the golden path is ambiguous or assumes context the user might not have
- Steps that are long, that do too much, or that are likely to fail silently
- CLI flags or options documented but probably rarely used
- Missing error handling guidance
- Whether the `## Failure handling` section exists (see `DESIGN.md` for the schema)

## Step 4: Check git history for friction patterns

```bash
git -C ~/.claude log --oneline -- skills/SKILL_NAME/ | head -15
```

Read the commit messages. "troubleshoot", "fix", "rewrite", "updated to reflect challenges" are signals. Look at what changed:

```bash
git -C ~/.claude log -p --follow -- skills/SKILL_NAME/SKILL.md | head -80
```

Diff tells you what the friction actually was, not just that there was friction.

## Step 5: Synthesize findings

Combine the three sources — script signals, SKILL.md content, git history — into a short diagnostic. Be specific:

- "The `--citations` flag is documented but was removed from conduit in March because it didn't work in headless mode. It's still in the table."
- "SKILL.md has no failure handling section. The two friction commits both involved auth failures that Claude didn't handle gracefully."
- "Line count is 697. The JSON schema section (lines 280-410) belongs in `references/` — it's never needed in full during a normal invocation."

Do not just repeat the audit script's output. Add the interpretation.

## Step 6: Propose and make changes

Present findings clearly, then ask whether to proceed with edits. Default actions by signal type:

| Signal | Default action |
|--------|---------------|
| Stale documented flags | Remove from SKILL.md |
| SKILL.md >500 lines | Extract bulk reference content to `references/` |
| No prerequisites section | Add one |
| No failure handling section | Add one using the schema in `DESIGN.md` |
| Bare `python script.py` | Replace with `uv run` pattern |
| Scripts missing `# /// script` | Add inline metadata to each script |
| Vague trigger description | Rewrite the frontmatter `description` field |

Make edits directly with the Edit tool. Don't produce a list of suggestions and stop — do the work.

## What good looks like

A clean skill after audit:
- Frontmatter description is specific enough to trigger reliably (20-60 words, covers key contexts)
- Prerequisites section covers every env var and binary the scripts need
- Failure handling section covers at least: auth failure, missing env var, silent/empty result
- No flags documented that don't actually work
- SKILL.md under 500 lines (bulk reference content in `references/`)
- Scripts either have `# /// script` metadata or are invoked via `uv run --directory`

## Reference

See `DESIGN.md` for:
- Full failure mode taxonomy (5 categories)
- Failure fixture format (`failure_modes.json`)
- Script output contract (`status: success|error|partial`, `error.type`, `error.recovery`)
