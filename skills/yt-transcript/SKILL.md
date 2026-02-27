---
name: youtube_transcript_api
description: >
  Fetch and work with YouTube video transcripts without auth or API keys.
  Use when the user wants to: get the transcript of a YouTube video (by URL or
  video ID); summarize, analyze, or quote from a video's spoken content; list
  available caption languages for a video; retrieve timestamps for specific
  moments; or get video metadata (title, channel, duration, description, tags).
  Accepts all common YouTube URL formats (youtube.com/watch?v=, youtu.be/,
  youtube.com/embed/) as well as bare video IDs. Transcripts and metadata are
  cached locally in SQLite. Optionally uses Webshare proxies if
  WEBSHARE_USERNAME and WEBSHARE_PASS env vars are set.
---

# YouTube Transcript Skill

Wraps `youtube-transcript-api` with SQLite caching, optional Webshare proxy
fallback, and `yt-dlp`-backed metadata retrieval.

## Prerequisites

`uv` must be installed: https://docs.astral.sh/uv/getting-started/installation/

No API key needed.

## Setup

Write a script and run it with `uv`:

```bash
uv run --with youtube-transcript-api --with yt-dlp python your_script.py
```

In the script, import from the skill directory:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/yt-transcript/scripts"))
from yt_transcript import extract_video_id, list_transcripts, get_transcript, get_metadata
```

Cache lives at `~/.cache/yt-transcript/`.

## Core Functions

### `get_transcript(url_or_id, languages=None, prefer_manual=True) -> Transcript`

Fetch a transcript. Checks SQLite cache first (for default-language fetches).
Prefers manually created captions over auto-generated when `prefer_manual=True`,
falling back to auto-generated if none exists.

```python
t = get_transcript("https://www.youtube.com/watch?v=aircAruvnKk")
# t.language      -> 'English'
# t.language_code -> 'en'
# t.is_generated  -> False (manually created)
# t.snippets      -> list of Snippet(text, start, duration)
# t.text          -> full plain text (space-joined)
```

**With timestamps** (for referencing moments):
```python
for s in t.snippets[:5]:
    print(f"[{s.start:.1f}s] {s.text}")
```

**Plain text** (for summarization/analysis):
```python
print(t.text)
```

**Specific language** (bypasses cache):
```python
t = get_transcript("aircAruvnKk", languages=["fr", "en"])
```

### `get_metadata(url_or_id) -> VideoMetadata`

Fetch video metadata via yt-dlp. Checks SQLite cache first.
Requires `pip install yt-dlp`.

```python
m = get_metadata("https://www.youtube.com/watch?v=aircAruvnKk")
# m.video_id       -> '37f0ALZg-XI'
# m.title          -> 'But what is a neural network?'
# m.channel        -> '3Blue1Brown'
# m.duration       -> 1021  (seconds)
# m.published_date -> '20171005'
# m.description    -> '...'
# m.tags           -> ['neural network', 'deep learning', ...]
# m.url            -> 'https://www.youtube.com/watch?v=aircAruvnKk'
```

### `list_transcripts(url_or_id) -> list[TranscriptMeta]`

Show all available caption tracks. Manually created listed before generated.

```python
metas = list_transcripts("aircAruvnKk")
for m in metas:
    kind = "auto" if m.is_generated else "manual"
    print(f"  {m.language_code:10s}  {m.language}  ({kind})")
```

Each `TranscriptMeta` has: `language`, `language_code`, `is_generated`, `is_translatable`.

### `extract_video_id(url_or_id) -> str`

Parse a video ID from any URL format, or pass through a bare 11-char ID.

```python
extract_video_id("https://youtu.be/aircAruvnKk")                       # -> "aircAruvnKk"
extract_video_id("https://youtube.com/watch?v=aircAruvnKk&t=42s")      # -> "aircAruvnKk"
extract_video_id("aircAruvnKk")                                         # -> "aircAruvnKk"
```

## Caching

Transcripts and metadata are cached in SQLite at `~/.cache/yt-transcript/`:
- `transcripts.db` — full snippet data (text + timestamps) keyed by video ID
- `metadata.db` — yt-dlp metadata keyed by video ID

Cache is used automatically for default-language transcript fetches. Passing
an explicit `languages` list bypasses the transcript cache.

## Proxy Support

If `WEBSHARE_USERNAME` and `WEBSHARE_PASS` env vars are set, requests are
routed through Webshare proxies to avoid rate limiting. Falls back to a direct
connection if proxy setup fails.

## Error Handling

```python
from youtube_transcript_api import (
    TranscriptsDisabled,  # video has no captions at all
    NoTranscriptFound,    # no captions in requested language
    VideoUnavailable,     # video is private or deleted
)

try:
    t = get_transcript(url)
except TranscriptsDisabled:
    # video owner disabled transcripts
    pass
except NoTranscriptFound:
    # try a different language: list_transcripts(url) to see what's available
    pass
except VideoUnavailable:
    # video doesn't exist or is private
    pass
```

## Dependencies

Invoked via `uv run` — no manual installation required:

```bash
uv run --with youtube-transcript-api --with yt-dlp python your_script.py
```

- `youtube-transcript-api>=1.2.4`
- `yt-dlp` (only required for `get_metadata`)
