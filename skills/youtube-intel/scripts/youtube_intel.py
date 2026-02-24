"""
YouTube Data API v3 wrapper.

Requires YOUTUBE_API_KEY env var.
"""

from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass

BASE_URL = "https://www.googleapis.com/youtube/v3"

# YouTube category ID -> name (common subset)
CATEGORY_NAMES: dict[str, str] = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "How-to & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
}


class ChannelNotFoundError(Exception):
    """Raised when channel handle or ID is not found."""


@dataclass
class ChannelProfile:
    id: str
    handle: str
    title: str
    description: str
    subscriber_count: int | None  # None if hidden
    total_view_count: int
    video_count: int
    created_at: str
    upload_frequency_days: float | None  # avg days between recent 10 uploads


@dataclass
class Video:
    id: str
    title: str
    published_at: str
    view_count: int
    like_count: int | None
    category: str
    topics: list[str]  # parsed from Wikipedia URLs in topicDetails


@dataclass
class ContentBreakdown:
    by_category: dict[str, int]  # category name -> video count
    by_topic: dict[str, int]  # topic name -> video count
    sample_size: int


@dataclass
class ChannelComparison:
    channel_a: ChannelProfile
    channel_b: ChannelProfile
    top_videos_a: list[Video]
    top_videos_b: list[Video]


def _api_key() -> str:
    key = os.environ.get("YOUTUBE_API_KEY", "")
    if not key:
        raise RuntimeError("YOUTUBE_API_KEY environment variable is not set")
    return key


def _get(endpoint: str, **params) -> dict:
    params["key"] = _api_key()
    r = httpx.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _parse_topics(topic_categories: list[str]) -> list[str]:
    """Extract human-readable names from Wikipedia category URLs."""
    names = []
    for url in topic_categories:
        # e.g. https://en.wikipedia.org/wiki/Mathematics -> Mathematics
        name = url.rstrip("/").split("/")[-1].replace("_", " ")
        names.append(name)
    return names


def _compute_upload_frequency(channel_id: str, uploads_playlist_id: str) -> float | None:
    """Return avg days between the most recent 10 uploads, or None on failure."""
    resp = _get(
        "playlistItems",
        part="snippet",
        playlistId=uploads_playlist_id,
        maxResults=10,
    )
    items = resp.get("items", [])
    if len(items) < 2:
        return None

    dates = [
        datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z", "+00:00"))
        for item in items
    ]
    total_days = (dates[0] - dates[-1]).days
    return round(total_days / (len(dates) - 1), 1)


def get_channel(handle_or_id: str) -> ChannelProfile:
    """
    Look up a channel by handle (e.g. @3blue1brown) or channel ID.

    Returns subscriber count, total views, video count, and upload frequency.
    """
    # Determine lookup parameter
    if handle_or_id.startswith("UC"):
        params = {"id": handle_or_id}
    else:
        # strip leading @ if present for the API (it accepts both)
        params = {"forHandle": handle_or_id}

    resp = _get(
        "channels",
        part="snippet,statistics,contentDetails",
        **params,
    )
    items = resp.get("items", [])
    if not items:
        raise ChannelNotFoundError(
            f"No channel found for '{handle_or_id}'. "
            "Check that the handle or ID is correct."
        )

    ch = items[0]
    stats = ch["statistics"]
    uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    channel_id = ch["id"]

    freq = _compute_upload_frequency(channel_id, uploads_id)

    return ChannelProfile(
        id=channel_id,
        handle=ch["snippet"].get("customUrl", ""),
        title=ch["snippet"]["title"],
        description=ch["snippet"]["description"],
        subscriber_count=(
            int(stats["subscriberCount"])
            if not stats.get("hiddenSubscriberCount")
            else None
        ),
        total_view_count=int(stats["viewCount"]),
        video_count=int(stats["videoCount"]),
        created_at=ch["snippet"]["publishedAt"],
        upload_frequency_days=freq,
    )


def get_top_videos(channel_id: str, n: int = 10) -> list[Video]:
    """
    Return the top N videos by view count for the given channel.

    Uses search.list (100 quota units) + videos.list (1 unit).
    Max n is 50.
    """
    n = min(n, 50)

    search_resp = _get(
        "search",
        part="id",
        channelId=channel_id,
        order="viewCount",
        type="video",
        maxResults=n,
    )
    video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
    if not video_ids:
        return []

    return _fetch_video_details(video_ids)


def _fetch_video_details(video_ids: list[str]) -> list[Video]:
    """Fetch statistics, snippet, and topicDetails for a list of video IDs."""
    # videos.list accepts up to 50 IDs at once
    chunks = [video_ids[i:i + 50] for i in range(0, len(video_ids), 50)]
    videos = []
    for chunk in chunks:
        resp = _get(
            "videos",
            part="snippet,statistics,topicDetails",
            id=",".join(chunk),
        )
        for item in resp.get("items", []):
            stats = item.get("statistics", {})
            snippet = item["snippet"]
            cat_id = snippet.get("categoryId", "")
            topic_urls = item.get("topicDetails", {}).get("topicCategories", [])
            like_count_raw = stats.get("likeCount")
            videos.append(Video(
                id=item["id"],
                title=snippet["title"],
                published_at=snippet["publishedAt"],
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(like_count_raw) if like_count_raw is not None else None,
                category=CATEGORY_NAMES.get(cat_id, f"Category {cat_id}"),
                topics=_parse_topics(topic_urls),
            ))
    return videos


def get_content_breakdown(channel_id: str, sample_size: int = 50) -> ContentBreakdown:
    """
    Break down a channel's content by category and topic.

    Samples up to `sample_size` top videos (by view count) for analysis.
    Uses search.list (100 quota units) + videos.list (1 unit per 50 videos).
    """
    sample_size = min(sample_size, 50)
    search_resp = _get(
        "search",
        part="id",
        channelId=channel_id,
        order="viewCount",
        type="video",
        maxResults=sample_size,
    )
    video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
    if not video_ids:
        return ContentBreakdown(by_category={}, by_topic={}, sample_size=0)

    videos = _fetch_video_details(video_ids)

    categories = Counter(v.category for v in videos)
    topics: Counter = Counter()
    for v in videos:
        for topic in v.topics:
            topics[topic] += 1

    return ContentBreakdown(
        by_category=dict(categories.most_common()),
        by_topic=dict(topics.most_common()),
        sample_size=len(videos),
    )


def compare_channels(handle_or_id_a: str, handle_or_id_b: str) -> ChannelComparison:
    """
    Compare two channels side by side.

    Returns profiles and top 10 videos for each.
    Fetches channels sequentially (two separate API round-trips).
    """
    channel_a = get_channel(handle_or_id_a)
    channel_b = get_channel(handle_or_id_b)
    top_a = get_top_videos(channel_a.id, n=10)
    top_b = get_top_videos(channel_b.id, n=10)
    return ChannelComparison(
        channel_a=channel_a,
        channel_b=channel_b,
        top_videos_a=top_a,
        top_videos_b=top_b,
    )
