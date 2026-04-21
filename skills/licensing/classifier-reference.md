# Classifier Reference

Two-pass course-level classifier that determines whether a scraped course is a licensing candidate.

**Pass 1 — deterministic pre-filter** (no LLM): reads `context/classifier-blockers.yaml`. Blocks on format, product_type, title, and description patterns. Fast, free.

**Pass 2 — LLM-as-judge**: renders `scripts/classifier_prompt.j2` per course, runs via `ConduitBatchAsync` with `gpt-oss:latest`. Returns a `ClassifierResult` Pydantic model with per-signal verdicts and a `proceed / flag / reject` recommendation.

## CLI Invocations

```bash
# Batch — classify all unclassified courses in a partner catalog
/Users/bianders/Brian_Code/conduit-project/.venv/bin/python scripts/classify.py partners/<slug>/catalog.json

# Single course spot-check (no file write)
/Users/bianders/Brian_Code/conduit-project/.venv/bin/python scripts/classify.py --single 3 partners/<slug>/catalog.json

# Re-classify already-classified courses
/Users/bianders/Brian_Code/conduit-project/.venv/bin/python scripts/classify.py --overwrite partners/<slug>/catalog.json
```

Results written back into `catalog.json` per course under a `classifier` key.

## Living Config Files

Update these to change classifier behavior — no code changes needed:

- `context/classifier-blockers.yaml` — hard eliminators; add/remove patterns freely
- `context/classifier-quality-signals.yaml` — LLM signal prompts; edit `prompt:` field to change how the LLM evaluates each signal
- `context/topic-priority.yaml` — green/yellow/red topic rubric; update whenever Content Strategy's priorities shift

## Local Model Constraint

`gpt-oss:latest` runs via HeadwaterClient on AlphaBlue. Do NOT run Ollama directly on MacBook (saturates memory). On MacBook, `conduit query --model gpt-oss` routes automatically through Headwater — no special flags needed. If Headwater is unreachable, stop and report; do NOT substitute a cloud model.
