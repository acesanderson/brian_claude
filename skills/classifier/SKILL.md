---
name: classifier
description: API cookbook for building bulk LLM classifiers using conduit + HeadwaterAsyncClient. Use when building any classifier script in ~/vibe/classifiers-project.
type: process
---

# Classifier Cookbook — conduit + Headwater

Each classifier is a custom script. What's reusable: the API surface, network topology, and patterns below. Build scripts in `~/vibe/classifiers-project/`.

**Run any script:** `uv run --directory ~/vibe/classifiers-project python <script>.py`

---

## Network topology

| host_alias | GPU | VRAM | Use when |
|---|---|---|---|
| *(omit)* | router | — | light jobs, let the router decide |
| `deepwater` | RTX 5090 | 32 GB | large models, long prompts, heavy parallelism |
| `bywater` | RTX 4090 | 16 GB | split traffic to parallelize against deepwater |

Default model: **`gpt-oss:latest`**. For bulk jobs, always heartbeat both hosts first and split 50/50.

---

## API surface

### Imports

```python
from headwater_client.client.headwater_client_async import HeadwaterAsyncClient
from headwater_api.classes import BatchRequest
from conduit.domain.request.generation_params import GenerationParams
from conduit.domain.config.conduit_options import ConduitOptions
```

### GenerationParams

```python
params = GenerationParams(
    model="gpt-oss:latest",
    output_type="structured_response",   # use for Pydantic-structured output
    response_model=MyModel,              # your Pydantic class
    temperature=0.0,
)
```

`output_type="structured_response"` + `response_model` activates instructor-backed structured parsing. Set `temperature=0.0` for classification.

### ConduitOptions

```python
options = ConduitOptions(project_name="my-classifier", include_history=False)
```

`project_name` is used for logging/attribution. `include_history=False` means each prompt is stateless — correct for batch classification.

### HeadwaterAsyncClient

```python
async with HeadwaterAsyncClient(host_alias="deepwater") as client:
    ok: bool = await client.ping()
    status = await client.get_status()   # .server_name, .uptime

    batch = BatchRequest(
        prompt_strings_list=["prompt1", "prompt2", ...],
        params=params,
        options=options,
    )
    resp = await client.conduit.query_batch(batch)

    for conv in resp.results:
        parsed = conv.last.parsed    # MyModel | None
        raw    = conv.last.content   # raw string (fallback when parsed is None)
```

`conv.last.parsed` is `None` when there's an instructor version mismatch — always have a fallback parse.

---

## Pydantic model pattern

```python
from enum import Enum
from pydantic import BaseModel, Field

class Confidence(str, Enum):
    LOW    = "LOW"
    MEDIUM = "MEDIUM"
    HIGH   = "HIGH"

class MyClassification(BaseModel):
    label: bool = Field(description="One-line summary. Full rubric lives in PROMPT_TEMPLATE only.")
    resolved_name: str = Field(description="Canonical, properly-cased name.")
    rationale: str = Field(description="One sentence explaining the decision.")
    confidence: Confidence = Field(description="HIGH = unambiguous. MEDIUM = secondary field needed. LOW = still uncertain.")
```

`Field(description=)` is read by the model — write it as instruction. But keep it to a summary; the full rubric goes in `PROMPT_TEMPLATE`. Duplication between the two causes silent drift.

Always include `confidence` (triage signal, not a filter) and `rationale` (exposes reasoning during rubric iteration). Default to false / conservative — precision over recall.

---

## Prompt template pattern

```python
PROMPT = """\
You are a [role]. Classify the following [entity].
Input: {input_json}
[primary_field] is X. [secondary_field] is Y — use it as a signal about Z.
Respond with JSON only — no commentary, no markdown fences.

label:
  true  → [ALL of: condition 1, condition 2, condition 3]
  false → [ANY of: disqualifier 1, disqualifier 2, ...]
  When in doubt, default to false.
..."""
```

Input is always a JSON blob of all available fields — not just the primary key. Secondary fields resolve ambiguous primaries.

---

## Minimal script skeleton

```python
from __future__ import annotations
import argparse
import asyncio
import csv
import json
import random
from pathlib import Path
from typing import TYPE_CHECKING
from enum import Enum
from pydantic import BaseModel, Field
from headwater_client.client.headwater_client_async import HeadwaterAsyncClient
from headwater_api.classes import BatchRequest
from conduit.domain.request.generation_params import GenerationParams
from conduit.domain.config.conduit_options import ConduitOptions

if TYPE_CHECKING:
    pass

# --- define PROMPT, MyClassification, CHUNK_SIZE, HOSTS, helpers here ---

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample", type=int, default=None)
    args = parser.parse_args()

    with open(args.input, newline="") as f:
        rows = list(csv.DictReader(f))

    index = _build_index(rows, key_col="...", signal_col="...")
    keys  = list(index)
    if args.sample:
        keys = random.sample(keys, min(args.sample, len(keys)))
        index = {k: index[k] for k in keys}

    results = asyncio.run(run(index))

    fieldnames = list(rows[0].keys()) + ["label", "resolved_name", "rationale", "confidence"]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            clf = results.get(row["..."].strip())
            row["label"]         = clf.label if clf else ""
            row["resolved_name"] = clf.resolved_name if clf else ""
            row["rationale"]     = clf.rationale if clf else ""
            row["confidence"]    = clf.confidence.value if clf else ""
            writer.writerow(row)

if __name__ == "__main__":
    main()
```

