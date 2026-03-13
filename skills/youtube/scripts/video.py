from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _models import Transcript

logger = logging.getLogger("youtube")


def extract_video_id(url_or_id: str) -> str:
    from _util import extract_video_id as _extract
    return _extract(url_or_id)


def get_transcript(url_or_id: str, **kwargs) -> "Transcript":
    raise NotImplementedError("get_transcript is implemented in Task 6")


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
