from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL_DIR = Path(__file__).parent.parent


def run_exa(
    *args: str,
    unset_keys: list[str] | None = None,
    set_keys: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | None, dict[str, Any] | None]:
    """Run exa.py via subprocess.

    Returns (returncode, stdout_parsed, stderr_parsed).
    stdout_parsed / stderr_parsed are None if the stream was empty.
    """
    env = os.environ.copy()
    for key in (unset_keys or []):
        env.pop(key, None)
    env.update(set_keys or {})

    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "exa.py"), *args],
        capture_output=True,
        text=True,
        env=env,
    )
    stdout = json.loads(result.stdout) if result.stdout.strip() else None
    stderr = json.loads(result.stderr) if result.stderr.strip() else None
    return result.returncode, stdout, stderr
