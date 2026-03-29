from __future__ import annotations

import os

import pytest


def test_cache_miss_when_file_absent(tmp_path, monkeypatch):
    import gartner
    monkeypatch.setattr(gartner, "CACHE_DIR", tmp_path)
    assert gartner._cache_get("missing", 3600) is None


def test_cache_hit_within_ttl(tmp_path, monkeypatch):
    import gartner
    monkeypatch.setattr(gartner, "CACHE_DIR", tmp_path)
    gartner._cache_set("mykey", {"segments": []})
    result = gartner._cache_get("mykey", 3600)
    assert result is not None
    assert "segments" in result
    assert "cached_at" in result


def test_cache_miss_when_expired(tmp_path, monkeypatch):
    import gartner
    monkeypatch.setattr(gartner, "CACHE_DIR", tmp_path)
    gartner._cache_set("mykey", {"segments": []})
    # backdate mtime by 2 hours
    p = tmp_path / "mykey.json"
    mtime = p.stat().st_mtime - 7200
    os.utime(p, (mtime, mtime))
    assert gartner._cache_get("mykey", 3600) is None
