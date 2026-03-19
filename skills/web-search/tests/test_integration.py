from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pytest

from conftest import run_exa

# All tests in this file require a live EXA_API_KEY.
pytestmark = pytest.mark.skipif(
    not os.getenv("EXA_API_KEY"),
    reason="EXA_API_KEY not set — skipping integration tests",
)


# ── AC-I1 ─────────────────────────────────────────────────────────────────────

def test_search_highlights_mode():
    """AC-I1: search returns results with url+highlights, no text key."""
    code, data, stderr = run_exa(
        "search", "papers on RLHF and calibration", "--category", "research paper"
    )
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert stderr is None
    assert "results" in data
    assert len(data["results"]) > 0, "Expected at least one result"
    for result in data["results"]:
        assert "url" in result, f"Missing 'url' in result: {result}"
        assert isinstance(result["url"], str)
        assert "highlights" in result, f"Missing 'highlights' in result: {result}"
        assert isinstance(result["highlights"], list)
        assert "text" not in result, f"'text' must not appear in highlights mode: {result}"
