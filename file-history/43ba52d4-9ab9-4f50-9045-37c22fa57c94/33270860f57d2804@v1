# /// script
# dependencies = [
#   "jinja2",
# ]
# ///

import asyncio
import sys
import json
import os
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from jinja2 import Template

# --- DEFAULTS ---
DEFAULT_MAX_WORKERS = 5
DEFAULT_TIMEOUT = 600
BATCH_DIR_NAME = "batch_runs"


def check_sandbox_enabled():
    """
    Check if Claude Code sandboxing is enabled.
    Returns True if sandbox mode is active, False otherwise.
    """
    try:
        # Check for sandbox configuration in settings
        settings_path = Path.home() / ".claude" / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
                # Check if sandbox is configured
                if "sandbox" in settings:
                    return True
        return False
    except Exception:
        return False


async def run_worker(sem, run_id, index, item, skill_name, user_template, timeout):
    """
    Spawns a single isolated Claude Code instance.
    """
    async with sem:
        # 1. Setup Isolation
        # We create a folder, but we DO NOT change the CWD of the subprocess.
        # This ensures Claude still sees .claude/config.toml and project-level skills.
        task_dir = os.path.abspath(
            os.path.join(BATCH_DIR_NAME, run_id, f"task_{index}")
        )
        os.makedirs(task_dir, exist_ok=True)

        output_file = os.path.join(task_dir, "result.json")

        # 2. Render Prompt
        # We inject strict instructions about where to write.
        system_instructions = (
            f"SYSTEM OVERRIDE: You are a headless worker agent. "
            f"You are restricted to working strictly within this directory: {task_dir}. "
            f"You have permission to use the '{skill_name}' tool. "
            f"Do not ask for confirmation. Do not output conversational filler. "
            f"Perform the task and save the final structured data to: {output_file}."
        )

        try:
            # Jinja2 rendering for the user's specific task
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

        # 3. Construct Command
        # Use Claude Code directly - native sandboxing will restrict to task_dir
        cmd = ["claude", "-p", full_prompt, "--dangerously-skip-permissions"]

        print(f"[{index}] Starting task for: {item} (🔒 Sandboxed to {task_dir})...")

        try:
            # 4. Execute with task_dir as working directory
            # Claude's sandbox will restrict filesystem writes to this directory
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=task_dir,  # Critical: Sets working directory for sandbox
            )

            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            # 5. Harvest Results
            if process.returncode == 0:
                # Check if the output file actually exists
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
                        print(f"[{index}] Failed: Output was not valid JSON.")
                        return {
                            "status": "error",
                            "item": item,
                            "error": "Invalid JSON in output file",
                            "task_dir": task_dir,
                        }
                else:
                    print(f"[{index}] Failed: No output file found.")
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
                    "error": stderr.decode(),
                    "task_dir": task_dir,
                }

        except asyncio.TimeoutError:
            print(f"[{index}] Timed out after {timeout}s. Killing.")
            try:
                process.kill()
            except:
                pass
            return {"status": "timeout", "item": item, "task_dir": task_dir}


def cleanup_and_finalize(run_id, run_dir, results):
    """
    Move artifacts to output directory in CWD and clean up temp directories.
    """
    cwd = os.getcwd()
    output_dir = os.path.join(cwd, f"batch_results_{run_id}")
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n--- Cleanup & Finalize ---")
    print(f"Moving artifacts to: {output_dir}")

    moved_count = 0
    for result in results:
        if result["status"] == "success" and "task_dir" in result:
            task_dir = result["task_dir"]
            # Move all files except result.json and .py scripts
            if os.path.exists(task_dir):
                for filename in os.listdir(task_dir):
                    if filename.endswith((".json", ".xlsx", ".md", ".csv")):
                        if filename != "result.json":  # Skip the internal result file
                            src = os.path.join(task_dir, filename)
                            dst = os.path.join(output_dir, filename)
                            shutil.copy2(src, dst)
                            moved_count += 1

    # Save summary to output directory
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Moved {moved_count} artifact files")
    print(f"Summary saved to: {summary_path}")

    # Delete temp batch_runs directory
    try:
        shutil.rmtree(BATCH_DIR_NAME)
        print(f"Cleaned up temp directory: {BATCH_DIR_NAME}/")
    except Exception as e:
        print(f"Warning: Could not delete temp directory: {e}")

    return output_dir


