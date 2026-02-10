# /// script
# dependencies = [
#    "jinja2",
# ]
# ///

import asyncio
import sys
import json
import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from jinja2 import Template

DEFAULT_MAX_WORKERS = 5
DEFAULT_TIMEOUT = 600
BATCH_DIR_NAME = "batch_runs"


def check_sandbox_enabled():
    """
    Check if Claude Code sandboxing is enabled via Env Var or Settings.
    """
    # First check environment variable (most reliable in subprocesses)
    if os.getenv("CLAUDE_SANDBOX") == "1":
        return True

    try:
        settings_path = Path.home() / ".claude" / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
                return "sandbox" in settings
        return False
    except Exception:
        return False


async def run_worker(sem, run_id, index, item, skill_name, user_template, timeout):
    """
    Spawns a single isolated Claude Code instance with private cache.
    """
    async with sem:
        task_dir = os.path.abspath(
            os.path.join(BATCH_DIR_NAME, run_id, f"task_{index}")
        )
        os.makedirs(task_dir, exist_ok=True)

        # FIX: Isolate UV cache to prevent 'Operation not permitted' on global cache locks
        worker_cache = os.path.join(task_dir, ".uv_cache")
        os.makedirs(worker_cache, exist_ok=True)

        output_file = os.path.join(task_dir, "result.json")

        system_instructions = (
            f"SYSTEM OVERRIDE: You are a headless worker agent. "
            f"You are restricted to working strictly within this directory: {task_dir}. "
            f"You MUST invoke the '{skill_name}' skill using the Skill tool to complete this task. "
            f"Use the syntax: /{skill_name} with the task-specific arguments. "
            f"Do not ask for confirmation. Do not output conversational filler. "
            f"Perform the task and save the final structured data to: {output_file}."
        )

        try:
            t = Template(user_template)
            task_prompt = t.render(item=item, task_id=index, output_file=output_file)
        except Exception as e:
            return {
                "status": "error",
                "item": item,
                "error": f"Template Error: {str(e)}",
                "task_dir": task_dir,
            }

        full_prompt = (
            f"{system_instructions}\n\nTASK INPUT: {item}\nINSTRUCTIONS: {task_prompt}"
        )

        # Inherit env and force private UV cache
        env = os.environ.copy()
        env["UV_CACHE_DIR"] = worker_cache

        # FIX: Remove API key so Claude falls back to stored credentials (work account)
        env.pop("ANTHROPIC_API_KEY", None)

        cmd = ["claude", "-p", full_prompt, "--dangerously-skip-permissions"]

        print(f"[{index}] Starting task for: {item} (🔒 Sandboxed to {task_dir})...")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=task_dir,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            if process.returncode == 0:
                if os.path.exists(output_file):
                    try:
                        with open(output_file, "r") as f:
                            data = json.load(f)
                        print(f"[{index}] Success.")
                        return {
                            "status": "success",
                            "item": item,
                            "data": data,
                            "task_dir": task_dir,
                        }
                    except json.JSONDecodeError:
                        return {
                            "status": "error",
                            "item": item,
                            "error": "Invalid JSON in output file",
                            "task_dir": task_dir,
                        }
                else:
                    return {
                        "status": "error",
                        "item": item,
                        "error": "Output file missing",
                        "logs": stdout.decode(),
                        "task_dir": task_dir,
                    }
            else:
                print(f"[{index}] Crushed (Exit Code {process.returncode}).")
                return {
                    "status": "error",
                    "item": item,
                    "error": stderr.decode() or stdout.decode(),
                    "task_dir": task_dir,
                }

        except asyncio.TimeoutError:
            print(f"[{index}] Timed out after {timeout}s. Killing.")
            try:
                process.kill()
            except:
                pass
            return {"status": "timeout", "item": item, "task_dir": task_dir}


async def validate_skill(item, skill_name, user_template, timeout, run_id):
    preflight_dir = os.path.abspath(os.path.join(BATCH_DIR_NAME, run_id, "preflight"))
    os.makedirs(preflight_dir, exist_ok=True)

    print(f"\n--- Pre-flight Validation ---")
    print(f"Testing skill on first item: {item}")

    sem = asyncio.Semaphore(1)
    result = await run_worker(sem, run_id, 0, item, skill_name, user_template, timeout)

    success = result["status"] == "success"
    if success:
        data_str = json.dumps(result.get("data", {}), indent=2)
        preview = data_str[:500] + ("..." if len(data_str) > 500 else "")
    else:
        preview = str(result.get("error", "Unknown error"))[:500]

    return (success, result, preview)


async def monitor_progress(results_list, total_tasks, monitor_interval, stop_event):
    start_time = datetime.now()
    while not stop_event.is_set():
        await asyncio.sleep(monitor_interval)
        completed = len(results_list)
        if completed == 0:
            continue

        success = sum(1 for r in results_list if r["status"] == "success")
        runtime = (datetime.now() - start_time).total_seconds()
        print(
            f"\n[Progress] {completed}/{total_tasks} completed | Success: {success} | Time: {int(runtime)}s"
        )


def cleanup_and_finalize(run_id, run_dir, results):
    output_dir = os.path.join(os.getcwd(), f"batch_results_{run_id}")
    os.makedirs(output_dir, exist_ok=True)

    for result in results:
        if result["status"] == "success" and "task_dir" in result:
            task_dir = result["task_dir"]
            for filename in os.listdir(task_dir):
                if (
                    filename.endswith((".json", ".xlsx", ".md", ".csv"))
                    and filename != "result.json"
                ):
                    shutil.copy2(
                        os.path.join(task_dir, filename),
                        os.path.join(output_dir, filename),
                    )

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(results, f, indent=2)

    shutil.rmtree(BATCH_DIR_NAME, ignore_errors=True)
    return output_dir


async def main():
    parser = argparse.ArgumentParser(
        description="Batch dispatch: Parallel skill execution"
    )
    parser.add_argument("skill")
    parser.add_argument("inputs")
    parser.add_argument("template")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-workers", type=int, default=DEFAULT_MAX_WORKERS)
    parser.add_argument("--skip-sandbox-check", action="store_true")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--monitor-interval", type=int, default=30)

    args = parser.parse_args()

    if not args.skip_sandbox_check and not check_sandbox_enabled():
        print("Error: Claude Code Sandboxing Not Enabled. Run /sandbox first.")
        sys.exit(1)

    inputs = json.loads(args.inputs)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(os.path.join(BATCH_DIR_NAME, run_id), exist_ok=True)

    if not args.skip_preflight:
        success, _, preview = await validate_skill(
            inputs[0], args.skill, args.template, args.timeout, run_id
        )
        if not success:
            print(f"Pre-flight FAILED: {preview}")
            sys.exit(1)

    sem = asyncio.Semaphore(args.max_workers)
    results_list = []
    stop_monitor = asyncio.Event()

    monitor_task = asyncio.create_task(
        monitor_progress(results_list, len(inputs), args.monitor_interval, stop_monitor)
    )

    async def worker_wrapper(i, item):
        res = await run_worker(
            sem, run_id, i, item, args.skill, args.template, args.timeout
        )
        results_list.append(res)
        return res

    results = await asyncio.gather(
        *(worker_wrapper(i, item) for i, item in enumerate(inputs))
    )

    stop_monitor.set()
    await monitor_task

    output_dir = cleanup_and_finalize(run_id, None, results)
    print(f"\nFinal output directory: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
