---
name: refactor-worktree
description: >
  Refactor code in an isolated git worktree on a new branch, leaving the current branch and
  working directory untouched. Use when the user asks to refactor, restructure, clean up, or
  reorganize code and wants the work done safely in isolation. Trigger phrases include "refactor
  this", "clean up this code", "restructure this module", "refactor but don't touch my current
  branch", "refactor in a worktree", or any refactoring request where branch safety is implied
  or stated.
---

# Refactor in Worktree

Perform all refactoring in an isolated git worktree on a new branch. Never modify files in the
current working directory. The user's active branch and install remain untouched.

## Workflow

### 1. Confirm scope

Before touching anything, state:
- What is being refactored (files/modules/scope)
- The branch name you will create (e.g. `refactor/auth-module`)
- The worktree path (e.g. `../[repo-name]-refactor`)

Get a quick confirmation if the scope is large or destructive (e.g. renaming across many files).

### 2. Create the worktree

```bash
# From the repo root
git worktree add <worktree-path> -b <branch-name>
```

Convention for paths and names:
- Path: `../<repo-name>-refactor` (sibling directory, not inside the repo)
- Branch: `refactor/<short-descriptor>` (e.g. `refactor/auth-cleanup`)

Verify success before proceeding:
```bash
git worktree list
```

### 3. Perform the refactor

All edits happen inside the worktree directory. Never edit files under the original repo path.

Follow this sequence:
1. Read the relevant files to understand the current structure
2. Plan the changes — identify all affected files before editing any
3. Make changes incrementally; run tests (if available) after each logical unit
4. Do not refactor beyond the stated scope

### 4. Commit in the worktree

```bash
cd <worktree-path>
git add <specific-files>
git commit -m "refactor: <description>"
```

Use focused commits. Do not bundle unrelated changes.

### 5. Report back

After committing, tell the user:
- Branch name and worktree path
- Summary of what changed and why
- How to review: `git diff main..<branch-name>` or `git log <branch-name>`
- How to merge when ready: `git merge <branch-name>` or open a PR

Do not automatically merge or push unless the user explicitly asks.

## Rules

- **Never edit files in the original working directory.** All writes go to the worktree.
- **Do not run `git worktree remove` automatically.** Leave cleanup to the user.
- If the repo has a test suite, run it before and after refactoring.
- If the refactor touches public APIs or interfaces, flag the breaking changes explicitly.
- Keep the branch name and worktree path visible throughout so the user always knows where work is happening.
