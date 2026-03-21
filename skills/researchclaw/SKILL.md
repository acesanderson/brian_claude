# ResearchClaw — Autonomous Research Pipeline Skill

## Description

Run ResearchClaw's 23-stage autonomous research pipeline. Given a research topic, this skill orchestrates the entire research workflow: literature review → hypothesis generation → experiment design → code generation & execution → result analysis → paper writing → peer review → final export.

## Prerequisites

- `uv` — required. Install: https://docs.astral.sh/uv/getting-started/installation/
- ResearchClaw repo at: `/Users/bianders/vibe/auto-research-claw`

## Trigger Conditions

Activate this skill when the user:
- Asks to "research [topic]", "write a paper about [topic]", or "investigate [topic]"
- Wants to run an autonomous research pipeline
- Asks to generate a research paper from scratch
- Mentions "ResearchClaw" by name

## Instructions

### Prerequisites Check

1. Verify the repo exists:
   ```bash
   ls /Users/bianders/vibe/auto-research-claw/pyproject.toml
   ```

2. Install the CLI as a uv tool (one-time, idempotent):
   ```bash
   uv tool install --editable /Users/bianders/vibe/auto-research-claw
   ```

3. Verify config exists at the repo root:
   ```bash
   ls /Users/bianders/vibe/auto-research-claw/config.yaml
   ```
   If missing, copy the example:
   ```bash
   cp /Users/bianders/vibe/auto-research-claw/config.researchclaw.example.yaml \
      /Users/bianders/vibe/auto-research-claw/config.yaml
   ```

4. Ensure the user's LLM API key is set in `config.yaml` under `llm.api_key` or `llm.api_key_env`.

### Running the Pipeline

**Option A: CLI via uv tool (recommended)**

```bash
researchclaw run \
  --config /Users/bianders/vibe/auto-research-claw/config.yaml \
  --topic "Your research topic here" \
  --auto-approve
```

If `uv tool install` hasn't been run yet, fall back to:
```bash
uv run --directory /Users/bianders/vibe/auto-research-claw \
  researchclaw run --topic "Your research topic here" --auto-approve
```

Options:
- `--topic` / `-t`: Override the research topic from config
- `--config` / `-c`: Config file path
- `--output` / `-o`: Output directory (default: `artifacts/rc-YYYYMMDD-HHMMSS-HASH/` inside repo)
- `--from-stage`: Resume from a specific stage (e.g., `PAPER_OUTLINE`)
- `--auto-approve`: Auto-approve gate stages (5, 9, 20) without human input

**Option B: Python API**

```bash
uv run --directory /Users/bianders/vibe/auto-research-claw python - <<'EOF'
from researchclaw.pipeline.runner import execute_pipeline
from researchclaw.config import RCConfig
from researchclaw.adapters import AdapterBundle
from pathlib import Path

config = RCConfig.load("/Users/bianders/vibe/auto-research-claw/config.yaml", check_paths=False)
results = execute_pipeline(
    run_dir=Path("/Users/bianders/vibe/auto-research-claw/artifacts/my-run"),
    run_id="research-001",
    config=config,
    adapters=AdapterBundle(),
    auto_approve_gates=True,
)
for r in results:
    print(f"Stage {r.stage.name}: {r.status.value}")
EOF
```

**Option C: Iterative Pipeline (multi-round improvement)**

```bash
uv run --directory /Users/bianders/vibe/auto-research-claw python - <<'EOF'
from researchclaw.pipeline.runner import execute_iterative_pipeline
from researchclaw.config import RCConfig
from researchclaw.adapters import AdapterBundle
from pathlib import Path

config = RCConfig.load("/Users/bianders/vibe/auto-research-claw/config.yaml", check_paths=False)
results = execute_iterative_pipeline(
    run_dir=Path("/Users/bianders/vibe/auto-research-claw/artifacts/my-run"),
    run_id="research-001",
    config=config,
    adapters=AdapterBundle(),
    max_iterations=3,
    convergence_rounds=2,
)
EOF
```

### Config: sandbox python_path

The default example config sets `experiment.sandbox.python_path: ".venv/bin/python"`. With uv, replace this with the uv-managed Python path:

```bash
uv python find 3.11  # prints the path to use
```

Then set in `config.yaml`:
```yaml
experiment:
  sandbox:
    python_path: "/path/from/uv/python/find"  # output of above command
```

### Output Structure

Artifacts are written to `/Users/bianders/vibe/auto-research-claw/artifacts/<run-id>/` by default:

```
artifacts/<run-id>/
├── stage-10/experiment.py          # Generated experiment code
├── stage-12/runs/run-1.json        # Experiment results
├── stage-14/experiment_summary.json
├── stage-17/paper_draft.md         # Full paper draft
├── stage-22/charts/                # Visualizations
└── pipeline_summary.json
```

Final deliverables are in `artifacts/<run-id>/deliverables/` — compile-ready LaTeX, BibTeX, charts.

### Experiment Modes

| Mode | Description | Config |
|------|-------------|--------|
| `simulated` | LLM generates synthetic results (no code execution) | `experiment.mode: simulated` |
| `sandbox` | Execute generated code locally via subprocess | `experiment.mode: sandbox` |
| `ssh_remote` | Execute on remote GPU server via SSH | `experiment.mode: ssh_remote` |

### Troubleshooting

- **Config validation error**: `uv run --directory /Users/bianders/vibe/auto-research-claw researchclaw validate --config config.yaml`
- **LLM connection failure**: Check `llm.base_url` and API key in `config.yaml`
- **Sandbox execution failure**: Run `uv python find 3.11` and set that path as `experiment.sandbox.python_path`
- **Gate rejection**: Add `--auto-approve` flag
- **`researchclaw` not found**: Run `uv tool install --editable /Users/bianders/vibe/auto-research-claw`

## Tools Required

- Bash (for CLI execution)
- Read/Write (for config and artifacts)
