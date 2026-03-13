# YouTube Skill Design

## 1. Goal

Consolidate `youtube-intel` and `yt-transcript` into a single `youtube` skill covering
channel analytics, playlist traversal, comment fetching, video transcript/metadata
retrieval, keyword search within transcripts, chapter extraction, and local Whisper
transcription. The skill is designed for agentic LLM use: all list-returning functions
are paginated and context-window-friendly.

## 2. Constraints and Non-Goals

**Constraints:**
- `uv` is the only required system prerequisite
- Channel analytics functions require `YOUTUBE_API_KEY` env var; all other functions work without it
- Whisper transcription runs locally via `faster-whisper`; no OpenAI API calls
- Comment and playlist functions return raw data only — no NLP, no sentiment, no summarization
- Cache lives at `~/.cache/youtube/` (fresh start; `~/.cache/yt-transcript/` is not migrated)
- All list-returning functions accept `max_items` and `page_token` for cursor-based pagination
- All functions are synchronous; no async variants
- No retry logic; API errors are raised immediately to the caller
- Cache entries never expire; there is no TTL or invalidation mechanism

**Non-goals:**
- Sentiment analysis, clustering, or any LLM-based processing of comments or transcripts
- Video upload, editing, or any write operation against the YouTube API
- OAuth / authenticated API access (read-only public data only)
- Downloading video files (audio is downloaded transiently for Whisper transcription, then deleted)
- Historical channel growth metrics (YouTube Data API does not expose this)
- Support for YouTube Music, YouTube Kids, or private videos
- Migrating or reading the old `~/.cache/yt-transcript/` cache
- Proxy support (the old yt-transcript Webshare proxy is not carried over)
- Transcript translation (YouTube API supports it; this skill does not)
- Reply thread fetching for comments (top-level comments only)
- Async execution or concurrent API calls
- Exponential backoff or retry on transient errors
- Cache TTL or invalidation

## 3. Interface Contracts

### Skill directory: `~/.claude/skills/youtube/`

```
youtube/
  SKILL.md
  pyproject.toml          # httpx, youtube-transcript-api>=1.2.4, yt-dlp, faster-whisper
  scripts/
    channel.py            # channel-level functions (requires YOUTUBE_API_KEY)
    video.py              # video-level functions (no API key needed)
    _cache.py             # shared SQLite cache (~/.cache/youtube/)
    _util.py              # extract_video_id, is_short
```

### Data shapes

```python
@dataclass
class ChannelProfile:
    id: str
    title: str
    handle: str | None     # stored WITHOUT leading "@" (e.g. "3blue1brown", not "@3blue1brown")
    subscriber_count: int | None   # None if channel hides it
    total_view_count: int
    video_count: int
    # avg days between 10 most recent uploads; None if channel has fewer than 2 videos
    upload_frequency_days: float | None
    created_at: str        # ISO 8601

@dataclass
class Video:
    id: str
    title: str
    view_count: int
    like_count: int | None
    duration_seconds: int
    is_short: bool         # True when duration_seconds < 60
    published_at: str      # ISO 8601
    category: str | None
    topics: list[str]

@dataclass
class PlaylistItem:
    id: str                # video ID
    title: str
    position: int
    # duration_seconds populated via a videos.list batch call (one call per page, 1 quota unit per 50 items)
    duration_seconds: int
    is_short: bool         # True when duration_seconds < 60
    published_at: str      # ISO 8601

@dataclass
class PlaylistPage:
    items: list[PlaylistItem]
    next_page_token: str | None    # None = no more pages
    total_results: int             # always populated; YouTube API always returns this

@dataclass
class Comment:
    id: str
    text: str
    author: str
    like_count: int
    published_at: str      # ISO 8601
    reply_count: int

@dataclass
class CommentPage:
    items: list[Comment]
    next_page_token: str | None

@dataclass
class ContentBreakdown:
    by_category: dict[str, int]
    by_topic: dict[str, int]
    sample_size: int       # count of videos analyzed AFTER short filtering

@dataclass
class ChannelComparison:
    channel_a: ChannelProfile
    channel_b: ChannelProfile
    top_videos_a: list[Video]      # 10 each, exclude_shorts=True
    top_videos_b: list[Video]

@dataclass
class Snippet:
    text: str
    start: float           # seconds
    duration: float

@dataclass
class Transcript:
    language: str
    language_code: str
    # True only when sourced from YouTube's auto-generated caption system.
    # Always False for source="whisper".
    is_generated: bool
    source: str            # "caption" | "whisper"
    snippets: list[Snippet]
    text: str              # space-joined full text

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
    duration: int          # seconds
    published_date: str    # ISO 8601 (YYYY-MM-DD); normalized from yt-dlp's YYYYMMDD
    description: str
    tags: list[str]
    url: str

@dataclass
class Chapter:
    title: str
    start: float           # seconds

@dataclass
class TranscriptHit:
    start: float           # seconds
    text: str
```

