---
allowed-tools: Bash(~/.claude/sdd-state.sh)
---
!`~/.claude/sdd-state.sh sdd-4-execute`

Present the two execution options, then proceed with my choice:

**Option A — Subagent-Driven (same session)**
Invoke `superpowers:subagent-driven-development`. Fresh subagent per task. After each task: spec compliance check (does the output match the AC?) + code quality review before moving to the next.

**Option B — Parallel Session**
Invoke `superpowers:executing-plans` in a new session. Batch execution with a checkpoint every 3 tasks.

If I want to execute a subset of criteria only, confirm the AC range before starting and scope execution strictly to those steps.

Enforce `superpowers:test-driven-development` (Red-Green-Refactor) for every step regardless of which option is chosen.
