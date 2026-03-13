from __future__ import annotations

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))


def test_get_top_videos_raises_on_n_over_50(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "fake-key")
    from channel import get_top_videos
    with pytest.raises(ValueError, match="n must be"):
        get_top_videos("UCxxx", n=51)


def test_get_comments_raises_on_max_items_over_100(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "fake-key")
    from channel import get_comments
    with pytest.raises(ValueError, match="max_items must be"):
        get_comments("dQw4w9WgXcQ", max_items=101)


def test_channel_functions_raise_without_api_key(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    from channel import get_channel, MissingAPIKeyError
    with pytest.raises(MissingAPIKeyError):
        get_channel("@3blue1brown")


@pytest.mark.integration
def test_get_channel_3blue1brown():
    from channel import get_channel
    ch = get_channel("@3blue1brown")
    assert ch.title == "3Blue1Brown"
    assert ch.id.startswith("UC")
    assert ch.video_count > 0


_CHANNEL_ID = "UCYO_jab_esuFRV4b17AJtAw"
_PLAYLIST_ID = "PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab"  # Essence of Linear Algebra


@pytest.mark.integration
def test_get_top_videos_excludes_shorts():
    from channel import get_top_videos
    videos = get_top_videos(_CHANNEL_ID, n=5, exclude_shorts=True)
    assert len(videos) <= 5
    assert all(not v.is_short for v in videos)


@pytest.mark.integration
def test_get_top_videos_includes_shorts_when_not_excluded():
    from channel import get_channel, get_top_videos
    ch = get_channel("@MrBeast")
    videos = get_top_videos(ch.id, n=50, exclude_shorts=False)
    assert any(v.is_short for v in videos), "Expected at least one Short"


@pytest.mark.integration
def test_get_playlist_respects_max_items():
    from channel import get_playlist
    page = get_playlist(_PLAYLIST_ID, max_items=3)
    assert len(page.items) <= 3
    assert page.total_results > 0


@pytest.mark.integration
def test_get_playlist_pagination_returns_non_overlapping_pages():
    from channel import get_playlist
    page1 = get_playlist(_PLAYLIST_ID, max_items=3)
    assert page1.next_page_token is not None, "Playlist must have > 3 items for this test"
    page2 = get_playlist(_PLAYLIST_ID, max_items=3, page_token=page1.next_page_token)
    assert page1.items[0].id != page2.items[0].id


@pytest.mark.integration
def test_get_comments_respects_max_items():
    from channel import get_comments
    page = get_comments("aircAruvnKk", max_items=5)
    assert len(page.items) <= 5
