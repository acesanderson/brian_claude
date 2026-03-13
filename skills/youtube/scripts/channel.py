from __future__ import annotations

import logging
import os
import re
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from _models import (
        ChannelProfile,
        Video,
        ContentBreakdown,
        ChannelComparison,
        PlaylistPage,
        CommentPage,
    )

logger = logging.getLogger("youtube")

_BASE = "https://www.googleapis.com/youtube/v3"


class MissingAPIKeyError(Exception):
    pass


class ChannelNotFoundError(Exception):
    pass


class PlaylistNotFoundError(Exception):
    pass


class CommentsDisabled(Exception):
    pass


class InvalidPageTokenError(Exception):
    pass


def _api_key() -> str:
    key = os.getenv("YOUTUBE_API_KEY", "")
    if not key:
        raise MissingAPIKeyError(
            "YOUTUBE_API_KEY environment variable is not set or is empty"
        )
    return key


def _get(path: str, **params) -> dict:
    params["key"] = _api_key()
    resp = httpx.get(f"{_BASE}/{path}", params=params)
    resp.raise_for_status()
    return resp.json()


def _parse_duration(iso: str) -> int:
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0
    h, mins, s = m.group(1), m.group(2), m.group(3)
    return int(h or 0) * 3600 + int(mins or 0) * 60 + int(s or 0)


def get_channel(handle_or_id: str) -> "ChannelProfile":
    from _models import ChannelProfile

    if handle_or_id.startswith("UC") and not handle_or_id.startswith("@"):
        channel_id = handle_or_id
    else:
        handle = handle_or_id.lstrip("@")
        data = _get("channels", part="id", forHandle=handle)
        items = data.get("items", [])
        if not items:
            raise ChannelNotFoundError(f"No channel found for handle: {handle_or_id!r}")
        channel_id = items[0]["id"]

    data = _get(
        "channels",
        part="snippet,statistics,contentDetails",
        id=channel_id,
    )
    items = data.get("items", [])
    if not items:
        raise ChannelNotFoundError(f"No channel found for ID: {channel_id!r}")

    item = items[0]
    stats = item.get("statistics", {})
    snippet = item["snippet"]

    uploads_playlist_id = (
        item.get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )
    upload_frequency = None
    if uploads_playlist_id:
        upload_frequency = _compute_upload_frequency(uploads_playlist_id)

    raw_handle = snippet.get("customUrl", "").lstrip("@") or None

    return ChannelProfile(
        id=channel_id,
        title=snippet["title"],
        handle=raw_handle,
        subscriber_count=int(stats["subscriberCount"])
        if not stats.get("hiddenSubscriberCount") else None,
        total_view_count=int(stats.get("viewCount", 0)),
        video_count=int(stats.get("videoCount", 0)),
        upload_frequency_days=upload_frequency,
        created_at=snippet["publishedAt"],
    )


def _compute_upload_frequency(uploads_playlist_id: str) -> float | None:
    from datetime import datetime

    data = _get(
        "playlistItems",
        part="contentDetails",
        playlistId=uploads_playlist_id,
        maxResults=10,
    )
    items = data.get("items", [])
    if len(items) < 2:
        return None
    dates = [
        datetime.fromisoformat(
            item["contentDetails"]["videoPublishedAt"].replace("Z", "+00:00")
        )
        for item in items
        if item["contentDetails"].get("videoPublishedAt")
    ]
    if len(dates) < 2:
        return None
    dates.sort(reverse=True)
    gaps = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1)]
    return sum(gaps) / len(gaps)


def get_top_videos(
    channel_id: str,
    n: int = 10,
    exclude_shorts: bool = True,
) -> list:
    from _models import Video
    from _util import is_short

    if n > 50:
        raise ValueError(f"n must be <= 50, got {n}")

    logger.warning("search.list called (100 quota units) for channel %s", channel_id)
    data = _get(
        "search",
        part="id",
        channelId=channel_id,
        order="viewCount",
        type="video",
        maxResults=n,
    )

    video_ids = [item["id"]["videoId"] for item in data.get("items", [])][:n]
    if not video_ids:
        return []

    details = _get(
        "videos",
        part="snippet,statistics,contentDetails",
        id=",".join(video_ids),
    )

    videos = []
    for item in details.get("items", []):
        duration_seconds = _parse_duration(
            item["contentDetails"].get("duration", "PT0S")
        )
        short = is_short(duration_seconds)
        if exclude_shorts and short:
            continue
        videos.append(Video(
            id=item["id"],
            title=item["snippet"]["title"],
            view_count=int(item["statistics"].get("viewCount", 0)),
            like_count=int(item["statistics"]["likeCount"])
            if "likeCount" in item["statistics"] else None,
            duration_seconds=duration_seconds,
            is_short=short,
            published_at=item["snippet"]["publishedAt"],
            category=None,
            topics=[],
        ))
    return videos


