from __future__ import annotations

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))


def test_search_transcript_empty_query_raises():
    from video import search_transcript
    with pytest.raises(ValueError, match="query must not be empty"):
        search_transcript("dQw4w9WgXcQ", "")


def test_search_transcript_returns_matching_snippets(mocker):
    from _models import Transcript, Snippet
    from video import search_transcript

    mock_transcript = Transcript(
        language="English",
        language_code="en",
        is_generated=False,
        source="caption",
        snippets=[
            Snippet(text="Backpropagation is a key algorithm", start=10.0, duration=3.0),
            Snippet(text="gradient descent in neural nets", start=14.0, duration=2.5),
            Snippet(text="BACKPROPAGATION computes gradients", start=20.0, duration=3.0),
        ],
        text="Backpropagation is a key algorithm gradient descent in neural nets BACKPROPAGATION computes gradients",
    )
    mocker.patch("video.get_transcript", return_value=mock_transcript)

    hits = search_transcript("dQw4w9WgXcQ", "backpropagation")
    assert len(hits) == 2
    assert hits[0].start == 10.0
    assert hits[1].start == 20.0


def test_search_transcript_no_match_returns_empty(mocker):
    from _models import Transcript, Snippet
    from video import search_transcript

    mock_transcript = Transcript(
        language="English",
        language_code="en",
        is_generated=False,
        source="caption",
        snippets=[Snippet(text="hello world", start=0.0, duration=1.0)],
        text="hello world",
    )
    mocker.patch("video.get_transcript", return_value=mock_transcript)

    hits = search_transcript("dQw4w9WgXcQ", "eigenvalue")
    assert hits == []
