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

# ── AC-I2 ─────────────────────────────────────────────────────────────────────

def test_search_text_mode():
    """AC-I2: --text flag returns text field, no highlights field."""
    code, data, stderr = run_exa("search", "introduction to transformers", "--text")
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert stderr is None
    assert len(data["results"]) > 0
    for result in data["results"]:
        assert "text" in result, f"Missing 'text' in result: {result}"
        assert isinstance(result["text"], str)
        assert "highlights" not in result, f"'highlights' must not appear in text mode: {result}"

# ── AC-I3 ─────────────────────────────────────────────────────────────────────

def test_search_num_results_respected():
    """AC-I3: --num-results 3 returns at most 3 results."""
    code, data, stderr = run_exa("search", "machine learning", "--num-results", "3")
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert len(data["results"]) <= 3, (
        f"Expected at most 3 results, got {len(data['results'])}"
    )

# ── AC-I4 ─────────────────────────────────────────────────────────────────────

def test_contents_returns_url_and_failed_urls():
    """AC-I4: exa contents returns matching URL result and failed_urls key."""
    target = "https://arxiv.org/abs/2307.06435"
    code, data, stderr = run_exa("contents", target)
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert "failed_urls" in data, "Output must always contain 'failed_urls' key"
    assert isinstance(data["failed_urls"], list)
    # At least one result should match the requested URL (or it's in failed_urls)
    urls_returned = [r["url"] for r in data["results"]]
    assert target in urls_returned or target in data["failed_urls"], (
        f"{target} not in results or failed_urls"
    )

# ── AC-I5 ─────────────────────────────────────────────────────────────────────

def test_similar_returns_bounded_results():
    """AC-I5: exa similar returns at most --num-results results."""
    code, data, stderr = run_exa(
        "similar", "https://arxiv.org/abs/2307.06435", "--num-results", "5"
    )
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert "results" in data
    assert len(data["results"]) > 0, "Expected at least one similar result"
    assert len(data["results"]) <= 5, (
        f"Expected at most 5 results, got {len(data['results'])}"
    )

# ── AC-I6 ─────────────────────────────────────────────────────────────────────

def test_answer_returns_string_and_citations():
    """AC-I6: exa answer returns answer (str) and citations (list)."""
    code, data, stderr = run_exa("answer", "What is 2+2?")
    assert code == 0, f"Expected exit 0, got {code}. stderr: {stderr}"
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0, "Exa should return a non-empty answer for 'What is 2+2?'"
    assert "citations" in data
    assert isinstance(data["citations"], list)
