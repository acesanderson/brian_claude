# Implementation Plan: Batch-Dispatch Observability Improvements

## Context

**Problem:** The batch-dispatch skill provides zero visibility during execution. When running 38 workers for 2+ hours, all tasks timed out but this was only discovered at completion, wasting significant time and API credits.

**Solution:** Add observability features per `/Users/bianders/Brian_Code/sandbox/scraping/OBSERVABILITY.md` specification to catch configuration errors early (within 20 minutes vs 2+ hours) and provide real-time progress feedback.

**Scope:** Phase 1 implementation (pre-flight validation + real-time monitoring) with extension points for Phase 2/3 features.

---

## Implementation Approach

### Phase 1: Critical Features (Implement Now)

#### 1. Pre-flight Validation

**Purpose:** Test skill on first item before launching full batch to catch configuration issues early.

**Implementation:**
- New function: `async def validate_skill(item, skill_name, user_template, timeout, run_id)`
- Reuses existing `run_worker()` logic with `index=0` in dedicated `batch_runs/{run_id}/preflight/task_0/` directory
- Returns `(success: bool, result: dict, preview: str)` tuple
- Preview shows first 500 chars of result data or error message
- Cleans up preflight directory after validation

**Integration in `main()` (after line 291):**
```python
if not args.skip_preflight:
    print(f"\n--- Pre-flight Validation ---")
    success, result, preview = await validate_skill(inputs[0], ...)

    if not success:
        print(f"❌ Pre-flight FAILED: {result.get('error')}")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            sys.exit(1)
    else:
        print(f"✅ Pre-flight PASSED\nSample: {preview}")
        input("Press Enter to proceed...")
```

**New CLI argument:**
```python
--skip-preflight  # Skip validation (for trusted workflows)
```

#### 2. Real-time Progress Monitoring

**Purpose:** Background task reporting progress every 2 minutes during execution.

**Implementation:**
- New function: `async def monitor_progress(results_list, total_tasks, interval, stop_event)`
- Runs as separate asyncio task launched before worker execution
- Calculates metrics from shared `results_list`: completed, success, errors, timeouts, success rate
- Output format: `[Progress] 15/50 completed (30%) | Success: 13/15 (87%) | Errors: 2 | Runtime: 5m 32s`
- Uses `asyncio.sleep(interval)` with `stop_event` check for graceful shutdown

**Integration in `main()` (replacing line 301 `asyncio.gather`):**
```python
# Shared state
results_list = []
stop_monitor = asyncio.Event()

# Launch monitor
if args.monitor_interval > 0:
    monitor_task = asyncio.create_task(
        monitor_progress(results_list, len(inputs), args.monitor_interval, stop_monitor)
    )

# Wrapper to collect results
async def worker_with_collection(worker_coro):
    result = await worker_coro
    results_list.append(result)
    return result

# Execute
worker_tasks = [worker_with_collection(task) for task in tasks]
results = await asyncio.gather(*worker_tasks)

# Stop monitoring
stop_monitor.set()
if args.monitor_interval > 0:
    await monitor_task
```

**New CLI argument:**
```python
--monitor-interval SECONDS  # Default: 120, 0 to disable
```

---

### Phase 2: Extension Points (Design Only)

**Features to add later:**
1. **Worker logging:** Capture stdout/stderr to `task_N/worker.stdout` and `task_N/worker.stderr`
   - Modify `run_worker()` to write process output to files
   - Add log paths to error results
   - CLI: `--no-worker-logs`

2. **Fail-fast mode:** Abort if first N tasks all fail
   - New function: `async def check_fail_fast(results_list, threshold, stop_event)`
   - Cancel remaining workers if all of first N fail
   - CLI: `--fail-fast=N`

**Extension points:**
- `run_worker()` already captures stdout/stderr (lines 96-104), just needs file writing
- Worker cancellation via `asyncio.Event` already supported by monitoring pattern
- Incremental result saving can use same `worker_with_collection()` wrapper