### channel.py — requires YOUTUBE_API_KEY

```python
def get_channel(handle_or_id: str) -> ChannelProfile
    # Accepts @handle (with or without leading @) or bare channel ID (UCxxx)

def get_top_videos(
    channel_id: str,
    n: int = 10,
    exclude_shorts: bool = True,
) -> list[Video]
    # n <= 50; raises ValueError if n > 50 before any network call
    # Uses one search.list call (100 quota units) — logs WARNING with quota cost
    # Filter is applied AFTER fetch: result may contain fewer than n items
    # when exclude_shorts=True filters some out. Does NOT issue additional requests to fill to n.

def get_content_breakdown(
    channel_id: str,
    sample_size: int = 50,
    exclude_shorts: bool = True,
) -> ContentBreakdown
    # Uses one search.list call (100 quota units) — logs WARNING with quota cost
    # sample_size is the number of videos fetched from API; ContentBreakdown.sample_size
    # reflects count AFTER short filtering.

def compare_channels(
    handle_or_id_a: str,
    handle_or_id_b: str,
) -> ChannelComparison
    # Calls get_top_videos for each channel with exclude_shorts=True, n=10

def get_playlist(
    playlist_id: str,
    max_items: int = 50,
    page_token: str | None = None,
    exclude_shorts: bool = True,
) -> PlaylistPage
    # Fetches up to max_items playlist items per call.
    # Duration populated via a single videos.list batch call on the returned page.
    # Short filtering applied AFTER duration fetch; result may contain fewer than max_items.
    # page_token is opaque; only tokens returned by this function are valid inputs.

def get_comments(
    video_id: str,
    max_items: int = 20,
    page_token: str | None = None,
) -> CommentPage
    # Sorted by relevance (YouTube API default). Top-level comments only.
    # max_items <= 100; raises ValueError if max_items > 100 before any network call.
```

### video.py — no API key needed

```python
def extract_video_id(url_or_id: str) -> str
    # Accepts watch?v=, youtu.be/, /embed/, or bare 11-char ID.
    # Raises ValueError on unrecognized format.

def get_transcript(
    url_or_id: str,
    languages: list[str] | None = None,
    prefer_manual: bool = True,
    fallback_whisper: bool = False,
) -> Transcript
    # Cache: SQLite hit on default-language fetches (languages=None).
    # Bypasses cache when languages= is explicitly set.
    # fallback_whisper=True: on TranscriptsDisabled or NoTranscriptFound,
    #   logs WARNING and delegates to transcribe_whisper(url_or_id).
    # Raises ValueError if languages is not None AND fallback_whisper=True.

def transcribe_whisper(
    url_or_id: str,
    model: str = "small",
) -> Transcript
    # Downloads audio to a temp file in ~/.cache/youtube/tmp/ via yt-dlp.
    # Transcribes with faster-whisper using the specified model.
    # Deletes temp audio file in a finally block (cleanup is guaranteed).
    # Logs WARNING when called (slow operation; caller should be aware).
    # Returns Transcript(source="whisper", is_generated=False, language_code from faster-whisper).
    # Raises WhisperTranscriptionError wrapping the original cause on yt-dlp or model failure.

def get_metadata(url_or_id: str) -> VideoMetadata
    # Fetches via yt-dlp; cached in SQLite at ~/.cache/youtube/metadata.db.
    # published_date normalized to ISO 8601 (YYYY-MM-DD).

def list_transcripts(url_or_id: str) -> list[TranscriptMeta]
    # Manual tracks listed before generated tracks.

def get_chapters(url_or_id: str) -> list[Chapter]
    # Parses description fetched via yt-dlp (uses metadata cache).
    # Recognizes YouTube's standard chapter format: lines matching
    #   /^\d+:\d{2}(:\d{2})?\s+.+/ at the start of a line.
    # Returns [] if no chapter markers found.
    # Raises VideoUnavailable if yt-dlp cannot fetch the video at all.

def search_transcript(url_or_id: str, query: str) -> list[TranscriptHit]
    # Case-insensitive substring match within individual snippets only.
    # Multi-word queries must appear within a single snippet to match.
    # Raises ValueError if query is empty string.
    # Fetches transcript via get_transcript (uses cache); does NOT call YouTube API.
```

