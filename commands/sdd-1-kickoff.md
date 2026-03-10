---
allowed-tools: Bash(~/.claude/sdd-state.sh)
---
!`~/.claude/sdd-state.sh sdd-1-kickoff`

Invoke the `superpowers:brainstorming` skill to design the feature I described.

When interviewing me, ask ONE question at a time. Focus on:
- Edge cases and failure modes
- Unstated constraints and what this should NOT do
- Integration boundaries with existing code

When writing the design doc (`docs/plans/YYYY-MM-DD-<topic>-design.md`), include these SDD sections:

1. Goal (2-3 sentences max)
2. Constraints and non-goals (exhaustive — if not in scope, say so explicitly)
3. Interface contracts (exact function signatures, data shapes, API boundaries)
4. Acceptance criteria (phrased as testable assertions)
5. Error handling / failure modes
6. One short code example showing the conventions/style to follow
7. Domain language (define exact nouns the implementation is allowed to use)
8. Invalid state transitions (list state mutations that must throw errors)

Mid-interview, when the design gets substantive, pause and ask:

> Before we move on — what are the major design decisions here? List them as "We chose X over Y because Z." I want to make sure we're aligned before you write anything. Push back if you think I'm making a bad call.
