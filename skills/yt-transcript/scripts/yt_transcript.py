"""
YouTube transcript fetcher wrapping youtube-transcript-api v1.2.4+.

No auth required. No API key needed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

if TYPE_CHECKING:
    pass

_VIDEO_ID_RE = re.compile(r"[A-Za-z0-9_-]{11}")
_PATTERNS = [
    re.compile(r"[?&]v=([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"embed/([A-Za-z0-9_-]{11})"),
]

_api = YouTubeTranscriptApi()


def extract_video_id(url_or_id: str) -> str:
    """
    Extract the 11-character video ID from any common YouTube URL format,
    or pass through a bare video ID.

    Supported formats:
      youtube.com/watch?v=<id>
      youtu.be/<id>
      youtube.com/embed/<id>
      bare 11-char ID
    """
    for pattern in _PATTERNS:
        m = pattern.search(url_or_id)
        if m:
            return m.group(1)
    if _VIDEO_ID_RE.fullmatch(url_or_id):
        return url_or_id
    raise ValueError(f"Cannot extract video ID from: {url_or_id!r}")


@dataclass
class Snippet:
    text: str
    start: float
    duration: float


@dataclass
class Transcript:
    video_id: str
    language: str
    language_code: str
    is_generated: bool
    snippets: list[Snippet]

    @property
    def text(self) -> str:
        """Full transcript as a single space-joined string."""
        return " ".join(s.text for s in self.snippets)


@dataclass
class TranscriptMeta:
    language: str
    language_code: str
    is_generated: bool
    is_translatable: bool


def list_transcripts(url_or_id: str) -> list[TranscriptMeta]:
    """
    Return metadata for all available transcripts for a video.

    Manually created transcripts are listed before auto-generated ones.
    """
    video_id = extract_video_id(url_or_id)
    tl = _api.list(video_id)
    results: list[TranscriptMeta] = []
    # manually created first
    for t in tl._manually_created_transcripts.values():
        results.append(TranscriptMeta(
            language=t.language,
            language_code=t.language_code,
            is_generated=False,
            is_translatable=t.is_translatable,
        ))
    for t in tl._generated_transcripts.values():
        results.append(TranscriptMeta(
            language=t.language,
            language_code=t.language_code,
            is_generated=True,
            is_translatable=t.is_translatable,
        ))
    return results


def get_transcript(
    url_or_id: str,
    languages: list[str] | None = None,
    prefer_manual: bool = True,
) -> Transcript:
    """
    Fetch the transcript for a video.

    Args:
        url_or_id: YouTube URL or bare 11-char video ID.
        languages: Preferred language codes in priority order. Defaults to ['en'].
        prefer_manual: If True, try manually created transcripts before
            auto-generated ones (within the requested languages). Falls back to
            auto-generated if no manual transcript exists.

    Returns:
        Transcript with .snippets (timestamped) and .text (plain concatenated).

    Raises:
        ValueError: Invalid URL or video ID.
        TranscriptsDisabled: Video has transcripts disabled.
        NoTranscriptFound: No transcript in the requested language(s).
        VideoUnavailable: Video does not exist or is private.
    """
    video_id = extract_video_id(url_or_id)
    langs = languages or ["en"]

    if prefer_manual:
        try:
            tl = _api.list(video_id)
            fetched = tl.find_manually_created_transcript(langs).fetch()
        except NoTranscriptFound:
            fetched = _api.fetch(video_id, languages=langs)
    else:
        fetched = _api.fetch(video_id, languages=langs)

    return Transcript(
        video_id=video_id,
        language=fetched.language,
        language_code=fetched.language_code,
        is_generated=fetched.is_generated,
        snippets=[
            Snippet(text=s.text, start=s.start, duration=s.duration)
            for s in fetched.snippets
        ],
    )
