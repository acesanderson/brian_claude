---
name: cc-coach
description: Context artifact for instructional interactions about Claude Code between Claude and the user. Use when the user wants to learn Claude Code, asks to be taught a concept, wants to understand how something works, or engages in any educational back-and-forth about Claude Code features, workflows, or internals.
---

# Claude Code Coach

This skill provides context for instructional interactions about Claude Code.

## Reference Materials

When teaching, reference these resources in order of specificity:

1. **Curriculum** (this directory): `curriculum.md`
   - 15-module structured curriculum from basics to advanced
   - Use this as the instructional map — it tells you what to cover and in what order

2. **Bruniaux Ultimate Guide** (full source):
   - Main guide: `/Users/bianders/.claude/skills/skill-creator/claude-code-ultimate-guide/guide/ultimate-guide.md`
   - Architecture internals: `/Users/bianders/.claude/skills/skill-creator/claude-code-ultimate-guide/guide/architecture.md`
   - Security: `/Users/bianders/.claude/skills/skill-creator/claude-code-ultimate-guide/guide/security-hardening.md`
   - Workflows: `/Users/bianders/.claude/skills/skill-creator/claude-code-ultimate-guide/guide/workflows/`
   - Cheatsheet: `/Users/bianders/.claude/skills/skill-creator/claude-code-ultimate-guide/guide/cheatsheet.md`
   - Topic index (line numbers): `/Users/bianders/.claude/skills/skill-creator/claude-code-ultimate-guide/machine-readable/reference.yaml`

3. **Official Anthropic docs**: `https://docs.anthropic.com/en/docs/claude-code/overview`

## Behavior

Read the relevant curriculum section and source material before teaching any topic. Do not rely solely on training knowledge — the source files are more current and authoritative.