def get_comments(
    video_id: str,
    max_items: int = 20,
    page_token: str | None = None,
) -> "CommentPage":
    from _models import Comment, CommentPage

    if max_items > 100:
        raise ValueError(f"max_items must be <= 100, got {max_items}")

    params: dict = dict(
        part="snippet",
        videoId=video_id,
        order="relevance",
        maxResults=min(max_items, 100),
        textFormat="plainText",
    )
    if page_token:
        params["pageToken"] = page_token

    try:
        data = _get("commentThreads", **params)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            try:
                reason = exc.response.json()["error"]["errors"][0]["reason"]
            except Exception:
                reason = ""
            if reason == "commentsDisabled":
                raise CommentsDisabled(f"Comments are disabled for video {video_id}") from exc
        raise

    comments = []
    for item in data.get("items", []):
        top = item["snippet"]["topLevelComment"]["snippet"]
        comments.append(Comment(
            id=item["id"],
            text=top["textDisplay"],
            author=top["authorDisplayName"],
            like_count=top.get("likeCount", 0),
            published_at=top["publishedAt"],
            reply_count=item["snippet"].get("totalReplyCount", 0),
        ))

    return CommentPage(
        items=comments,
        next_page_token=data.get("nextPageToken"),
    )


def get_playlist(
    playlist_id: str,
    max_items: int = 50,
    page_token: str | None = None,
    exclude_shorts: bool = True,
) -> "PlaylistPage":
    from _models import PlaylistItem, PlaylistPage
    from _util import is_short

    params: dict = dict(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=min(max_items, 50),
    )
    if page_token:
        params["pageToken"] = page_token

    try:
        data = _get("playlistItems", **params)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise PlaylistNotFoundError(f"Playlist not found: {playlist_id}") from exc
        raise

    if not data.get("items"):
        return PlaylistPage(items=[], next_page_token=None, total_results=0)

    video_ids = [item["contentDetails"]["videoId"] for item in data["items"]]
    duration_map = _fetch_durations(video_ids)

    items = []
    for item in data["items"]:
        vid_id = item["contentDetails"]["videoId"]
        duration = duration_map.get(vid_id, 0)
        short = is_short(duration)
        if exclude_shorts and short:
            continue
        items.append(PlaylistItem(
            id=vid_id,
            title=item["snippet"]["title"],
            position=item["snippet"]["position"],
            duration_seconds=duration,
            is_short=short,
            published_at=item["contentDetails"].get("videoPublishedAt", ""),
        ))

    return PlaylistPage(
        items=items,
        next_page_token=data.get("nextPageToken"),
        total_results=data.get("pageInfo", {}).get("totalResults", 0),
    )


def _fetch_durations(video_ids: list[str]) -> dict[str, int]:
    if not video_ids:
        return {}
    data = _get("videos", part="contentDetails", id=",".join(video_ids))
    return {
        item["id"]: _parse_duration(item["contentDetails"].get("duration", "PT0S"))
        for item in data.get("items", [])
    }


def get_content_breakdown(
    channel_id: str,
    sample_size: int = 50,
    exclude_shorts: bool = True,
) -> "ContentBreakdown":
    from _models import ContentBreakdown
    from _util import is_short

    logger.warning("search.list called (100 quota units) for channel %s", channel_id)
    data = _get(
        "search",
        part="id",
        channelId=channel_id,
        type="video",
        maxResults=min(sample_size, 50),
    )
    video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
    if not video_ids:
        return ContentBreakdown(by_category={}, by_topic={}, sample_size=0)

    details = _get(
        "videos",
        part="snippet,contentDetails,topicDetails",
        id=",".join(video_ids),
    )

    by_category: dict[str, int] = {}
    by_topic: dict[str, int] = {}
    analyzed = 0

    for item in details.get("items", []):
        duration = _parse_duration(item["contentDetails"].get("duration", "PT0S"))
        if exclude_shorts and is_short(duration):
            continue
        analyzed += 1

        category_id = item["snippet"].get("categoryId")
        if category_id:
            by_category[category_id] = by_category.get(category_id, 0) + 1

        topics = item.get("topicDetails", {}).get("topicCategories", [])
        for topic_url in topics:
            topic = topic_url.rstrip("/").split("/")[-1].replace("_", " ")
            by_topic[topic] = by_topic.get(topic, 0) + 1

    return ContentBreakdown(by_category=by_category, by_topic=by_topic, sample_size=analyzed)


def compare_channels(
    handle_or_id_a: str,
    handle_or_id_b: str,
) -> "ChannelComparison":
    from _models import ChannelComparison

    ch_a = get_channel(handle_or_id_a)
    ch_b = get_channel(handle_or_id_b)
    return ChannelComparison(
        channel_a=ch_a,
        channel_b=ch_b,
        top_videos_a=get_top_videos(ch_a.id, n=10, exclude_shorts=True),
        top_videos_b=get_top_videos(ch_b.id, n=10, exclude_shorts=True),
    )
