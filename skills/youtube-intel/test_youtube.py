"""
Exploratory test script for the YouTube Data API v3.
Tests against @3blue1brown to validate key + response shapes.

Run:
    YOUTUBE_API_KEY=<key> python3 test_youtube.py
"""

from __future__ import annotations

import json
import os
import sys

import httpx

BASE = "https://www.googleapis.com/youtube/v3"
API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

if not API_KEY:
    print("ERROR: YOUTUBE_API_KEY env var is not set", file=sys.stderr)
    sys.exit(1)


def get(endpoint: str, **params) -> dict:
    params["key"] = API_KEY
    r = httpx.get(f"{BASE}/{endpoint}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def pp(label: str, data: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(json.dumps(data, indent=2))


# ── 1. Channel lookup by handle ──────────────────────────────────────────────
print("\n[1] channels.list — forHandle=@3blue1brown")
channel_resp = get(
    "channels",
    part="snippet,statistics,contentDetails",
    forHandle="@3blue1brown",
)
pp("channels.list response", channel_resp)

if not channel_resp.get("items"):
    print("ERROR: No channel found — handle lookup failed", file=sys.stderr)
    sys.exit(1)

channel = channel_resp["items"][0]
channel_id = channel["id"]
uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

print(f"\nChannel ID:          {channel_id}")
print(f"Title:               {channel['snippet']['title']}")
print(f"Subscribers:         {channel['statistics'].get('subscriberCount', 'hidden')}")
print(f"Total views:         {channel['statistics']['viewCount']}")
print(f"Video count:         {channel['statistics']['videoCount']}")
print(f"Uploads playlist ID: {uploads_playlist_id}")

# ── 2. Search for top videos by view count ───────────────────────────────────
print("\n[2] search.list — top videos by viewCount")
search_resp = get(
    "search",
    part="snippet",
    channelId=channel_id,
    order="viewCount",
    type="video",
    maxResults=5,
)
pp("search.list response (top 5 by views)", search_resp)

video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
print(f"\nTop video IDs: {video_ids}")

# ── 3. Fetch video statistics for those IDs ───────────────────────────────────
if video_ids:
    print("\n[3] videos.list — statistics + topicDetails for top videos")
    videos_resp = get(
        "videos",
        part="snippet,statistics,topicDetails",
        id=",".join(video_ids),
    )
    pp("videos.list response", videos_resp)

    for v in videos_resp.get("items", []):
        title = v["snippet"]["title"]
        views = v["statistics"].get("viewCount", "N/A")
        category = v["snippet"].get("categoryId", "N/A")
        topics = v.get("topicDetails", {}).get("topicCategories", [])
        print(f"\n  Title:    {title}")
        print(f"  Views:    {views}")
        print(f"  Category: {category}")
        print(f"  Topics:   {topics}")

# ── 4. playlistItems for upload recency (latest 5) ───────────────────────────
print("\n[4] playlistItems.list — latest uploads")
playlist_resp = get(
    "playlistItems",
    part="snippet",
    playlistId=uploads_playlist_id,
    maxResults=5,
)
pp("playlistItems.list response (latest 5)", playlist_resp)

dates = [
    item["snippet"]["publishedAt"]
    for item in playlist_resp.get("items", [])
]
print(f"\nLatest upload dates: {dates}")

print("\n\nAll tests passed — API key valid and response shapes confirmed.")