---

## Recipes

### Deduplication

```python
def _build_index(rows: list[dict], key_col: str, signal_col: str) -> dict[str, str]:
    groups: dict[str, list[str]] = {}
    for row in rows:
        k = row[key_col].strip()
        if k:
            groups.setdefault(k, []).append(row.get(signal_col, ""))
    return {k: max((v.strip() for v in vs if v.strip()), key=len, default="")
            for k, vs in groups.items()}
```

Classify once per unique key; join back at write time. Consider normalizing keys before grouping (lowercase, strip legal suffixes) to avoid classifying `"Salesforce"` and `"Salesforce, Inc."` separately.

### Fallback parse

```python
def _parse(key: str, conv, model: type[MyClassification]) -> MyClassification:
    if conv.last.parsed is not None:
        return conv.last.parsed
    try:
        raw = conv.last.content
        return model(**json.loads(raw[raw.find("{"):raw.rfind("}") + 1]))
    except Exception:
        return model(label=False, resolved_name=key,
                     rationale="Parse failure.", confidence=Confidence.LOW)
```

### Dual-host batch

```python
CHUNK_SIZE = 20   # 100 hits 300s backend timeout
HOSTS = ["deepwater", "bywater"]

async def _heartbeat(host):
    try:
        async with HeadwaterAsyncClient(host_alias=host) as c:
            return await c.ping()
    except Exception:
        return False

async def run(index: dict[str, str]) -> dict[str, MyClassification]:
    params = GenerationParams(model="gpt-oss:latest", output_type="structured_response",
                              response_model=MyClassification, temperature=0.0)
    options = ConduitOptions(project_name="my-classifier", include_history=False)

    alive = await asyncio.gather(*[_heartbeat(h) for h in HOSTS])
    live = [h for h, ok in zip(HOSTS, alive) if ok]
    if not live:
        raise RuntimeError("No hosts available.")

    keys = list(index)
    chunks = [keys[i:i+CHUNK_SIZE] for i in range(0, len(keys), CHUNK_SIZE)]

    async def half(host, these_chunks):
        results = {}
        async with HeadwaterAsyncClient(host_alias=host) as c:
            for chunk in these_chunks:
                prompts = [PROMPT.format(input_json=json.dumps(
                    {"primary": k, "secondary": index[k]})) for k in chunk]
                resp = await c.conduit.query_batch(
                    BatchRequest(prompt_strings_list=prompts, params=params, options=options))
                for k, conv in zip(chunk, resp.results):
                    results[k] = _parse(k, conv, MyClassification)
        return results

    if len(live) == 1:
        return await half(live[0], chunks)
    mid = len(chunks) // 2
    a, b = await asyncio.gather(half(live[0], chunks[:mid]), half(live[1], chunks[mid:]))
    return {**a, **b}
```

---

## Non-negotiable before any full run

**Checkpoint before you run.** This is mandatory, not optional. A crash at chunk 130/199 with no checkpoint means starting the entire run over — including work completed on the other host. Learned the hard way.

Required pattern — add before `_classify_half`:

```python
CHECKPOINT = Path("/tmp/classify_checkpoint.json")

def load_checkpoint(model):
    if not CHECKPOINT.exists():
        return {}
    return {k: model(**v) for k, v in json.loads(CHECKPOINT.read_text()).items()}

def save_checkpoint(results):
    CHECKPOINT.write_text(json.dumps({k: v.model_dump() for k, v in results.items()}))
```

Inside `half()`: skip keys already in checkpoint, call `save_checkpoint({**checkpoint, **results})` after every chunk. On startup, load checkpoint and exclude already-classified keys from `org_keys`.

**NEVER delete the checkpoint before confirming the run completed.** If restarting after a crash, the checkpoint holds all prior work. Only clear it after the final CSV has been written and verified.

---

## Known gaps — mitigate before scaling

**Resumability.** Crash at chunk 30/60 = start over. Write a checkpoint JSON after each chunk; skip already-classified keys on startup. Merges naturally with an identity cache.

**Confidence is uncalibrated.** Self-reported HIGH ≠ accurate. Build a gold set (~200 rows, seeded from reviewed LOWs) to measure precision/recall per rubric version. Without it, rubric iteration is aesthetic. Consider prompting: *"What additional information would change your classification?"* — surfaces genuine ambiguity better than an enum.

**Identity cache.** Cache `normalized_key → result` across runs so re-running on updated data only classifies new rows. Keyed on normalized name + headline hash.

**Variable prompt length.** CHUNK_SIZE=20 assumes uniform prompt size. For variable-length fields, target ~8 000 tokens/batch: estimate `len(prompt) // 4` per item and fill to budget.

---

## Pilot workflow

1. `--sample 100` first. Review YES list + LOW list.
2. Tighten rubric in `PROMPT_TEMPLATE` (Field descriptions are summaries only).
3. Repeat until YES list is clean — typically 3–4 iterations.
4. Run full corpus. Print summary: `label: N/M (X%)`, `Confidence: HIGH=N, MEDIUM=N, LOW=N`.
