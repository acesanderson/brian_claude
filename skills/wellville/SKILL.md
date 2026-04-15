---
name: wellville
description: Personal wellbeing assistant covering health and finances. Use when the user asks about health records, medical history, financial state, FIRE progress, or anything related to their personal wellbeing system. Invocable by user only.
---

# Wellville — Personal Wellbeing System

Wellville is the unified home for health and financial tracking. Two subskills; one source of truth.

```
~/wellville/
├── health/            ← health facts vault  → read health.md for full context
└── finances/          ← financial facts vault → read finances.md for full context
```

## Which subskill to load

- **Health query** (symptoms, appointments, medications, labs, medical history): read `~/.claude/skills/wellville/health.md`
- **Finance query** (FIRE status, accounts, portfolio, purchases, snapshots, morgan): read `~/.claude/skills/wellville/finances.md`
- **Both / unclear**: read both files

Load the relevant subskill file with the Read tool before proceeding.

## Keyword: resolve

When the user says **resolve**, run these two steps in order:

**Step 1 — Flush todos.** For each subproject touched this session, check whether any new open items, follow-ups, or decisions belong in its `todos.md`. If so, append them. Do not duplicate existing items.
- `~/wellville/health/todos.md`
- `~/wellville/finances/todos.md`

**Step 2 — Improve the skill.** Re-read `health.md` and `finances.md` (whichever subskills were active). If any workflow convention, assumption, or structural fact changed during the session — update the relevant subskill file. Only make changes that would materially help a future session; skip cosmetic edits.