## 4. Acceptance Criteria

**Unit-testable (no network required):**
- `extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")` == `"dQw4w9WgXcQ"`
- `extract_video_id("https://youtu.be/dQw4w9WgXcQ")` == `"dQw4w9WgXcQ"`
- `extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")` == `"dQw4w9WgXcQ"`
- `extract_video_id("dQw4w9WgXcQ")` == `"dQw4w9WgXcQ"`
- `extract_video_id("not-a-video")` raises `ValueError`
- `get_transcript(url, languages=["fr"], fallback_whisper=True)` raises `ValueError`
- `get_top_videos(channel_id, n=51)` raises `ValueError` without making any network call
- `get_comments(video_id, max_items=101)` raises `ValueError` without making any network call
- `search_transcript(url, "")` raises `ValueError`
- A `Transcript` with `source="whisper"` and `is_generated=True` must not be constructable (enforced via `__post_init__`)
- `search_transcript` (with mocked transcript) returns only snippets whose `.text` contains the query (case-insensitive)
- `search_transcript` returns `[]` when no snippets match

**Integration-testable (require network):**
- `get_channel("@3blue1brown")` returns `ChannelProfile` with `title="3Blue1Brown"` and `id` starting with `"UC"`
- `get_top_videos(channel_id, n=5, exclude_shorts=True)` returns `len(result) <= 5`, all with `is_short=False`
- For a channel known to publish Shorts: `get_top_videos(channel_id, n=50, exclude_shorts=False)` returns at least one item with `is_short=True`
- `get_playlist(playlist_id, max_items=3)` returns `PlaylistPage` with `len(items) <= 3`
- Two consecutive `get_playlist` calls with `page_token` from first call return non-overlapping `items[0].id`
- `get_comments(video_id, max_items=5)` returns `CommentPage` with `len(items) <= 5`
- `get_transcript` called twice for the same video ID (default language) makes only one network call (verified via mock or SQLite row count)
- `get_chapters` on a video known to have chapters returns `list[Chapter]` with `len > 0` and all `start >= 0`
- `get_chapters` on a video known to have no chapters returns `[]`
- `transcribe_whisper` leaves no temp files in `~/.cache/youtube/tmp/` after completion (success or failure)

## 5. Error Handling / Failure Modes

