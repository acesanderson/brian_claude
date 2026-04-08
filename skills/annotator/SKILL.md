---
name: annotator
description: Workflow skill for hand-annotating licensed courses and conference talks using the annotator-project CLI. Use whenever the user wants to start an annotation pass, sample a new queue, check annotation progress, see how many items have been labeled, or work with any annotation task.
---

# Annotator

Human annotation tool for building ground-truth labels. Project lives at `~/vibe/annotator-project/`.

**Task log:** `~/.local/share/annotation/tasks.md` — read this at session start to surface pending tasks. Update it when tasks are created or completed.

All commands are run via:
```bash
uv run --directory ~/vibe/annotator-project annotator <subcommand>
```

## Files

| File | Purpose |
|------|---------|
| `~/.local/share/annotation/tasks.md` | Pending and completed annotation tasks — source of truth |
| `~/vibe/annotator-project/annotation_queue.jsonl` | Default queue for course annotation tasks |
| `~/vibe/annotator-project/annotations.jsonl` | Default annotations file for course tasks |

Task-specific queues and annotations live next to their source data (e.g. `~/licensing/projects/ai-engineer/`).

## Subcommands

### sample — generate a course annotation queue (catalog DB)

```bash
uv run --directory ~/vibe/annotator-project annotator sample \
  --per-provider 20 \
  -o ~/vibe/annotator-project/annotation_queue.jsonl
```

- Default: 10 courses per provider; we use 20
- Baked-in filters: excludes `instructor-led`, excludes `dasa`/`devops-institute`/`finops-foundation`/`unknown`, requires ≥ 10 courses per provider
- Regenerating creates a new random sample — unannotated entries from the old queue are lost, but `annotations.jsonl` is untouched

### sample-talks — generate a talk annotation queue (talks-inventory JSON)

```bash
uv run --directory ~/vibe/annotator-project annotator sample-talks \
  <path/to/talks-inventory.json> \
  --tier review \
  -o <path/to/annotation_queue.jsonl>
```

- `--tier`: `review` (default) | `strong_candidate` | `reject`
- Normalizes talks to the same queue format as `sample` — `annotate` and `report` work unchanged
- Fields mapped: video ID → `course_id`, track → `provider_slug`, notes → `description`, duration → minutes, TIV score → `level`

### annotate — interactive annotation loop

```bash
uv run --directory ~/vibe/annotator-project annotator annotate \
  <queue.jsonl> \
  -o <annotations.jsonl>
```

- Resumable: skips already-annotated entries, picks up at first unannotated
- Saves after every entry — safe to quit anytime with `q`
- Controls: `y` yes / `n` no / `s` skip / `q` quit
- Reason codes (optional, press Enter to skip): `f` format, `l` length, `t` tone, `p` platform, `c` cert-prep, `o` other

**Must be run in a real terminal** — not invocable by Claude directly.

### report — check progress

```bash
uv run --directory ~/vibe/annotator-project annotator report \
  <annotations.jsonl> \
  [--csv <output.csv>]
```

Shows: label distribution, per-provider/per-track breakdown, reason code counts.

## Typical session

1. Read `~/.local/share/annotation/tasks.md` to see what's pending
2. Check progress: run `report` on the relevant annotations file
3. Start annotating: run `annotate <queue> -o <annotations>` in your terminal
4. After session: run `report` again; update `tasks.md` if task is complete

## On task creation

When a new annotation task is set up, append it to `tasks.md` under `## Pending`:

```markdown
- [ ] **<short name>** _(<project>)_
  - <one sentence on what's being annotated and the decision>
  - Queue: `<path>`
  - Annotations: `<path>`
  - Command: `uv run --directory ~/vibe/annotator-project annotator annotate <queue> -o <annotations>`
```

## On task completion

Move the entry from `## Pending` to `## Completed`, change `[ ]` to `[x]`, add completion date.