def check_and_warn_sandbox():
    """
    Check sandbox configuration immediately and provide clear setup instructions.
    Returns True if should continue, False if should exit.
    """
    sandbox_enabled = check_sandbox_enabled()

    if not sandbox_enabled:
        print("\n" + "="*70)
        print("⚠️  SECURITY WARNING: Claude Code Sandboxing Not Enabled")
        print("="*70)
        print("\n🔒 Sandboxing protects your filesystem during batch execution.")
        print("   Without it, workers have full access to all your files.\n")
        print("📋 To enable sandboxing (one-time setup):\n")
        print("   1. In Claude Code, run this command:")
        print("      > /sandbox\n")
        print("   2. Choose: 'Auto-allow mode'")
        print("      (This auto-approves sandboxed commands)\n")
        print("   3. Restart batch-dispatch\n")
        print("ℹ️  Or run with --skip-sandbox-check to proceed anyway (NOT RECOMMENDED)\n")
        print("="*70 + "\n")
        return False

    return True


async def main():
    parser = argparse.ArgumentParser(
        description="Batch dispatch: Run a skill in parallel across multiple inputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (uses Claude Code's native sandboxing)
  batch_runner.py catalog-scraper '["url1", "url2"]' "Scrape {{ item }}"

  # With custom timeout (10 minutes)
  batch_runner.py catalog-scraper '["url1", "url2"]' "Scrape {{ item }}" --timeout 600

  # With custom concurrency (limit to 3 parallel workers)
  batch_runner.py my-skill '["a", "b", "c"]' "Process {{ item }}" --max-workers 3

Note: Requires Claude Code sandboxing to be enabled. Run /sandbox to configure.
        """,
    )
    parser.add_argument("skill", help="Name of the skill to execute")
    parser.add_argument(
        "inputs", help='JSON array of inputs (e.g., \'["url1", "url2"]\')'
    )
    parser.add_argument("template", help="Jinja2 template for task instructions")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout per task in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Maximum concurrent workers (default: {DEFAULT_MAX_WORKERS})",
    )
    parser.add_argument(
        "--skip-sandbox-check",
        action="store_true",
        help="Skip checking if Claude Code sandboxing is enabled (not recommended)",
    )

    args = parser.parse_args()

    # Check sandboxing IMMEDIATELY (unless explicitly skipped)
    if not args.skip_sandbox_check:
        if not check_and_warn_sandbox():
            sys.exit(1)

    try:
        inputs = json.loads(args.inputs)
        if not isinstance(inputs, list):
            print("Error: Inputs must be a JSON array")
            sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in inputs: {e}")
        sys.exit(1)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(BATCH_DIR_NAME, run_id)
    os.makedirs(run_dir, exist_ok=True)

    print(f"--- Batch Dispatch Initiated ---")
    print(f"Run ID: {run_id}")
    print(f"Items: {len(inputs)}")
    print(f"Skill: {args.skill}")
    print(f"Timeout: {args.timeout}s per task")
    print(f"Max Workers: {args.max_workers}")
    print(f"Isolation: 🔒 Claude Code Sandbox")

    sem = asyncio.Semaphore(args.max_workers)

    tasks = [
        run_worker(sem, run_id, i, item, args.skill, args.template, args.timeout)
        for i, item in enumerate(inputs)
    ]

    # Run all
    results = await asyncio.gather(*tasks)

    # Count successes/failures
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    timeout_count = sum(1 for r in results if r["status"] == "timeout")

    print(f"\n--- Batch Job Complete ---")
    print(f"Success: {success_count}/{len(inputs)}")
    if error_count > 0:
        print(f"Errors: {error_count}")
    if timeout_count > 0:
        print(f"Timeouts: {timeout_count}")

    # Cleanup and finalize
    output_dir = cleanup_and_finalize(run_id, run_dir, results)

    print(f"\nFinal output directory: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
