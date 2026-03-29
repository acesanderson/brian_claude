---
allowed-tools: Bash(~/.claude/sdd-state.sh)
---
!`~/.claude/sdd-state.sh sdd-1c-review`

Read the most recent design doc in `docs/plans/`. Present the following review checklist and assess each item against the doc:

- **Non-goals** — Is the section actually constraining? Does it explicitly name things a subagent might fill in with a bad default?
- **Acceptance criteria** — Would you bet money these are complete? Are they phrased as testable assertions, not prose?
- **Interface contracts** — Are types and shapes explicit? No ambiguous "object" or "string" without structure?
- **Domain language** — Are synonyms eliminated? Is every noun the implementation is allowed to use listed?
- **Invalid state transitions** — Are illegal paths listed explicitly, not just valid ones?
- **Observability** — Does each AC include log/metric emissions as testable assertions? ("Must log a warning with `user_id` when X" not "should handle X gracefully")

For each item, state whether it passes or flag the specific gap. Do not proceed to adversarial review or plan generation until I approve.