| Condition | Behavior |
|-----------|----------|
| `YOUTUBE_API_KEY` absent or empty string, channel function called | Raise `MissingAPIKeyError` immediately — no network call |
| `YOUTUBE_API_KEY` set but invalid (API returns 400/403) | Re-raise `httpx.HTTPStatusError`; not retried |
| YouTube API quota exceeded (429 or 403 with `quotaExceeded` reason) | Re-raise `httpx.HTTPStatusError`; not retried |
| Network timeout on any HTTP call | Raise `httpx.TimeoutException`; not retried |
| Channel handle/ID not found | Raise `ChannelNotFoundError` |
| Video captions disabled | Raise `TranscriptsDisabled` (from `youtube-transcript-api`) |
| No captions in requested language | Raise `NoTranscriptFound` (from `youtube-transcript-api`) |
| Video private or deleted | Raise `VideoUnavailable` |
| Playlist ID not found | Raise `PlaylistNotFoundError` |
| Comments disabled on video | Raise `CommentsDisabled` |
| `page_token` invalid or expired | Re-raise `httpx.HTTPStatusError(400)` as `InvalidPageTokenError` |
| `get_top_videos` returns fewer than n due to short filtering | Return what's available; do not raise |
| Channel has fewer than 2 videos (can't compute upload frequency) | `ChannelProfile.upload_frequency_days = None` |
| `faster-whisper` model not cached | Downloads automatically to `~/.cache/huggingface/hub/` on first use; no special handling needed |
| yt-dlp audio download fails | Raise `WhisperTranscriptionError` wrapping original cause; temp file cleaned up in `finally` |
| `transcribe_whisper` called on a live stream URL | Raise `WhisperTranscriptionError("live streams are not supported")` |
| Description has no chapter markers | Return `[]`; not an error |
| yt-dlp fails to fetch video for `get_chapters` | Raise `VideoUnavailable` |
| `search_transcript` on a video with no snippets | Return `[]`; not an error |

## 6. Logging Requirements

All log output uses Python's standard `logging` module. The skill does not configure
handlers — callers configure logging. Default logger name: `youtube`.

| Event | Level |
|-------|-------|
| `search.list` API call made | `WARNING` — includes quota cost: `"search.list called (100 quota units)"` |
| `get_comments` API call made | `DEBUG` |
| Cache hit (transcript or metadata) | `DEBUG` — includes video ID |
| Cache miss | `DEBUG` — includes video ID |
| Whisper fallback triggered | `WARNING` — `"caption unavailable; falling back to Whisper for {video_id}"` |
| `transcribe_whisper` started | `WARNING` — `"starting Whisper transcription for {video_id} (model={model}); this may be slow"` |
| Temp audio file created | `DEBUG` — includes full path |
| Temp audio file deleted | `DEBUG` — includes full path |
| Temp audio cleanup failed | `ERROR` — includes path and exception |

## 7. Code Example (conventions/style)

```python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))

from channel import get_channel, get_playlist
from video import get_transcript, search_transcript

channel = get_channel("@3blue1brown")
page = get_playlist(channel.id, max_items=10)

for item in page.items:
    transcript = get_transcript(item.id, fallback_whisper=True)
    hits = search_transcript(item.id, "eigenvalue")
    for hit in hits:
        print(f"[{hit.start:.1f}s] {hit.text}")

# advance to the next page
if page.next_page_token:
    next_page = get_playlist(channel.id, max_items=10, page_token=page.next_page_token)
```

## 8. Domain Language

| Term | Definition |
|------|------------|
| **channel** | A YouTube creator account identified by a handle (`@name`) or channel ID (`UCxxx`) |
| **video** | A single YouTube video, identified by an 11-character video ID |
| **short** | A video with `duration_seconds < 60`; identified by duration alone, not by YouTube's Shorts feed |
| **playlist** | An ordered, curator-defined list of videos identified by a playlist ID (`PLxxx`) |
| **transcript** | The full caption text for a video, as a sequence of timed snippets |
| **snippet** | A single timed segment within a transcript: `(text, start, duration)` |
| **chapter** | A named section of a video with a start timestamp, parsed from the description |
| **page token** | An opaque string returned by paginated functions; pass it back to retrieve the next page; tokens are not interchangeable across functions |
| **caption** | A transcript sourced from YouTube's caption system (manual or auto-generated) |
| **whisper transcript** | A transcript produced by local `faster-whisper` from downloaded audio; `is_generated=False` |
| **is_generated** | True only when a transcript came from YouTube's automatic speech recognition system; always False for whisper transcripts |
| **comment** | A top-level comment on a video; reply threads are explicitly out of scope |
| **quota unit** | The YouTube Data API v3 cost currency; daily limit is 10,000 units; `search.list` costs 100 units per call |
| **handle** | The `@username` identifier for a channel, stored without the leading `@` in `ChannelProfile.handle` |

## 9. Invalid State Transitions

- Calling `get_transcript` with both `languages=["fr"]` and `fallback_whisper=True` must raise `ValueError` before any network call — language override and Whisper fallback are mutually exclusive
- `get_top_videos` with `n > 50` must raise `ValueError` before any network call
- `get_comments` with `max_items > 100` must raise `ValueError` before any network call
- `search_transcript` with `query=""` must raise `ValueError`
- A `Transcript` with `source="whisper"` must have `is_generated=False`; enforced via `__post_init__` raising `ValueError` if violated
- Passing a `page_token` from `get_playlist` to `get_comments` or vice versa is undefined behavior; tokens are scoped to the function that produced them and must not be cross-used
- `get_top_videos` must never issue a second API call to fill `n` after short filtering — it returns fewer items, not a padded list
