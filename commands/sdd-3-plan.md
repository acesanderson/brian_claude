---
allowed-tools: Bash(~/.claude/sdd-state.sh)
---
!`~/.claude/sdd-state.sh sdd-3-plan`

Invoke the `superpowers:writing-plans` skill with these constraints:

- Every TDD step must explicitly reference which Acceptance Criterion from the design doc it fulfills (e.g. "AC-3: rate limit returns 429")
- Do not group multiple acceptance criteria into a single TDD step
- Each step follows Red-Green-Refactor: write failing test → verify it fails → implement → verify it passes → commit
- Do not add implementation steps that have no corresponding acceptance criterion

If I specified a subset of criteria to cover, scope the plan to those only.
