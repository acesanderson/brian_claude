---
name: youtube_transcript_api
description: >
  Fetch and work with YouTube video transcripts without auth or API keys.
  Use when the user wants to: get the transcript of a YouTube video (by URL or
  video ID); summarize, analyze, or quote from a video's spoken content; list
  available caption languages for a video; or retrieve timestamps for specific
  moments. Accepts all common YouTube URL formats (youtube.com/watch?v=,
  youtu.be/, youtube.com/embed/) as well as bare video IDs.
  No API key required. Install: pip install youtube-transcript-api
---

# YouTube Transcript Skill

Wraps `youtube-transcript-api` to fetch video transcripts without auth.

## Setup

```python
import sys
sys.path.insert(0, "/Users/bianders/.claude/skills/yt-transcript/scripts")
from yt_transcript import extract_video_id, list_transcripts, get_transcript
```

No API key needed. Requires `youtube-transcript-api>=1.2.4` (v1.0.x has a
known bug where transcript URLs return empty bodies).

## Core Functions

### `get_transcript(url_or_id, languages=None, prefer_manual=True) -> Transcript`

Fetch a transcript. Prefers manually created captions over auto-generated
when `prefer_manual=True` (default), falling back to auto-generated if none exists.

```python
t = get_transcript("https://www.youtube.com/watch?v=aircAruvnKk")
# t.language      -> 'English'
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
print(t.text)  # 18k chars of space-joined speech
```

**Specific language:**
```python
t = get_transcript("aircAruvnKk", languages=["fr", "en"])
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
extract_video_id("https://youtu.be/aircAruvnKk")   # -> "aircAruvnKk"
extract_video_id("https://youtube.com/watch?v=aircAruvnKk&t=42s")  # -> "aircAruvnKk"
extract_video_id("aircAruvnKk")  # -> "aircAruvnKk"
```

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
except NoTranscriptFound:
    # try a different language: list_transcripts(url) to see what's available
except VideoUnavailable:
    # video doesn't exist or is private
```

## Version Note

`youtube-transcript-api` v1.0.x contains a bug where `transcript.fetch()`
silently returns an empty XML response. Use `>=1.2.4`.

## Dependencies

- `youtube-transcript-api>=1.2.4`
