---
name: regression-qa
description: >
  Generates and runs a regression test suite for an existing backend project
  (REST/GraphQL APIs, CLI tools, client-server apps). Use this skill whenever
  the user wants to: audit what a project does and write tests for it, generate
  regression tests for existing code, ensure all endpoints or commands are
  covered by passing tests, run QA on a project they didn't write, or say
  things like "make sure everything works", "write regression tests", "test
  all my endpoints", "QA this project", or "run until green". Also triggers on
  "ralph loop" + testing context.
---

# Regression QA

Generates a regression test suite for an existing project by observing what
the code actually does, writing tests that pin that behavior, and optionally
looping until all tests pass.

This is NOT TDD. The spec is derived from existing code. Tests start green
for correct behavior and fail only when something breaks.

## Modes

**Single pass** (default): Run Planner → Generator → tests once. Surface
results. The user decides what to do with failures.

**Ralph Loop** (opt-in): Run Planner → Generator → tests → Healer in a loop
until all tests pass (or max iterations hit). Triggered when the user says
"ralph loop", "run until green", "loop until passing", or similar.

## Starting a session

The first thing to do is confirm `project_root`. Extract it from the user's
message (e.g. "the project at ~/vibe/myapp" → `/Users/<user>/vibe/myapp`).
If the user didn't specify a path, ask before proceeding. Never assume the
current working directory is the project to test.

## Workflow

### Step 1 — Planner

Spawn a subagent with the instructions in `agents/planner.md` (read it first).
Pass it:
- The project root directory
- The path to write specs: `<project_root>/regression-qa/specs/`

The Planner reads the codebase and writes one Markdown spec file per logical
module (e.g., `specs/users.md`, `specs/cli.md`). Each spec lists every
endpoint/command/function that needs a test, with expected inputs, outputs,
and edge cases.

The Planner is idempotent: if specs already exist, it updates them (adds new
functionality, marks removed functionality) rather than regenerating from
scratch.

### Step 2 — Generator

Spawn a subagent with the instructions in `agents/generator.md` (read it first).
Pass it:
- The project root
- The specs directory: `<project_root>/regression-qa/specs/`
- The test output directory: `<project_root>/regression-qa/tests/` (or the
  project's existing test dir if one exists and the user prefers)

The Generator reads the specs and writes pytest tests. It checks existing
tests first and only fills gaps — it does not overwrite tests that already
exist and pass.

### Step 3 — Run tests

Run the test suite using `scripts/run_tests.sh <project_root>`. This outputs
structured JSON to stdout. Capture it.

```bash
bash ~/.claude/skills/regression-qa/scripts/run_tests.sh <project_root>
```

Parse the JSON. If all tests pass, you're done — report the green count to
the user.

### Step 4 — Healer (Ralph Loop only)

If in Ralph Loop mode and there are failures, spawn a subagent with
`agents/healer.md`. Pass it:
- The project root
- The test output JSON (the failures array)

The Healer patches failing tests or annotates them as real bugs. After it
finishes, re-run `run_tests.sh` and check results.

Loop until:
- All tests pass (or all failures are annotated as real bugs), OR
- `max_iterations` is reached (default: 5)

On hitting max iterations, surface remaining failures to the user with a
clear summary: which tests were fixed, which are real bugs, which couldn't
be resolved.

### Step 5 — Report

Always end with a clear summary:
```
Regression QA complete
  Passed:      12
  Fixed:        3  (test issues, not bugs)
  Real bugs:    1  (annotated with pytest.mark.skip)
  Unresolved:   0
  Iterations:   2
```

If real bugs were found, list them explicitly so the user can decide what
to do.

## Idempotency

Safe to re-run at any time:
- Planner updates specs in-place, never duplicates
- Generator only adds missing test coverage, never overwrites passing tests
- Healer only touches failing tests
- Re-running on a fully-green project is a no-op

## Setup note

Specs and generated tests live under `<project_root>/regression-qa/`. You
can commit this directory — it becomes the project's living regression suite.

## Reading the agent files

Before spawning each subagent, read the corresponding agent file:
- `~/.claude/skills/regression-qa/agents/planner.md`
- `~/.claude/skills/regression-qa/agents/generator.md`
- `~/.claude/skills/regression-qa/agents/healer.md`

Pass the full content as the subagent's system instructions.
