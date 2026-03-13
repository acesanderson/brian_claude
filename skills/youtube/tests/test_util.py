from __future__ import annotations

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))


def test_extract_video_id_watch_url():
    from _util import extract_video_id
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_short_url():
    from _util import extract_video_id
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_embed_url():
    from _util import extract_video_id
    assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_bare_id():
    from _util import extract_video_id
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_video_id_invalid_raises():
    from _util import extract_video_id
    with pytest.raises(ValueError):
        extract_video_id("https://example.com/not-youtube")
