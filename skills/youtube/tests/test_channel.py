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
