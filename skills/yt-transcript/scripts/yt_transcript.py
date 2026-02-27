"""
YouTube transcript and metadata fetcher.

Features:
- SQLite caching for transcripts (with full snippet/timestamp preservation) and metadata
- Optional Webshare proxy support via WEBSHARE_USERNAME / WEBSHARE_PASS env vars
- yt-dlp metadata retrieval (optional dependency)
- All common YouTube URL formats supported
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_URL_PATTERNS = [
    re.compile(r"[?&]v=([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"embed/([A-Za-z0-9_-]{11})"),
]


# ── Data types ────────────────────────────────────────────────────────────────

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


@dataclass
class VideoMetadata:
    video_id: str
    url: str | None
    title: str | None
    published_date: str | None
    channel: str | None
    duration: int | None
    description: str | None
    tags: list[str]


# ── Cache helpers ─────────────────────────────────────────────────────────────

def _cache_dir() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    d = base / "yt-transcript"
    d.mkdir(parents=True, exist_ok=True)
    return d


class _TranscriptCache:
    def __init__(self) -> None:
        self._con = sqlite3.connect(_cache_dir() / "transcripts.db")
        self._con.execute(
            "CREATE TABLE IF NOT EXISTS transcripts ("
            "id TEXT PRIMARY KEY, "
            "language TEXT, "
            "language_code TEXT, "
            "is_generated INT, "
            "snippets TEXT NOT NULL)"
        )
        self._con.commit()

    def get(self, video_id: str) -> Transcript | None:
        row = self._con.execute(
            "SELECT language, language_code, is_generated, snippets "
            "FROM transcripts WHERE id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return None
        language, language_code, is_generated, snippets_json = row
        snippets = [Snippet(**s) for s in json.loads(snippets_json)]
        return Transcript(
            video_id=video_id,
            language=language,
            language_code=language_code,
            is_generated=bool(is_generated),
            snippets=snippets,
        )

    def set(self, video_id: str, transcript: Transcript) -> None:
        snippets_json = json.dumps(
            [{"text": s.text, "start": s.start, "duration": s.duration}
             for s in transcript.snippets]
        )
        self._con.execute(
            "INSERT OR REPLACE INTO transcripts "
            "(id, language, language_code, is_generated, snippets) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                video_id,
                transcript.language,
                transcript.language_code,
                int(transcript.is_generated),
                snippets_json,
            ),
        )
        self._con.commit()


class _MetadataCache:
    def __init__(self) -> None:
        self._con = sqlite3.connect(_cache_dir() / "metadata.db")
        self._con.execute(
            "CREATE TABLE IF NOT EXISTS metadata ("
            "id TEXT PRIMARY KEY, "
            "url TEXT, "
            "title TEXT, "
            "published_date TEXT, "
            "channel TEXT, "
            "duration INT, "
            "description TEXT, "
            "tags TEXT)"
        )
        self._con.commit()

    def get(self, video_id: str) -> VideoMetadata | None:
        row = self._con.execute(
            "SELECT url, title, published_date, channel, duration, description, tags "
            "FROM metadata WHERE id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return None
        url, title, published_date, channel, duration, description, tags_str = row
        return VideoMetadata(
            video_id=video_id,
            url=url,
            title=title,
            published_date=published_date,
            channel=channel,
            duration=duration,
            description=description,
            tags=json.loads(tags_str) if tags_str else [],
        )

    def set(self, video_id: str, meta: VideoMetadata) -> None:
        self._con.execute(
            "INSERT OR REPLACE INTO metadata "
            "(id, url, title, published_date, channel, duration, description, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                video_id,
                meta.url,
                meta.title,
                meta.published_date,
                meta.channel,
                meta.duration,
                meta.description,
                json.dumps(meta.tags or []),
            ),
        )
        self._con.commit()


# ── Module-level singletons ───────────────────────────────────────────────────

def _make_api() -> YouTubeTranscriptApi:
    username = os.environ.get("WEBSHARE_USERNAME")
    password = os.environ.get("WEBSHARE_PASS")
    if username and password:
        try:
            from youtube_transcript_api.proxies import WebshareProxyConfig
            logger.debug("Using Webshare proxy for transcript requests")
            return YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=username,
                    proxy_password=password,
                )
            )
        except Exception as exc:
            logger.warning("Webshare proxy setup failed (%s), using direct connection", exc)
    return YouTubeTranscriptApi()


_api = _make_api()
_transcript_cache = _TranscriptCache()
_metadata_cache = _MetadataCache()


# ── Public API ────────────────────────────────────────────────────────────────

def extract_video_id(url_or_id: str) -> str:
    """
    Extract the 11-char video ID from any common YouTube URL, or pass through a bare ID.

    Supported formats:
      youtube.com/watch?v=<id>
      youtu.be/<id>
      youtube.com/embed/<id>
      bare 11-char ID
    """
    for pattern in _URL_PATTERNS:
        m = pattern.search(url_or_id)
        if m:
            return m.group(1)
    if _ID_RE.match(url_or_id):
        return url_or_id
    raise ValueError(f"Cannot extract video ID from: {url_or_id!r}")


def list_transcripts(url_or_id: str) -> list[TranscriptMeta]:
    """
    Return metadata for all available transcripts. Manual transcripts listed before auto-generated.
    """
    video_id = extract_video_id(url_or_id)
    tl = _api.list(video_id)
    results: list[TranscriptMeta] = []
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
    Fetch transcript for a video. Checks SQLite cache first (default-language fetches only).

    Args:
        url_or_id: YouTube URL or bare video ID.
        languages: Language codes in priority order. Defaults to ['en'].
                   Passing an explicit list bypasses the cache.
        prefer_manual: Prefer manually created captions; falls back to auto-generated.

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
    use_cache = languages is None

    if use_cache:
        cached = _transcript_cache.get(video_id)
        if cached:
            logger.debug("Transcript cache hit for %s", video_id)
            return cached

    if prefer_manual:
        try:
            tl = _api.list(video_id)
            fetched = tl.find_manually_created_transcript(langs).fetch()
        except NoTranscriptFound:
            fetched = _api.fetch(video_id, languages=langs)
    else:
        fetched = _api.fetch(video_id, languages=langs)

    transcript = Transcript(
        video_id=video_id,
        language=fetched.language,
        language_code=fetched.language_code,
        is_generated=fetched.is_generated,
        snippets=[
            Snippet(text=s.text, start=s.start, duration=s.duration)
            for s in fetched.snippets
        ],
    )

    if use_cache:
        _transcript_cache.set(video_id, transcript)

    return transcript


@lru_cache(maxsize=128)
def get_metadata(url_or_id: str) -> VideoMetadata:
    """
    Fetch video metadata (title, channel, duration, description, tags) via yt-dlp.
    Checks SQLite cache first.

    Requires yt-dlp — invoke via: uv run --with yt-dlp python your_script.py
    """
    import yt_dlp

    video_id = extract_video_id(url_or_id)

    cached = _metadata_cache.get(video_id)
    if cached:
        logger.debug("Metadata cache hit for %s", video_id)
        return cached

    with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
        info = ydl.extract_info(video_id, download=False)

    meta = VideoMetadata(
        video_id=info.get("id") or video_id,
        url=info.get("webpage_url"),
        title=info.get("title"),
        published_date=info.get("upload_date"),
        channel=info.get("channel"),
        duration=info.get("duration"),
        description=info.get("description"),
        tags=info.get("tags") or [],
    )
    _metadata_cache.set(video_id, meta)
    return meta
