---
name: cronicle
description: Use when creating, configuring, or debugging Cronicle scheduled jobs on AlphaBlue. Covers event setup, the standard shell command template, Python script patterns (logging, checkpointing, resumability), known gotchas, and how an LLM agent can create events via the Cronicle API. Trigger whenever the user mentions Cronicle, scheduling a job on AlphaBlue, or wants to run a script on a schedule.
---

# Cronicle

Cronicle is the job scheduler running on **AlphaBlue** at `http://172.16.0.2:3012`. It provides a web UI, live log viewer, concurrency control, and job history. Jobs must be physically present on AlphaBlue — script deployment is HITL (user copies via `scp` or syncs via `git pull` / `deploy.sh`).

Cronicle runs as **root** by default (required by Cronicle). This is accepted. Use XDG env vars in the shell preamble to redirect data paths to the fishhouses user's home.

---

## Standard Shell Command Template

Use this as the preamble for every Cronicle event:

```bash
#!/bin/bash
set -eo pipefail
source /home/fishhouses/.secrets
source /home/fishhouses/.exports
export XDG_DATA_HOME=/home/fishhouses/.local/share
export XDG_CONFIG_HOME=/home/fishhouses/.config
export XDG_STATE_HOME=/home/fishhouses/.local/state
cd /home/fishhouses/Brian_Code/<project>
exec /home/fishhouses/.local/bin/uv run python jobs/<script>.py --cron
```

Key decisions:
- `#!/bin/bash` — Cronicle defaults to `sh`; `pipefail` is bash-only, shebang is required
- `set -eo pipefail` — exit on error, catch pipe failures; `-u` is omitted because sourced files often reference unset vars
- `source .secrets` + `source .exports` — inject env vars; keeps secrets out of the Cronicle UI
- XDG overrides — Cronicle runs as root, so XDG defaults to `/root/.local/...`; override to use fishhouses' actual data/config/state dirs
- `exec` — replaces the shell process with Python so SIGTERM from Cronicle hits Python directly

---

## Event Settings (UI)

| Field | Value | Why |
|---|---|---|
| **Timeout** | `0` (disabled) for long jobs | Let the script decide when to stop |
| **Concurrency** | `1` | Never run two instances simultaneously |
| **Retries** | `0` | Script handles its own resume logic |
| **Allow Queued Jobs** | off | With concurrency=1, overlapping triggers skip rather than queue |
| **Category** | meaningful group | Keeps the Schedule tab navigable |

### One-time scheduling

The timing widget is cron-like but supports one-time runs: select a specific year + month + day + hour + minute. Example: 2026 → May → 6th → 2 → :00 produces "will run once at 2:00 AM on May 6, 2026." Disable the event after it runs if you don't want recurrence.

### Global config gotchas

In `/opt/cronicle/conf/config.json`:
- `job_memory_max`: defaults to 1 GB (`1073741824`). Set to `0` to disable for memory-hungry jobs (ML inference, large dataframes).
- `job_env`: inject env vars for all jobs — good for non-secret vars like `POSTGRES_USERNAME`. For secrets, prefer `source /home/fishhouses/.secrets` in the shell command instead.

---

## Python Script Pattern

```python
"""
job_name — one-line description.

Usage:
    uv run python jobs/my_job.py            # full run
    uv run python jobs/my_job.py --cron     # health-gated (for Cronicle)
    uv run python jobs/my_job.py --dry-run  # print plan, exit
    uv run python jobs/my_job.py --limit N  # first N items (smoke test)
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent / "my_job.log"
STATUS_PATH = Path(__file__).parent / "my_job_status.json"

logger = logging.getLogger(__name__)
_shutdown = False


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # captured by Cronicle live log
            logging.FileHandler(LOG_PATH),       # persistent on disk
        ],
    )


def handle_sigterm(signum, frame) -> None:
    global _shutdown
    _shutdown = True
    logger.info("SIGTERM received — will stop after current unit of work")


def health_check() -> bool:
    # ping servers/dependencies; return False to skip cleanly
    ...


def run(args: argparse.Namespace) -> None:
    # main logic — check `_shutdown` between units of work
    ...


def write_status(status: str, **kwargs) -> None:
    import json
    STATUS_PATH.write_text(json.dumps({
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cron", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    setup_logging()
    signal.signal(signal.SIGTERM, handle_sigterm)

    if args.dry_run:
        return

    if args.cron and not health_check():
        logger.info("health check failed — skipping (exit 0)")
        sys.exit(0)  # clean skip; Cronicle does not mark as failure

    try:
        run(args)
        write_status("success")
    except Exception:
        logger.exception("unhandled exception")
        write_status("failure")
        sys.exit(1)  # non-zero → Cronicle marks job failed


if __name__ == "__main__":
    main()
```

