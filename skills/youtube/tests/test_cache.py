from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))


def test_transcript_cache_miss_returns_none(monkeypatch, tmp_path):
    import _cache
    monkeypatch.setattr(_cache, "CACHE_DIR", tmp_path)
    assert _cache.get_transcript_cache("nonexistent") is None


def test_transcript_cache_round_trip(monkeypatch, tmp_path):
    import _cache
    monkeypatch.setattr(_cache, "CACHE_DIR", tmp_path)
    data = {"language": "en", "snippets": [{"text": "hello", "start": 0.0, "duration": 1.0}]}
    _cache.set_transcript_cache("abc123", data)
    result = _cache.get_transcript_cache("abc123")
    assert result == data


def test_metadata_cache_miss_returns_none(monkeypatch, tmp_path):
    import _cache
    monkeypatch.setattr(_cache, "CACHE_DIR", tmp_path)
    assert _cache.get_metadata_cache("nonexistent") is None


def test_metadata_cache_round_trip(monkeypatch, tmp_path):
    import _cache
    monkeypatch.setattr(_cache, "CACHE_DIR", tmp_path)
    data = {"title": "My Video", "channel": "Test Channel", "duration": 300}
    _cache.set_metadata_cache("xyz789", data)
    result = _cache.get_metadata_cache("xyz789")
    assert result == data