---

## Critical Files

### Primary Implementation
- **`/Users/bianders/.claude/skills/batch-dispatch/references/batch_runner.py`**
  - Current: 322 lines, Python async with argparse
  - Modify: Add 2 new functions (~80 lines), update `main()` (~40 lines)
  - Total: ~400 lines after Phase 1

### Documentation Updates
- **`/Users/bianders/.claude/skills/batch-dispatch/SKILL.md`**
  - Add new CLI arguments to "Options" section (lines 59-63)
  - Add example showing observability features
  - Update "How It Works" section with monitoring description

### Reference (Read-Only)
- **`/Users/bianders/Brian_Code/sandbox/scraping/OBSERVABILITY.md`**
  - Source specification for all improvements

---

## Existing Patterns to Reuse

### From batch_runner.py:

1. **Async worker pattern** (lines 43-152):
   - Use `asyncio.Semaphore` for concurrency control
   - Return result dicts: `{"status": "success|error|timeout", "item": ..., "data": ...}`
   - Preflight can directly call `run_worker()` with different parameters

2. **Error handling** (lines 146-152):
   - Wrap in try/except, return error dicts on failure
   - Include `task_dir` in all results for debugging

3. **CLI argument pattern** (lines 242-263):
   - Use `argparse.ArgumentParser` with formatted epilog
   - Use `action="store_true"` for boolean flags
   - Use `type=int, default=X` for numeric options

4. **Directory management** (lines 281-283):
   - Use `datetime.now().strftime("%Y%m%d_%H%M%S")` for run IDs
   - Create directories with `os.makedirs(path, exist_ok=True)`

---

## Implementation Steps

### Step 1: Pre-flight Validation (~2 hours)

1. **Add `validate_skill()` function** (after `run_worker()`, ~40 lines):
   ```python
   async def validate_skill(item, skill_name, user_template, timeout, run_id):
       """Run skill on single item to validate configuration."""
       preflight_dir = os.path.join(BATCH_DIR_NAME, run_id, "preflight")
       os.makedirs(preflight_dir, exist_ok=True)

       # Call run_worker with sem=asyncio.Semaphore(1), index=0
       result = await run_worker(
           sem=asyncio.Semaphore(1),
           run_id=run_id,
           index=0,
           item=item,
           skill_name=skill_name,
           user_template=user_template,
           timeout=timeout
       )

       # Generate preview
       success = result["status"] == "success"
       if success:
           data_preview = str(result.get("data", {}))[:500]
       else:
           data_preview = result.get("error", "Unknown error")[:500]

       # Cleanup preflight directory
       shutil.rmtree(preflight_dir, ignore_errors=True)

       return (success, result, data_preview)
   ```

2. **Add CLI argument** (in `main()`, after line 263):
   ```python
   parser.add_argument(
       "--skip-preflight",
       action="store_true",
       help="Skip pre-flight validation on first item"
   )
   ```

3. **Integrate validation** (in `main()`, after line 291):
   - Add validation code block (see "Integration" section above)
   - Handle interactive prompts with stdin check: `if sys.stdin.isatty()`

4. **Test:**
   - Run with skill that will fail (verify abort prompt)
   - Run with `--skip-preflight` (verify no validation)
   - Run with success and continue (verify batch proceeds)

### Step 2: Progress Monitoring (~3 hours)

