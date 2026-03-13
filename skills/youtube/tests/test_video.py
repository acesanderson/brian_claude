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


def test_get_transcript_languages_and_fallback_whisper_raises():
    from video import get_transcript
    with pytest.raises(ValueError, match="mutually exclusive"):
        get_transcript("dQw4w9WgXcQ", languages=["fr"], fallback_whisper=True)


def test_get_transcript_uses_cache_on_second_call(mocker, tmp_path, monkeypatch):
    import _cache
    monkeypatch.setattr(_cache, "CACHE_DIR", tmp_path)

    from youtube_transcript_api._transcripts import FetchedTranscriptSnippet, FetchedTranscript

    snippet = FetchedTranscriptSnippet(text="hello", start=0.0, duration=1.0)
    fetched = FetchedTranscript(
        snippets=[snippet],
        video_id="dQw4w9WgXcQ",
        language="English",
        language_code="en",
        is_generated=False,
    )
    mock_t = mocker.MagicMock()
    mock_t.fetch.return_value = fetched

    mock_list = mocker.MagicMock()
    mock_list.find_manually_created_transcript.return_value = mock_t

    mock_api_instance = mocker.MagicMock()
    mock_api_instance.list.return_value = mock_list

    mocker.patch("youtube_transcript_api.YouTubeTranscriptApi", return_value=mock_api_instance)

    from video import get_transcript
    get_transcript("dQw4w9WgXcQ")
    get_transcript("dQw4w9WgXcQ")

    assert mock_api_instance.list.call_count == 1  # network called only once
