# YouTube Skill

Unified skill for YouTube channel analytics, video transcripts, playlist traversal,
comment fetching, chapter extraction, and local Whisper transcription.

## Prerequisites

- **uv** — install: https://docs.astral.sh/uv/getting-started/installation/
- `YOUTUBE_API_KEY` — required only for channel functions (`channel.py`). Get one at
  https://console.cloud.google.com/. Enable "YouTube Data API v3". No OAuth needed.

## Setup

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))

from channel import get_channel, get_top_videos, get_playlist, get_comments
from video import get_transcript, search_transcript, get_chapters, transcribe_whisper, get_metadata
```

Run with:
```bash
uv run --directory ~/.claude/skills/youtube python your_script.py
```

## Channel Functions (require YOUTUBE_API_KEY)

### `get_channel(handle_or_id) -> ChannelProfile`
Look up a channel by `@handle` or channel ID. `handle` on the result has no leading `@`.

### `get_top_videos(channel_id, n=10, exclude_shorts=True) -> list[Video]`
Top N videos by view count. `n <= 50`. Shorts (< 60s) filtered by default.
**Quota cost: 100 units (search.list)**

### `get_playlist(playlist_id, max_items=50, page_token=None, exclude_shorts=True) -> PlaylistPage`
Paginated playlist access. Pass `page.next_page_token` to get the next page.

### `get_comments(video_id, max_items=20, page_token=None) -> CommentPage`
Top-level comments sorted by relevance. `max_items <= 100`. Paginated.

### `get_content_breakdown(channel_id, sample_size=50, exclude_shorts=True) -> ContentBreakdown`
Category and topic breakdown for a channel sample.
**Quota cost: 100 units (search.list)**

### `compare_channels(handle_or_id_a, handle_or_id_b) -> ChannelComparison`
Side-by-side channel profiles + top 10 videos each.

## Video Functions (no API key needed)

### `get_transcript(url_or_id, languages=None, prefer_manual=True, fallback_whisper=False) -> Transcript`
Fetch captions. Cached in `~/.cache/youtube/transcripts.db`. Set `fallback_whisper=True`
to use local Whisper when captions are unavailable. Cannot combine `languages=` with
`fallback_whisper=True`.

### `transcribe_whisper(url_or_id, model="small") -> Transcript`
Downloads audio via yt-dlp, transcribes locally with `faster-whisper`. Model `small`
(~245 MB) downloaded to `~/.cache/huggingface/hub/` on first use.

### `get_metadata(url_or_id) -> VideoMetadata`
Video metadata via yt-dlp. Cached in `~/.cache/youtube/metadata.db`.

### `list_transcripts(url_or_id) -> list[TranscriptMeta]`
All available caption tracks. Manual tracks listed before auto-generated.

### `get_chapters(url_or_id) -> list[Chapter]`
Chapters parsed from video description. Returns `[]` if none found.

### `search_transcript(url_or_id, query) -> list[TranscriptHit]`
Case-insensitive substring search within transcript snippets. Each hit includes timestamp.

## Quota Notes

- Daily limit: 10,000 units
- `search.list`: **100 units** — called by `get_top_videos` and `get_content_breakdown`
- `videos.list`, `channels.list`, `playlistItems.list`, `commentThreads.list`: **1 unit each**

## Error Reference

| Exception | Cause |
|-----------|-------|
| `MissingAPIKeyError` | `YOUTUBE_API_KEY` not set |
| `ChannelNotFoundError` | Handle or ID doesn't exist |
| `PlaylistNotFoundError` | Playlist ID doesn't exist |
| `CommentsDisabled` | Video has comments disabled |
| `VideoUnavailable` | Video is private or deleted |
| `TranscriptsDisabled` | Video has no captions at all |
| `NoTranscriptFound` | No captions in requested language |
| `InvalidPageTokenError` | Expired or wrong-function page token |
| `WhisperTranscriptionError` | yt-dlp download or model failure |
