---
allowed-tools: Bash(~/.claude/sdd-state.sh)
---
!`~/.claude/sdd-state.sh sdd-2-adversarial`

Read the most recent design doc in `docs/plans/`. Critically review it on these axes:

- Where are the ambiguities? Where could two developers interpret this differently?
- What failure modes aren't covered in the interface contracts?
- What's missing from the non-goals that a subagent might fill in with a bad default?
- Are the acceptance criteria strictly testable as written, or do any rely on subjective judgment?
- Are observability requirements missing? (logs, metrics, alerts that prove the feature worked in production)
- Are any domain language synonyms unresolved? (`Account` vs `User` vs `Profile`, etc.)
- Are there invalid state transitions not yet listed?

For each gap found, propose a concrete fix. Update the design doc with your changes. Then present a summary of what changed and wait for my approval before invoking `superpowers:writing-plans`.
