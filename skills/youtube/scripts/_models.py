from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChannelProfile:
    id: str
    title: str
    handle: str | None          # WITHOUT leading "@"
    subscriber_count: int | None
    total_view_count: int
    video_count: int
    upload_frequency_days: float | None
    created_at: str             # ISO 8601


@dataclass
class Video:
    id: str
    title: str
    view_count: int
    like_count: int | None
    duration_seconds: int
    is_short: bool              # duration_seconds < 60
    published_at: str           # ISO 8601
    category: str | None
    topics: list[str]


@dataclass
class PlaylistItem:
    id: str
    title: str
    position: int
    duration_seconds: int
    is_short: bool
    published_at: str           # ISO 8601


@dataclass
class PlaylistPage:
    items: list[PlaylistItem]
    next_page_token: str | None
    total_results: int


@dataclass
class Comment:
    id: str
    text: str
    author: str
    like_count: int
    published_at: str           # ISO 8601
    reply_count: int


@dataclass
class CommentPage:
    items: list[Comment]
    next_page_token: str | None


@dataclass
class ContentBreakdown:
    by_category: dict[str, int]
    by_topic: dict[str, int]
    sample_size: int            # count AFTER short filtering


@dataclass
class ChannelComparison:
    channel_a: ChannelProfile
    channel_b: ChannelProfile
    top_videos_a: list[Video]
    top_videos_b: list[Video]


@dataclass
class Snippet:
    text: str
    start: float
    duration: float


@dataclass
class Transcript:
    language: str
    language_code: str
    is_generated: bool          # True only for YouTube auto-captions; always False for whisper
    source: str                 # "caption" | "whisper"
    snippets: list[Snippet]
    text: str                   # space-joined full text

    def __post_init__(self) -> None:
        if self.source == "whisper" and self.is_generated:
            raise ValueError("is_generated must be False when source='whisper'")


@dataclass
class TranscriptMeta:
    language: str
    language_code: str
    is_generated: bool
    is_translatable: bool


@dataclass
class VideoMetadata:
    video_id: str
    title: str
    channel: str
    duration: int               # seconds
    published_date: str         # ISO 8601 (YYYY-MM-DD)
    description: str
    tags: list[str]
    url: str


@dataclass
class Chapter:
    title: str
    start: float                # seconds


@dataclass
class TranscriptHit:
    start: float                # seconds
    text: str
