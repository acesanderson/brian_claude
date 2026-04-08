from __future__ import annotations

import logging
import re as _re
from pathlib import Path as _Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _models import Transcript

logger = logging.getLogger("youtube")


class WhisperTranscriptionError(Exception):
    pass


def extract_video_id(url_or_id: str) -> str:
    from _util import extract_video_id as _extract
    return _extract(url_or_id)


def get_transcript(
    url_or_id: str,
    languages: list[str] | None = None,
    prefer_manual: bool = True,
    fallback_whisper: bool = False,
    proxy_config=None,
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
        api = YouTubeTranscriptApi(proxy_config=proxy_config)
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


def get_chapters(url_or_id: str) -> list:
    import yt_dlp
    from _models import Chapter
    from _util import extract_video_id

    video_id = extract_video_id(url_or_id)
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    description = (info or {}).get("description", "") or ""

    pattern = _re.compile(r"^(\d+:\d{2}(?::\d{2})?)\s+(.+)$", _re.MULTILINE)

    chapters = []
    for m in pattern.finditer(description):
        timestamp, title = m.group(1), m.group(2).strip()
        parts = timestamp.split(":")
        if len(parts) == 2:
            start = int(parts[0]) * 60 + int(parts[1])
        else:
            start = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        chapters.append(Chapter(title=title, start=float(start)))

    return chapters


def _download_audio(video_id: str) -> _Path:
    import yt_dlp
    tmp_dir = _Path.home() / ".cache" / "youtube" / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(tmp_dir / f"{video_id}.%(ext)s")
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = info.get("ext", "m4a")

    result = tmp_dir / f"{video_id}.{ext}"
    logger.debug("temp audio file created: %s", result)
    return result


def transcribe_whisper(url_or_id: str, model: str = "small") -> "Transcript":
    import faster_whisper
    from _models import Transcript, Snippet
    from _util import extract_video_id

    video_id = extract_video_id(url_or_id)
    logger.warning(
        "starting Whisper transcription for %s (model=%s); this may be slow",
        video_id, model,
    )

    audio_path = _download_audio(video_id)
    try:
        whisper_model = faster_whisper.WhisperModel(model)
        segments, info = whisper_model.transcribe(str(audio_path))
        snippets = [
            Snippet(text=seg.text.strip(), start=seg.start, duration=seg.end - seg.start)
            for seg in segments
        ]
        return Transcript(
            language=info.language,
            language_code=info.language,
            is_generated=False,
            source="whisper",
            snippets=snippets,
            text=" ".join(s.text for s in snippets),
        )
    except Exception as exc:
        raise WhisperTranscriptionError(
            f"Whisper transcription failed for {video_id}: {exc}"
        ) from exc
    finally:
        if audio_path.exists():
            audio_path.unlink()
            logger.debug("temp audio file deleted: %s", audio_path)
        else:
            logger.error("temp audio file not found for cleanup: %s", audio_path)


def get_metadata(url_or_id: str) -> "VideoMetadata":
    import yt_dlp
    from _models import VideoMetadata
    from _util import extract_video_id
    from _cache import get_metadata_cache, set_metadata_cache

    video_id = extract_video_id(url_or_id)
    cached = get_metadata_cache(video_id)
    if cached:
        logger.debug("metadata cache hit for %s", video_id)
        return VideoMetadata(**cached)
    logger.debug("metadata cache miss for %s", video_id)

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    raw_date = (info or {}).get("upload_date", "")
    published_date = (
        f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
        if len(raw_date) == 8 else ""
    )

    data = {
        "video_id": video_id,
        "title": (info or {}).get("title", ""),
        "channel": (info or {}).get("uploader", ""),
        "duration": int((info or {}).get("duration", 0)),
        "published_date": published_date,
        "description": (info or {}).get("description", ""),
        "tags": (info or {}).get("tags", []),
        "url": url,
    }
    set_metadata_cache(video_id, data)
    return VideoMetadata(**data)


def list_transcripts(url_or_id: str) -> list:
    from youtube_transcript_api import YouTubeTranscriptApi
    from _models import TranscriptMeta
    from _util import extract_video_id

    video_id = extract_video_id(url_or_id)
    api = YouTubeTranscriptApi()
    transcript_list = api.list(video_id)

    manual = []
    generated = []
    for t in transcript_list:
        meta = TranscriptMeta(
            language=t.language,
            language_code=t.language_code,
            is_generated=t.is_generated,
            is_translatable=t.is_translatable,
        )
        if t.is_generated:
            generated.append(meta)
        else:
            manual.append(meta)
    return manual + generated


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
