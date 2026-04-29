# Scheduled Batch Jobs — HeadwaterServer Design Spec

## Problem

`classify_orgs.py` runs on the MacBook, connects to Headwater GPU hosts, and blocks for
hours on large datasets (11k rows). Brian wants to submit the job during the day and have
it execute at 3 AM without the MacBook staying on.

## Decision: Model A — Server Holds Prompts, Runs Inference at Scheduled Time

1. Client reads CSV, builds prompt list, POSTs job spec + scheduled time to HeadwaterServer
2. Server stores the job (SQLite) and runs inference autonomously at the scheduled time
3. Client fetches results the next morning, reconstructs output CSV

MacBook can be closed after submit.

## Where the Endpoint Lives: Router (port 8081)

The router is the right host because:
- Single submit endpoint regardless of which GPU hosts are alive at 3 AM
- At execution time, the router picks the best available backend via existing fallback logic
- Consistent with how `classify_orgs.py` already works (`headwater` alias → 8081)

## Scheduler Mechanism

`asyncio` background loop in FastAPI's `lifespan` context — no APScheduler dep needed.

```python
async def scheduler_loop():
    while True:
        await run_due_jobs()
        await asyncio.sleep(60)  # check every minute
```

Started in the existing `lifespan()` context manager in `headwater-server/server/headwater.py`.

## API Surface (3 new endpoints on router)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/jobs` | Submit a scheduled job, returns `job_id` |
| `GET` | `/jobs/{id}` | Status + results when done |
| `GET` | `/jobs` | List all jobs (optional `?status=pending` filter) |

## Job Spec (POST /jobs body)

```json
{
  "prompts": ["...formatted prompt string per org..."],
  "model": "gpt-oss:latest",
  "temperature": 0.0,
  "output_type": "structured_response",
  "project_name": "ed-rolodex-classifier",
  "scheduled_at": "2026-04-24T03:00:00",
  "label": "ed_rolodex_full_run"
}
```

Response: `{"job_id": "...", "status": "pending", "scheduled_at": "..."}`

## Response Schema Approach

Do not try to serialize the Pydantic class (`OrgClassification`) over the wire. Instead:
- Server runs prompts with `output_type="structured_response"` but without schema enforcement
- Results stored as raw JSON strings per prompt
- `classify_orgs.py` already has `_parse_conv()` as a fallback JSON parser — reuse that
  on the fetch side to reconstruct `OrgClassification` objects from stored JSON

This keeps the schema logic entirely client-side. No server-side schema registry needed.

## Results Storage

SQLite on the router host. Schema:

```
jobs(
  id TEXT PRIMARY KEY,
  label TEXT,
  submitted_at TEXT,
  scheduled_at TEXT,
  started_at TEXT,
  completed_at TEXT,
  status TEXT,         -- pending | running | done | failed
  prompt_count INTEGER,
  results_json TEXT,   -- JSON array of per-prompt result strings
  error TEXT
)
```

11k results × ~200 bytes each ≈ ~2MB per job. Fine for SQLite TEXT.
Add a TTL cleanup on results older than 30 days.

## Startup Recovery

On router startup: any jobs in `status = 'running'` are reset to `status = 'pending'`.
Prevents orphaned jobs after a router restart mid-execution.

## New Files

### headwater-api
- `classes/jobs.py` — `BatchJobRequest`, `BatchJobStatus`, `JobResult`

### headwater-server
- `api/jobs_server_api.py` — route registration (mirrors `conduit_server_api.py` pattern)
- `services/jobs_service/job_store.py` — SQLite CRUD (aiosqlite)
- `services/jobs_service/scheduler.py` — asyncio loop, dispatches due jobs via existing conduit batch service
- `server/headwater.py` — wire scheduler into lifespan + register `JobsServerAPI` (2-line change)

### headwater-client
- `api/jobs_api.py` — `JobsAsyncAPI` (submit, get, list)
- `client/headwater_client_async.py` — add `.jobs` property

### classify_orgs.py (or companion scripts)
Two new modes alongside the existing immediate-run default:

- `--submit [--at HH:MM]` — reads CSV, builds prompts, POSTs to `/jobs`, prints job ID
- `--fetch JOB_ID` — GETs results, parses JSON → `OrgClassification`, writes output CSV

Existing `uv run classify_orgs.py --input X --output Y` behavior unchanged.

## Typical Workflow After This Is Built

```bash
# morning: submit for tonight
uv run ~/licensing/scripts/classify_orgs.py \
  --input scripts/ed_rolodex_enriched.csv \
  --output scripts/ed_rolodex_classified.csv \
  --submit --at 03:00
# → job_id: 20260424_030000_abc123

# next morning: fetch results
uv run ~/licensing/scripts/classify_orgs.py \
  --fetch 20260424_030000_abc123 \
  --output scripts/ed_rolodex_classified.csv
```

## Open Questions (resolved before implementation)

1. ~~Split classify_orgs.py vs. companion scripts?~~ → `--submit`/`--fetch` flags on existing script
2. ~~Response schema portability?~~ → raw JSON stored server-side, client-side Pydantic parsing
3. ~~Scheduler on router or individual server?~~ → router

## Gotchas

- `aiosqlite` dependency needs to be added to `headwater-server/pyproject.toml`
- Router currently has no persistent state — SQLite file location needs to be configurable
  (env var `HEADWATER_JOBS_DB`, default `~/.local/share/headwater/jobs.db`)
- The existing conduit batch service runs on individual servers (port 8080), not the router.
  The router's scheduler will need to act as a conduit client (HTTP POST to `/conduit/batch`
  on the selected backend), not call the service function directly.
- Large prompt lists (11k items) should be chunked for the POST body to avoid hitting any
  default request size limits in uvicorn (default 1MB). Either chunk on submit or raise
  `--limit-max-requests` in uvicorn config.