1. **Add `monitor_progress()` function** (after `validate_skill()`, ~40 lines):
   ```python
   async def monitor_progress(results_list, total_tasks, monitor_interval, stop_event):
       """Background task reporting progress every N seconds."""
       start_time = datetime.now()

       while not stop_event.is_set():
           await asyncio.sleep(monitor_interval)
           if stop_event.is_set():
               break

           # Calculate metrics
           completed = len(results_list)
           if completed == 0:
               continue

           success = sum(1 for r in results_list if r["status"] == "success")
           errors = sum(1 for r in results_list if r["status"] == "error")
           timeouts = sum(1 for r in results_list if r["status"] == "timeout")
           success_rate = (success / completed * 100) if completed > 0 else 0
           runtime = (datetime.now() - start_time).total_seconds()
           runtime_str = f"{int(runtime // 60)}m {int(runtime % 60)}s"

           # Report
           print(f"\n[Progress] {completed}/{total_tasks} completed ({completed/total_tasks*100:.0f}%) | "
                 f"Success: {success}/{completed} ({success_rate:.0f}%) | "
                 f"Errors: {errors} | Timeouts: {timeouts} | "
                 f"Runtime: {runtime_str}")

           # Warning if no progress
           if completed == 0 and runtime > 300:
               print("   ⚠️  WARNING: No tasks completed after 5 minutes")
   ```

2. **Add CLI argument** (in `main()`, after preflight argument):
   ```python
   parser.add_argument(
       "--monitor-interval",
       type=int,
       default=120,
       help="Progress monitoring interval in seconds (default: 120, 0 to disable)"
   )
   ```

3. **Refactor worker execution** (in `main()`, replace line 301):
   - Add shared results list and stop event
   - Create monitor task
   - Wrap workers with collection function
   - Stop monitor after completion
   - (See "Integration" section above for full code)

4. **Test:**
   - Run long batch with default interval (verify reports every 2 min)
   - Run with `--monitor-interval 5` (verify faster updates)
   - Run with `--monitor-interval 0` (verify no monitoring)
   - Run fast batch (verify monitor exits gracefully)

### Step 3: Documentation (~1 hour)

1. **Update SKILL.md** (at `/Users/bianders/.claude/skills/batch-dispatch/SKILL.md`):
   - Add new options to "Options" section (line 59):
     ```markdown
     - `--skip-preflight`: Skip pre-flight validation on first item
     - `--monitor-interval SECONDS`: Progress update interval (default: 120, 0 to disable)
     ```

   - Add example showing new features (after line 80):
     ```markdown
     **With observability features:**
     ```bash
     /batch-dispatch catalog-scraper '["url1", "url2", "url3"]' "Scrape {{ item }}" --monitor-interval 60
     # Output:
     # --- Pre-flight Validation ---
     # Testing skill on first item: url1
     # ✅ Pre-flight PASSED
     # Sample: {"provider": "example", "courses": 42, ...}
     #
     # [Progress] 1/3 completed (33%) | Success: 1/1 (100%) | Runtime: 2m 15s
     # [Progress] 3/3 completed (100%) | Success: 3/3 (100%) | Runtime: 6m 42s
     ```
     ```

2. **Update README.md** (at `/Users/bianders/.claude/skills/batch-dispatch/references/README.md`):
   - Add "Observability Features" section
   - Document troubleshooting with monitoring output

---

## Edge Cases

### Pre-flight False Positives/Negatives
- **Issue:** First item passes but isn't representative
- **Handling:** Show preview output for user verification, allow skip with `--skip-preflight`

### Monitor During Fast Batches
- **Issue:** Batch completes before first interval
- **Handling:** Monitor checks `stop_event` before each report, exits gracefully

### Interactive Prompts in Scripts
- **Issue:** Pre-flight prompts break automated workflows
- **Handling:** Check `sys.stdin.isatty()`, auto-skip prompts if not TTY

### Stalled Workers
- **Issue:** All workers hang with no completion
- **Handling:** Monitor shows "⚠️ WARNING: No tasks completed after 5 minutes"

---

## Verification Plan

