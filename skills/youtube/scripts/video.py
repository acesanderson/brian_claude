from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _models import Transcript

logger = logging.getLogger("youtube")


def extract_video_id(url_or_id: str) -> str:
    from _util import extract_video_id as _extract
    return _extract(url_or_id)


def get_transcript(
    url_or_id: str,
    languages: list[str] | None = None,
    prefer_manual: bool = True,
    fallback_whisper: bool = False,
) -> "Transcript":
    from youtube_transcript_api import (
        TranscriptsDisabled,
        NoTranscriptFound,
        YouTubeTranscriptApi,
    )
    from _models import Transcript, Snippet
    from _util import extract_video_id
    from _cache import get_transcript_cache, set_transcript_cache

    if languages is not None and fallback_whisper:
        raise ValueError(
            "languages and fallback_whisper are mutually exclusive: "
            "Whisper transcribes the video's spoken language, not a requested language"
        )

    video_id = extract_video_id(url_or_id)
    use_cache = languages is None

    if use_cache:
        cached = get_transcript_cache(video_id)
        if cached:
            logger.debug("transcript cache hit for %s", video_id)
            return Transcript(
                language=cached["language"],
                language_code=cached["language_code"],
                is_generated=cached["is_generated"],
                source="caption",
                snippets=[
                    Snippet(text=s["text"], start=s["start"], duration=s["duration"])
                    for s in cached["snippets"]
                ],
                text=cached["text"],
            )
        logger.debug("transcript cache miss for %s", video_id)

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        if prefer_manual:
            try:
                t = transcript_list.find_manually_created_transcript(
                    languages or ["en"]
                )
            except NoTranscriptFound:
                t = transcript_list.find_generated_transcript(languages or ["en"])
        else:
            t = transcript_list.find_transcript(languages or ["en"])

        fetched = t.fetch()
        snippets = [
            Snippet(text=s.text, start=s.start, duration=s.duration)
            for s in fetched.snippets
        ]
        transcript = Transcript(
            language=fetched.language,
            language_code=fetched.language_code,
            is_generated=fetched.is_generated,
            source="caption",
            snippets=snippets,
            text=" ".join(s.text for s in snippets),
        )

        if use_cache:
            set_transcript_cache(video_id, {
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "snippets": [
                    {"text": s.text, "start": s.start, "duration": s.duration}
                    for s in snippets
                ],
                "text": transcript.text,
            })

        return transcript

    except (TranscriptsDisabled, NoTranscriptFound):
        if fallback_whisper:
            logger.warning(
                "caption unavailable; falling back to Whisper for %s", video_id
            )
            return transcribe_whisper(url_or_id)
        raise


def transcribe_whisper(url_or_id: str) -> "Transcript":
    raise NotImplementedError("transcribe_whisper is implemented in Task 8")


def search_transcript(url_or_id: str, query: str) -> list:
    from _models import TranscriptHit
    if not query:
        raise ValueError("query must not be empty")
    transcript = get_transcript(url_or_id)
    lower_query = query.lower()
    return [
        TranscriptHit(start=s.start, text=s.text)
        for s in transcript.snippets
        if lower_query in s.text.lower()
    ]