### Checkpointing / Resumability / Idempotency

- **Checkpoint in DB** — upsert, not insert; derive stable IDs from content (hash or natural key)
- **On startup** — query existing state, skip completed work before doing anything
- **Per-unit saves** — write to DB after each unit completes, not in a batch at the end
- **Idempotent writes** — `ON CONFLICT DO UPDATE`; running twice produces the same result
- **`--cron` flag** — health-gate before doing any work; exit 0 on skip so Cronicle doesn't flag as failure

---

## Script Deployment (HITL)

Scripts must be physically present on AlphaBlue before Cronicle can run them. Current workflow:

```bash
# From local machine — push and pull via deploy.sh
bash scripts/deploy.sh alphablue

# Or manual scp for one-off files
scp myfile.py alphablue:/home/fishhouses/Brian_Code/<project>/
```

There is no automated deployment from Cronicle itself. The user must sync code before scheduling.

---

## LLM Agent: Creating Events via API

Cronicle exposes a REST API. Get an API key from **Administration → API Keys** in the UI.

### Create an event

```bash
curl -s -X POST http://172.16.0.2:3012/api/app/create_event/v1 \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "my job",
    "enabled": 1,
    "plugin": "shellplug",
    "target": "alphablue",
    "timing": { "hours": [2], "minutes": [0] },
    "max_children": 1,
    "timeout": 0,
    "catch_up": 0,
    "params": {
      "script": "#!/bin/bash\nset -eo pipefail\nsource /home/fishhouses/.secrets\n..."
    }
  }'
```

### Run an event immediately

```bash
curl -s "http://172.16.0.2:3012/api/app/run_event/v1?id=EVENT_ID&api_key=YOUR_KEY"
```

### List schedule

```bash
curl -s "http://172.16.0.2:3012/api/app/get_schedule/v1?api_key=YOUR_KEY"
```

For one-time timing, use a specific date in the `timing` object:
```json
"timing": { "years": [2026], "months": [5], "days": [6], "hours": [2], "minutes": [0] }
```

Full API docs: https://github.com/jhuckaby/Cronicle/blob/master/docs/API.md

---

## Future: Multi-Host Expansion

**TBD** — Cronicle supports multi-server clusters natively. Plan is to install Cronicle workers on all hosts (petrosian, spassky, caruana, botvinnik, etc.) so that AlphaBlue acts as the primary scheduler and jobs can be targeted to any host by name. This would allow work-laptop-specific scripts to be managed from a single UI. See Cronicle docs on server groups and the `target` field in events.

---

## Known Gotchas

| Problem | Cause | Fix |
|---|---|---|
| `uv: not found` (exit 127) | Headless PATH lacks `~/.local/bin` | Use absolute path: `/home/fishhouses/.local/bin/uv run` |
| `Illegal option -o pipefail` (exit 2) | Cronicle runs `sh` by default | Add `#!/bin/bash` shebang |
| `unbound variable` in sourced file | `-u` flag catches vars in `.exports` | Use `-eo pipefail` not `-euo pipefail` |
| `FileNotFoundError` on dataset paths | Cronicle runs as root; XDG resolves to `/root/...` | Set XDG env vars to `/home/fishhouses/.local/...` in shell preamble |
| `Exceeded memory limit of 1 GB` | `job_memory_max` global default | Set to `0` in `conf/config.json` and restart Cronicle |
| Secrets missing at runtime | Headless shell doesn't source `~/.bashrc` | `source /home/fishhouses/.secrets` in shell preamble |
