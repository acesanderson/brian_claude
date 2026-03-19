from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conftest import run_exa

SKILL_DIR = Path(__file__).parent.parent


# ── AC-U9 ─────────────────────────────────────────────────────────────────────

def test_help_exits_zero():
    """AC-U9: uv run ... python exa.py --help exits 0."""
    result = subprocess.run(
        [sys.executable, str(SKILL_DIR / "exa.py"), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


# ── AC-U8 ─────────────────────────────────────────────────────────────────────

def test_no_fetch_tools_import():
    """AC-U8: exa.py must not import fetch_tools."""
    exa_source = (SKILL_DIR / "exa.py").read_text()
    assert "fetch_tools" not in exa_source


# ── AC-U1 ─────────────────────────────────────────────────────────────────────

def test_missing_api_key_search():
    """AC-U1: EXA_API_KEY unset on any subcommand → exit 1, structured error."""
    code, stdout, stderr = run_exa("search", "test query", unset_keys=["EXA_API_KEY"])
    assert code == 1
    assert stdout is None
    assert stderr == {"error": "Missing EXA_API_KEY environment variable"}


# ── AC-U5 ─────────────────────────────────────────────────────────────────────

def test_text_highlights_mutually_exclusive_search():
    """AC-U5: --text and --highlights together on 'search' → exit 1."""
    code, stdout, stderr = run_exa("search", "test", "--text", "--highlights")
    assert code == 1
    assert stdout is None
    assert stderr == {"error": "--text and --highlights are mutually exclusive"}


def test_text_highlights_mutually_exclusive_contents():
    """AC-U5: --text and --highlights together on 'contents' → exit 1."""
    code, stdout, stderr = run_exa(
        "contents", "https://example.com", "--text", "--highlights",
        set_keys={"EXA_API_KEY": "dummy_key_for_testing"},
    )
    assert code == 1
    assert stderr == {"error": "--text and --highlights are mutually exclusive"}


def test_text_highlights_mutually_exclusive_similar():
    """AC-U5: --text and --highlights together on 'similar' → exit 1."""
    code, stdout, stderr = run_exa(
        "similar", "https://example.com", "--text", "--highlights",
        set_keys={"EXA_API_KEY": "dummy_key_for_testing"},
    )
    assert code == 1
    assert stderr == {"error": "--text and --highlights are mutually exclusive"}
