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


def _make_ydl_mock(mocker, info):
    mock_ydl = mocker.MagicMock()
    mock_ydl.extract_info.return_value = info
    mock_ydl.__enter__ = mocker.MagicMock(return_value=mock_ydl)
    mock_ydl.__exit__ = mocker.MagicMock(return_value=False)
    return mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)


def test_get_chapters_parses_standard_format(mocker):
    from video import get_chapters

    description = (
        "A great video about math.\n\n"
        "0:00 Introduction\n"
        "3:45 Main concept\n"
        "10:22 Conclusion\n"
    )
    _make_ydl_mock(mocker, {"description": description})

    chapters = get_chapters("dQw4w9WgXcQ")
    assert len(chapters) == 3
    assert chapters[0].title == "Introduction"
    assert chapters[0].start == 0.0
    assert chapters[1].title == "Main concept"
    assert abs(chapters[1].start - 225.0) < 0.01  # 3*60 + 45


def test_get_chapters_returns_empty_when_no_chapters(mocker):
    from video import get_chapters

    _make_ydl_mock(mocker, {"description": "Just a video with no chapters here."})

    assert get_chapters("dQw4w9WgXcQ") == []


def test_transcribe_whisper_deletes_temp_audio_on_success(mocker, tmp_path):
    from video import transcribe_whisper

    audio_file = tmp_path / "youtube" / "tmp" / "dQw4w9WgXcQ.m4a"
    audio_file.parent.mkdir(parents=True, exist_ok=True)
    audio_file.write_text("fake audio")

    mocker.patch("video._download_audio", return_value=audio_file)

    mock_seg = mocker.MagicMock()
    mock_seg.text = "hello"
    mock_seg.start = 0.0
    mock_seg.end = 1.0
    mock_info_obj = mocker.MagicMock()
    mock_info_obj.language = "en"
    mock_model = mocker.MagicMock()
    mock_model.transcribe.return_value = ([mock_seg], mock_info_obj)
    mocker.patch("faster_whisper.WhisperModel", return_value=mock_model)

    transcribe_whisper("dQw4w9WgXcQ")
    assert not audio_file.exists()


def test_transcribe_whisper_deletes_temp_audio_on_failure(mocker, tmp_path):
    from video import transcribe_whisper

    audio_file = tmp_path / "youtube" / "tmp" / "dQw4w9WgXcQ.m4a"
    audio_file.parent.mkdir(parents=True, exist_ok=True)
    audio_file.write_text("fake audio")

    mocker.patch("video._download_audio", return_value=audio_file)
    mocker.patch("faster_whisper.WhisperModel", side_effect=RuntimeError("model error"))

    with pytest.raises(Exception):
        transcribe_whisper("dQw4w9WgXcQ")

    assert not audio_file.exists()