### Unit Tests (Optional)
```python
# tests/test_observability.py

async def test_validate_skill_success():
    """Verify preflight validation succeeds with valid skill."""
    success, result, preview = await validate_skill(
        item="test_input",
        skill_name="echo",  # Simple test skill
        user_template="Echo {{ item }}",
        timeout=60,
        run_id="test_run"
    )
    assert success == True
    assert "data" in result or result["status"] == "success"

async def test_monitor_progress_output():
    """Verify monitor produces expected output."""
    results = []
    stop = asyncio.Event()

    # Simulate completion
    async def add_results():
        await asyncio.sleep(0.5)
        results.append({"status": "success", "item": "a"})
        results.append({"status": "error", "item": "b"})
        await asyncio.sleep(0.5)
        stop.set()

    await asyncio.gather(
        monitor_progress(results, 2, 0.3, stop),
        add_results()
    )
    # Verify progress was printed (manual inspection or capture stdout)
```

### Manual Testing

**Test 1: Pre-flight catches errors**
```bash
cd /Users/bianders/Brian_Code/sandbox/scraping
python /Users/bianders/.claude/skills/batch-dispatch/references/batch_runner.py \
    nonexistent-skill \
    '["item1", "item2"]' \
    "Process {{ item }}" \
    --timeout 60

# Expected: Pre-flight fails, prompts to abort, exit code 1 if abort
```

**Test 2: Pre-flight success continues**
```bash
cd /Users/bianders/Brian_Code/sandbox/scraping
python /Users/bianders/.claude/skills/batch-dispatch/references/batch_runner.py \
    catalog-scraper \
    '["https://www.anthropic.com"]' \
    "Scrape course catalog from {{ item }}" \
    --timeout 300

# Expected: Pre-flight passes, shows preview, prompts to continue, batch runs
```

**Test 3: Monitor reports progress**
```bash
cd /Users/bianders/Brian_Code/sandbox/scraping
python /Users/bianders/.claude/skills/batch-dispatch/references/batch_runner.py \
    catalog-scraper \
    '["https://example1.com", "https://example2.com", "https://example3.com"]' \
    "Scrape {{ item }}" \
    --timeout 600 \
    --monitor-interval 10 \
    --skip-preflight

# Expected: Progress reports every 10 seconds showing completion counts
```

**Test 4: Skip features**
```bash
cd /Users/bianders/Brian_Code/sandbox/scraping
python /Users/bianders/.claude/skills/batch-dispatch/references/batch_runner.py \
    catalog-scraper \
    '["https://example.com"]' \
    "Scrape {{ item }}" \
    --skip-preflight \
    --monitor-interval 0

# Expected: No preflight, no monitoring, works like original version
```

### End-to-End Verification

Run a real catalog scraping batch with 3-5 providers:
1. Verify pre-flight catches invalid URLs or skill errors
2. Verify progress reports show increasing completion counts
3. Verify final output directory contains expected artifacts
4. Verify `summary.json` has correct success/error counts

**Success criteria:**
- Pre-flight detects configuration errors within 3-5 minutes
- Progress reports appear every 2 minutes
- No breaking changes to existing workflows
- Zero regressions in batch execution correctness

---

## Backward Compatibility

**Breaking changes:** NONE

**New defaults:**
- Monitoring enabled by default (`--monitor-interval 120`)
- Pre-flight enabled by default (can skip with `--skip-preflight`)

**Opt-out:**
- Disable monitoring: `--monitor-interval 0`
- Skip pre-flight: `--skip-preflight`

**Existing scripts:** Work unchanged (will see new preflight prompt unless stdin not TTY)

---

## Estimated Effort

- **Step 1 (Pre-flight):** 2 hours
- **Step 2 (Monitoring):** 3 hours
- **Step 3 (Documentation):** 1 hour
- **Testing/Polish:** 1 hour

**Total Phase 1:** ~7 hours

**Phase 2 (deferred):** ~8-10 hours additional for worker logging + fail-fast mode

---

## Success Metrics

After implementation:
- ✅ Configuration errors detected within 20 minutes (vs 2+ hours)
- ✅ User knows within 5 minutes if workers are producing output
- ✅ Can abort early if pre-flight fails (saves API credits)
- ✅ Zero breaking changes to existing batch-dispatch users
- ✅ Clear path to Phase 2/3 features via established patterns
