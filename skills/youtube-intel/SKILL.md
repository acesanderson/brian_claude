---
name: youtube_data_api
description: >
  Analyze YouTube channels using the YouTube Data API v3. Use when the user asks to:
  look up a YouTube channel (by handle like @3blue1brown or channel ID), get subscriber
  count, total views, upload frequency, or top videos; break down a channel's content
  by topic or category; or compare two YouTube channels side by side.
  Requires YOUTUBE_API_KEY env var (no OAuth needed).
---

# YouTube Intel Skill

Wraps the YouTube Data API v3 to analyze channels.

## Setup

```python
import sys
sys.path.insert(0, "/Users/bianders/.claude/skills/youtube-intel/scripts")
from youtube_intel import get_channel, get_top_videos, get_content_breakdown, compare_channels
```

`YOUTUBE_API_KEY` must be set in the environment.

## Core Functions

### `get_channel(handle_or_id: str) -> ChannelProfile`

Look up a channel by handle (`@3blue1brown`) or channel ID (`UCYO_jab_esuFRV4b17AJtAw`).

```python
ch = get_channel("@3blue1brown")
# ch.title, ch.subscriber_count, ch.total_view_count,
# ch.video_count, ch.upload_frequency_days, ch.created_at
```

`upload_frequency_days` is the avg days between the 10 most recent uploads.
`subscriber_count` is `None` if the channel hides it.

### `get_top_videos(channel_id: str, n: int = 10) -> list[Video]`

Top N videos by view count (max 50). Each `Video` has:
`id`, `title`, `view_count`, `like_count`, `published_at`, `category`, `topics`.

```python
top = get_top_videos(ch.id, n=10)
for v in top:
    print(f"{v.view_count:>12,}  {v.title}")
```

### `get_content_breakdown(channel_id: str, sample_size: int = 50) -> ContentBreakdown`

Categorize content from a sample of top videos. Returns:
- `by_category`: `{category_name: count}` (e.g. `{"Education": 48, "Science & Technology": 2}`)
- `by_topic`: `{topic_name: count}` derived from Wikipedia topic URLs
- `sample_size`: actual number of videos analyzed

```python
bd = get_content_breakdown(ch.id, sample_size=50)
print(bd.by_category)
print(bd.by_topic)
```

### `compare_channels(handle_or_id_a, handle_or_id_b) -> ChannelComparison`

Returns `channel_a`, `channel_b` profiles and `top_videos_a`, `top_videos_b` (10 each).

```python
cmp = compare_channels("@3blue1brown", "@veritasium")
# cmp.channel_a vs cmp.channel_b
```

## Quota Notes

`search.list` costs **100 units** per call (daily limit: 10,000 units).
`get_top_videos` and `get_content_breakdown` each use one `search.list` call.
`get_channel` uses `channels.list` (1 unit) + `playlistItems.list` (1 unit).

## Error Handling

```python
from youtube_intel import ChannelNotFoundError

try:
    ch = get_channel("@nonexistent")
except ChannelNotFoundError:
    # handle or ID is wrong
```

`httpx.HTTPStatusError` is raised on API errors (e.g. invalid key = 400/403).

## Dependencies

- `httpx`
