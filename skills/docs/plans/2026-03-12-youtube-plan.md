# YouTube Skill Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single `youtube` Claude Code skill consolidating channel analytics, playlist/comment fetching, transcript retrieval, Whisper transcription, chapter extraction, and keyword search — replacing `youtube-intel` and `yt-transcript`.

**Architecture:** Four focused modules (`_util`, `_cache`, `video`, `channel`) plus shared data models in `_models.py`. All functions are synchronous. `video.py` functions work without an API key; `channel.py` functions require `YOUTUBE_API_KEY`. A SQLite cache at `~/.cache/youtube/` serves both transcript and metadata lookups.

**Tech Stack:** `httpx`, `youtube-transcript-api>=1.2.4`, `yt-dlp`, `faster-whisper`, `pytest`, `pytest-mock`

**Spec:** `~/.claude/skills/docs/plans/2026-03-12-youtube-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `~/.claude/skills/youtube/pyproject.toml` | Dependency manifest; `uv run --directory` entrypoint |
| `~/.claude/skills/youtube/scripts/_models.py` | All dataclasses shared across modules |
| `~/.claude/skills/youtube/scripts/_util.py` | `extract_video_id`, `is_short` |
| `~/.claude/skills/youtube/scripts/_cache.py` | SQLite read/write for transcripts and metadata |
| `~/.claude/skills/youtube/scripts/video.py` | `get_transcript`, `transcribe_whisper`, `get_metadata`, `list_transcripts`, `get_chapters`, `search_transcript` |
| `~/.claude/skills/youtube/scripts/channel.py` | `get_channel`, `get_top_videos`, `get_content_breakdown`, `compare_channels`, `get_playlist`, `get_comments` |
| `~/.claude/skills/youtube/SKILL.md` | Human-readable usage doc |
| `~/.claude/skills/youtube/tests/conftest.py` | Shared fixtures and pytest marks |
| `~/.claude/skills/youtube/tests/test_util.py` | Unit tests for `_util.py` |
| `~/.claude/skills/youtube/tests/test_cache.py` | Unit tests for `_cache.py` |
| `~/.claude/skills/youtube/tests/test_models.py` | Unit tests for `_models.py` invariants |
| `~/.claude/skills/youtube/tests/test_video.py` | Unit + integration tests for `video.py` |
| `~/.claude/skills/youtube/tests/test_channel.py` | Unit + integration tests for `channel.py` |

---

## Chunk 1: Scaffolding + _util.py

### Task 1: Project scaffolding

**Files:**
- Create: `~/.claude/skills/youtube/pyproject.toml`
- Create: `~/.claude/skills/youtube/tests/conftest.py`
- Create: `~/.claude/skills/youtube/scripts/__init__.py` (empty)
- Create: `~/.claude/skills/youtube/tests/__init__.py` (empty)

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "youtube"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27",
    "youtube-transcript-api>=1.2.4",
    "yt-dlp",
    "faster-whisper",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-mock"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "integration: requires network access and YOUTUBE_API_KEY",
]
```

- [ ] **Step 2: Create tests/conftest.py**

```python
from __future__ import annotations

import os
import pytest

# Skip all integration tests unless YOUTUBE_API_KEY is set
def pytest_collection_modifyitems(config, items):
    skip_integration = pytest.mark.skip(reason="YOUTUBE_API_KEY not set")
    for item in items:
        if "integration" in item.keywords and not os.getenv("YOUTUBE_API_KEY"):
            item.add_marker(skip_integration)
```

- [ ] **Step 3: Create empty __init__.py files**

```bash
mkdir -p ~/.claude/skills/youtube/scripts
mkdir -p ~/.claude/skills/youtube/tests
touch ~/.claude/skills/youtube/scripts/__init__.py
touch ~/.claude/skills/youtube/tests/__init__.py
```

- [ ] **Step 4: Verify pytest collects zero tests (not an error)**

```bash
cd ~/.claude/skills/youtube
uv run --with pytest --with pytest-mock pytest tests/ -v
```

Expected: `no tests ran` or `collected 0 items`

- [ ] **Step 5: Commit**

```bash
cd ~/.claude/skills/youtube
git add pyproject.toml tests/conftest.py scripts/__init__.py tests/__init__.py
git commit -m "feat(youtube): scaffold project structure"
```

---

### Task 2: _util.py — extract_video_id

**Fulfills:** AC-U1, AC-U2, AC-U3, AC-U4, AC-U5

**Files:**
- Create: `~/.claude/skills/youtube/scripts/_util.py`
- Create: `~/.claude/skills/youtube/tests/test_util.py`

#### AC-U1: watch?v= URL format

- [ ] **Step 1: Write failing test (AC-U1)**

```python
# tests/test_util.py
from __future__ import annotations
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))

def test_extract_video_id_watch_url():
    from _util import extract_video_id
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd ~/.claude/skills/youtube
uv run --with pytest pytest tests/test_util.py::test_extract_video_id_watch_url -v
```

Expected: FAIL with `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/_util.py
from __future__ import annotations
import re
from urllib.parse import urlparse, parse_qs


def extract_video_id(url_or_id: str) -> str:
    parsed = urlparse(url_or_id)
    if "youtube.com" in parsed.netloc and parsed.path == "/watch":
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
    raise ValueError(f"Cannot extract video ID from: {url_or_id!r}")


def is_short(duration_seconds: int) -> bool:
    return duration_seconds < 60
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd ~/.claude/skills/youtube
uv run --with pytest pytest tests/test_util.py::test_extract_video_id_watch_url -v
```

Expected: PASS

#### AC-U2: youtu.be/ short URL format

- [ ] **Step 5: Write failing test (AC-U2)**

```python
# Add to tests/test_util.py
def test_extract_video_id_short_url():
    from _util import extract_video_id
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
```

- [ ] **Step 6: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_util.py::test_extract_video_id_short_url -v
```

Expected: FAIL with `ValueError`

- [ ] **Step 7: Extend implementation to handle youtu.be**

```python
# Update extract_video_id in scripts/_util.py
def extract_video_id(url_or_id: str) -> str:
    parsed = urlparse(url_or_id)

    if parsed.netloc in ("youtu.be", "www.youtu.be"):
        vid = parsed.path.lstrip("/")
        if vid:
            return vid[:11]

    if "youtube.com" in parsed.netloc and parsed.path == "/watch":
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]

    raise ValueError(f"Cannot extract video ID from: {url_or_id!r}")
```

- [ ] **Step 8: Run test to verify it passes**

```bash
uv run --with pytest pytest tests/test_util.py::test_extract_video_id_short_url -v
```

Expected: PASS

#### AC-U3: /embed/ URL format

- [ ] **Step 9: Write failing test (AC-U3)**

```python
# Add to tests/test_util.py
def test_extract_video_id_embed_url():
    from _util import extract_video_id
    assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
```

- [ ] **Step 10: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_util.py::test_extract_video_id_embed_url -v
```

Expected: FAIL with `ValueError`

- [ ] **Step 11: Extend implementation to handle /embed/**

```python
# Update extract_video_id in scripts/_util.py — add before the final raise:
    if "youtube.com" in parsed.netloc and parsed.path.startswith("/embed/"):
        vid = parsed.path[7:]
        if vid:
            return vid[:11]
```

- [ ] **Step 12: Run test to verify it passes**

```bash
uv run --with pytest pytest tests/test_util.py::test_extract_video_id_embed_url -v
```

Expected: PASS

#### AC-U4: bare 11-char video ID

- [ ] **Step 13: Write failing test (AC-U4)**

```python
# Add to tests/test_util.py
def test_extract_video_id_bare_id():
    from _util import extract_video_id
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
```

- [ ] **Step 14: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_util.py::test_extract_video_id_bare_id -v
```

Expected: FAIL with `ValueError`

- [ ] **Step 15: Extend implementation to handle bare IDs (add at top of function)**

```python
# Update extract_video_id in scripts/_util.py — insert as first check:
    if re.match(r"^[A-Za-z0-9_-]{11}$", url_or_id):
        return url_or_id
```

- [ ] **Step 16: Run test to verify it passes**

```bash
uv run --with pytest pytest tests/test_util.py::test_extract_video_id_bare_id -v
```

Expected: PASS

#### AC-U5: invalid input raises ValueError

- [ ] **Step 17: Write failing test (AC-U5)**

```python
# Add to tests/test_util.py
def test_extract_video_id_invalid_raises():
    from _util import extract_video_id
    with pytest.raises(ValueError):
        extract_video_id("not-a-video")
```

- [ ] **Step 18: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_util.py::test_extract_video_id_invalid_raises -v
```

Expected: FAIL (the current implementation raises ValueError but need to verify it works with a short non-ID string)

- [ ] **Step 19: Run all _util tests together**

```bash
uv run --with pytest pytest tests/test_util.py -v
```

Expected: All 5 tests PASS

- [ ] **Step 20: Commit**

```bash
git add scripts/_util.py tests/test_util.py
git commit -m "feat(youtube): add _util.py with extract_video_id (AC-U1..U5)"
```

---

## Chunk 2: _models.py + _cache.py

### Task 3: Data models with invariant enforcement

**Fulfills:** AC-U10

**Files:**
- Create: `~/.claude/skills/youtube/scripts/_models.py`
- Create: `~/.claude/skills/youtube/tests/test_models.py`

- [ ] **Step 1: Write failing test (AC-U10)**

```python
# tests/test_models.py
from __future__ import annotations
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))

def test_whisper_transcript_cannot_have_is_generated_true():
    from _models import Transcript
    with pytest.raises(ValueError, match="is_generated must be False"):
        Transcript(
            language="English",
            language_code="en",
            is_generated=True,
            source="whisper",
            snippets=[],
            text="",
        )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_models.py::test_whisper_transcript_cannot_have_is_generated_true -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write _models.py with all dataclasses**

```python
# scripts/_models.py
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ChannelProfile:
    id: str
    title: str
    handle: str | None          # WITHOUT leading "@"
    subscriber_count: int | None
    total_view_count: int
    video_count: int
    upload_frequency_days: float | None
    created_at: str             # ISO 8601


@dataclass
class Video:
    id: str
    title: str
    view_count: int
    like_count: int | None
    duration_seconds: int
    is_short: bool              # duration_seconds < 60
    published_at: str           # ISO 8601
    category: str | None
    topics: list[str]


@dataclass
class PlaylistItem:
    id: str
    title: str
    position: int
    duration_seconds: int
    is_short: bool
    published_at: str           # ISO 8601


@dataclass
class PlaylistPage:
    items: list[PlaylistItem]
    next_page_token: str | None
    total_results: int


@dataclass
class Comment:
    id: str
    text: str
    author: str
    like_count: int
    published_at: str           # ISO 8601
    reply_count: int


@dataclass
class CommentPage:
    items: list[Comment]
    next_page_token: str | None


@dataclass
class ContentBreakdown:
    by_category: dict[str, int]
    by_topic: dict[str, int]
    sample_size: int            # count AFTER short filtering


@dataclass
class ChannelComparison:
    channel_a: ChannelProfile
    channel_b: ChannelProfile
    top_videos_a: list[Video]
    top_videos_b: list[Video]


@dataclass
class Snippet:
    text: str
    start: float
    duration: float


@dataclass
class Transcript:
    language: str
    language_code: str
    is_generated: bool          # True only for YouTube auto-captions; always False for whisper
    source: str                 # "caption" | "whisper"
    snippets: list[Snippet]
    text: str                   # space-joined full text

    def __post_init__(self) -> None:
        if self.source == "whisper" and self.is_generated:
            raise ValueError("is_generated must be False when source='whisper'")


@dataclass
class TranscriptMeta:
    language: str
    language_code: str
    is_generated: bool
    is_translatable: bool


@dataclass
class VideoMetadata:
    video_id: str
    title: str
    channel: str
    duration: int               # seconds
    published_date: str         # ISO 8601 (YYYY-MM-DD)
    description: str
    tags: list[str]
    url: str


@dataclass
class Chapter:
    title: str
    start: float                # seconds


@dataclass
class TranscriptHit:
    start: float                # seconds
    text: str
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run --with pytest pytest tests/test_models.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/_models.py tests/test_models.py
git commit -m "feat(youtube): add _models.py with dataclasses and Transcript invariant (AC-U10)"
```

---

### Task 4: _cache.py — transcript and metadata SQLite cache

**Files:**
- Create: `~/.claude/skills/youtube/scripts/_cache.py`
- Create: `~/.claude/skills/youtube/tests/test_cache.py`

- [ ] **Step 1: Write failing tests for transcript cache round-trip**

```python
# tests/test_cache.py
from __future__ import annotations
import pytest
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))


@pytest.fixture(autouse=True)
def tmp_cache_dir(tmp_path, monkeypatch):
    """Redirect cache to a temp directory for all cache tests."""
    import _cache
    monkeypatch.setattr(_cache, "CACHE_DIR", tmp_path)


def test_transcript_cache_miss_returns_none():
    from _cache import get_transcript_cache
    assert get_transcript_cache("dQw4w9WgXcQ") is None


def test_transcript_cache_round_trip():
    from _cache import get_transcript_cache, set_transcript_cache
    data = {"language": "en", "snippets": [{"text": "hello", "start": 0.0, "duration": 1.0}]}
    set_transcript_cache("dQw4w9WgXcQ", data)
    assert get_transcript_cache("dQw4w9WgXcQ") == data


def test_metadata_cache_miss_returns_none():
    from _cache import get_metadata_cache
    assert get_metadata_cache("dQw4w9WgXcQ") is None


def test_metadata_cache_round_trip():
    from _cache import get_metadata_cache, set_metadata_cache
    data = {"title": "Never Gonna Give You Up", "channel": "Rick Astley"}
    set_metadata_cache("dQw4w9WgXcQ", data)
    assert get_metadata_cache("dQw4w9WgXcQ") == data
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_cache.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write _cache.py**

```python
# scripts/_cache.py
from __future__ import annotations
import json
import sqlite3
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "youtube"


def _connect(db_name: str) -> sqlite3.Connection:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(CACHE_DIR / db_name)


def get_transcript_cache(video_id: str) -> dict | None:
    with _connect("transcripts.db") as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS transcripts "
            "(video_id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        row = conn.execute(
            "SELECT data FROM transcripts WHERE video_id = ?", (video_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def set_transcript_cache(video_id: str, data: dict) -> None:
    with _connect("transcripts.db") as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS transcripts "
            "(video_id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO transcripts (video_id, data) VALUES (?, ?)",
            (video_id, json.dumps(data)),
        )


def get_metadata_cache(video_id: str) -> dict | None:
    with _connect("metadata.db") as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS metadata "
            "(video_id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        row = conn.execute(
            "SELECT data FROM metadata WHERE video_id = ?", (video_id,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def set_metadata_cache(video_id: str, data: dict) -> None:
    with _connect("metadata.db") as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS metadata "
            "(video_id TEXT PRIMARY KEY, data TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO metadata (video_id, data) VALUES (?, ?)",
            (video_id, json.dumps(data)),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_cache.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/_cache.py tests/test_cache.py
git commit -m "feat(youtube): add _cache.py with SQLite transcript/metadata cache"
```

---

## Chunk 3: video.py

### Task 5: search_transcript — validation and matching

**Fulfills:** AC-U9, AC-U11, AC-U12

**Files:**
- Create: `~/.claude/skills/youtube/scripts/video.py` (initial, grows across tasks)
- Create: `~/.claude/skills/youtube/tests/test_video.py`

#### AC-U9: empty query raises ValueError

- [ ] **Step 1: Write failing test (AC-U9)**

```python
# tests/test_video.py
from __future__ import annotations
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))


def test_search_transcript_empty_query_raises():
    from video import search_transcript
    with pytest.raises(ValueError, match="query must not be empty"):
        search_transcript("dQw4w9WgXcQ", "")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_video.py::test_search_transcript_empty_query_raises -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal video.py with search_transcript stub**

```python
# scripts/video.py
from __future__ import annotations
import logging
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger("youtube")


def extract_video_id(url_or_id: str) -> str:
    from _util import extract_video_id as _extract
    return _extract(url_or_id)


def get_transcript(url_or_id: str, **kwargs) -> "Transcript":
    raise NotImplementedError("get_transcript is implemented in Task 6")


def search_transcript(url_or_id: str, query: str) -> list:
    from _models import TranscriptHit
    if not query:
        raise ValueError("query must not be empty")
    # Full implementation added in Task 5, Step 7 once get_transcript stub exists above
    return []
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run --with pytest pytest tests/test_video.py::test_search_transcript_empty_query_raises -v
```

Expected: PASS

#### AC-U11: search returns matching snippets (case-insensitive)

- [ ] **Step 5: Write failing test (AC-U11)**

```python
# Add to tests/test_video.py
def test_search_transcript_returns_matching_snippets(mocker):
    from _models import Transcript, Snippet
    from video import search_transcript

    mock_transcript = Transcript(
        language="English",
        language_code="en",
        is_generated=False,
        source="caption",
        snippets=[
            Snippet(text="Backpropagation is a key algorithm", start=10.0, duration=3.0),
            Snippet(text="gradient descent in neural nets", start=14.0, duration=2.5),
            Snippet(text="BACKPROPAGATION computes gradients", start=20.0, duration=3.0),
        ],
        text="Backpropagation is a key algorithm gradient descent in neural nets BACKPROPAGATION computes gradients",
    )
    mocker.patch("video.get_transcript", return_value=mock_transcript)

    hits = search_transcript("dQw4w9WgXcQ", "backpropagation")
    assert len(hits) == 2
    assert hits[0].start == 10.0
    assert hits[1].start == 20.0
```

- [ ] **Step 6: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_video.py::test_search_transcript_returns_matching_snippets -v
```

Expected: FAIL (returns empty list, expected 2 hits)

- [ ] **Step 7: Implement search_transcript fully**

```python
# Update search_transcript in scripts/video.py
def search_transcript(url_or_id: str, query: str) -> list:
    from _models import TranscriptHit
    if not query:
        raise ValueError("query must not be empty")
    transcript = get_transcript(url_or_id)
    lower_query = query.lower()
    return [
        TranscriptHit(start=s.start, text=s.text)
        for s in transcript.snippets
        if lower_query in s.text.lower()
    ]
```

Note: `get_transcript` is defined in Task 6. For now the test mocks it, so this works.

- [ ] **Step 8: Run test to verify it passes**

```bash
uv run --with pytest pytest tests/test_video.py::test_search_transcript_returns_matching_snippets -v
```

Expected: PASS

#### AC-U12: search returns [] when no snippets match

- [ ] **Step 9: Write failing test (AC-U12)**

```python
# Add to tests/test_video.py
def test_search_transcript_no_match_returns_empty(mocker):
    from _models import Transcript, Snippet
    from video import search_transcript

    mock_transcript = Transcript(
        language="English",
        language_code="en",
        is_generated=False,
        source="caption",
        snippets=[Snippet(text="hello world", start=0.0, duration=1.0)],
        text="hello world",
    )
    mocker.patch("video.get_transcript", return_value=mock_transcript)

    hits = search_transcript("dQw4w9WgXcQ", "eigenvalue")
    assert hits == []
```

- [ ] **Step 10: Run test to verify it passes immediately (implementation already handles this)**

```bash
uv run --with pytest pytest tests/test_video.py::test_search_transcript_no_match_returns_empty -v
```

Expected: PASS (no code change needed)

- [ ] **Step 11: Commit**

```bash
git add scripts/video.py tests/test_video.py
git commit -m "feat(youtube): add search_transcript with validation (AC-U9, U11, U12)"
```

---

### Task 6: get_transcript — validation and caching

**Fulfills:** AC-U6, AC-I7

**Files:**
- Modify: `~/.claude/skills/youtube/scripts/video.py`
- Modify: `~/.claude/skills/youtube/tests/test_video.py`

#### AC-U6: languages + fallback_whisper raises ValueError

- [ ] **Step 1: Write failing test (AC-U6)**

```python
# Add to tests/test_video.py
def test_get_transcript_languages_and_fallback_whisper_raises():
    from video import get_transcript
    with pytest.raises(ValueError, match="mutually exclusive"):
        get_transcript("dQw4w9WgXcQ", languages=["fr"], fallback_whisper=True)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_video.py::test_get_transcript_languages_and_fallback_whisper_raises -v
```

Expected: FAIL with `ModuleNotFoundError` (get_transcript not yet defined) or attribute error

- [ ] **Step 3: Add get_transcript to video.py**

```python
# Add to scripts/video.py
from youtube_transcript_api import YouTubeTranscriptApi


def get_transcript(
    url_or_id: str,
    languages: list[str] | None = None,
    prefer_manual: bool = True,
    fallback_whisper: bool = False,
) -> "Transcript":
    from _models import Transcript, Snippet
    from _util import extract_video_id
    from _cache import get_transcript_cache, set_transcript_cache

    if languages is not None and fallback_whisper:
        raise ValueError(
            "languages and fallback_whisper are mutually exclusive: "
            "Whisper transcribes the video's spoken language, not a requested language"
        )

    video_id = extract_video_id(url_or_id)
    use_cache = languages is None

    if use_cache:
        cached = get_transcript_cache(video_id)
        if cached:
            logger.debug("transcript cache hit for %s", video_id)
            return Transcript(
                language=cached["language"],
                language_code=cached["language_code"],
                is_generated=cached["is_generated"],
                source="caption",
                snippets=[
                    Snippet(text=s["text"], start=s["start"], duration=s["duration"])
                    for s in cached["snippets"]
                ],
                text=cached["text"],
            )
        logger.debug("transcript cache miss for %s", video_id)

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        if prefer_manual:
            try:
                t = transcript_list.find_manually_created_transcript(
                    languages or ["en"]
                )
            except NoTranscriptFound:
                t = transcript_list.find_generated_transcript(languages or ["en"])
        else:
            t = transcript_list.find_transcript(languages or ["en"])

        raw = t.fetch()
        snippets = [
            Snippet(text=s["text"], start=s["start"], duration=s["duration"])
            for s in raw
        ]
        transcript = Transcript(
            language=t.language,
            language_code=t.language_code,
            is_generated=t.is_generated,
            source="caption",
            snippets=snippets,
            text=" ".join(s.text for s in snippets),
        )

        if use_cache:
            set_transcript_cache(video_id, {
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "snippets": [
                    {"text": s.text, "start": s.start, "duration": s.duration}
                    for s in snippets
                ],
                "text": transcript.text,
            })

        return transcript

    except (TranscriptsDisabled, NoTranscriptFound) as exc:
        # Only fall back to Whisper for missing-caption errors.
        # Quota errors, network errors, and invalid keys must propagate unchanged.
        if fallback_whisper:
            logger.warning(
                "caption unavailable; falling back to Whisper for %s", video_id
            )
            return transcribe_whisper(url_or_id)
        raise
```

Note: Add these imports at the top of the `get_transcript` function body (or at the module top):
```python
from youtube_transcript_api import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run --with pytest pytest tests/test_video.py::test_get_transcript_languages_and_fallback_whisper_raises -v
```

Expected: PASS

#### AC-I7: second call for same video uses cache (no second network call)

- [ ] **Step 5: Write failing test (AC-I7)**

```python
# Add to tests/test_video.py
def test_get_transcript_uses_cache_on_second_call(mocker, tmp_path, monkeypatch):
    import _cache
    from _models import Transcript, Snippet
    monkeypatch.setattr(_cache, "CACHE_DIR", tmp_path)

    mock_fetch = mocker.patch("youtube_transcript_api.YouTubeTranscriptApi.list_transcripts")
    mock_t = mocker.MagicMock()
    mock_t.language = "English"
    mock_t.language_code = "en"
    mock_t.is_generated = False
    mock_t.fetch.return_value = [{"text": "hello", "start": 0.0, "duration": 1.0}]
    mock_list = mocker.MagicMock()
    mock_list.find_manually_created_transcript.return_value = mock_t
    mock_fetch.return_value = mock_list

    from video import get_transcript
    get_transcript("dQw4w9WgXcQ")
    get_transcript("dQw4w9WgXcQ")

    assert mock_fetch.call_count == 1  # network called only once
```

- [ ] **Step 6: Run test to verify it fails or passes**

```bash
uv run --with pytest pytest tests/test_video.py::test_get_transcript_uses_cache_on_second_call -v
```

Expected: PASS (implementation already writes to cache on first call and reads on second)

If it fails due to monkeypatching issues, ensure `_cache.CACHE_DIR` is correctly patched before the import.

- [ ] **Step 7: Run all video tests**

```bash
uv run --with pytest pytest tests/test_video.py -v
```

Expected: All tests PASS

- [ ] **Step 8: Commit**

```bash
git add scripts/video.py tests/test_video.py
git commit -m "feat(youtube): add get_transcript with validation and caching (AC-U6, AC-I7)"
```

---

### Task 7: get_chapters — parsing and failure modes

**Fulfills:** AC-I8, AC-I9

**Files:**
- Modify: `~/.claude/skills/youtube/scripts/video.py`
- Modify: `~/.claude/skills/youtube/tests/test_video.py`

#### AC-I8: parses standard chapter format from description

- [ ] **Step 1: Write failing test (AC-I8)**

```python
# Add to tests/test_video.py
def test_get_chapters_parses_standard_format(mocker):
    from video import get_chapters

    description = (
        "A great video about math.\n\n"
        "0:00 Introduction\n"
        "3:45 Main concept\n"
        "10:22 Conclusion\n"
    )
    mock_info = {"description": description}
    mocker.patch("yt_dlp.YoutubeDL.__init__", return_value=None)
    mocker.patch("yt_dlp.YoutubeDL.extract_info", return_value=mock_info)

    chapters = get_chapters("dQw4w9WgXcQ")
    assert len(chapters) == 3
    assert chapters[0].title == "Introduction"
    assert chapters[0].start == 0.0
    assert chapters[1].title == "Main concept"
    assert abs(chapters[1].start - 225.0) < 0.01  # 3*60 + 45
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_video.py::test_get_chapters_parses_standard_format -v
```

Expected: FAIL with `AttributeError` or `ImportError`

- [ ] **Step 3: Implement get_chapters**

```python
# Add to scripts/video.py
import re as _re
import yt_dlp


def get_chapters(url_or_id: str) -> list:
    from _models import Chapter
    from _util import extract_video_id

    video_id = extract_video_id(url_or_id)
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    description = (info or {}).get("description", "") or ""

    # Match lines like: 0:00, 1:23, 10:22, 1:23:45
    pattern = _re.compile(
        r"^(\d+:\d{2}(?::\d{2})?)\s+(.+)$", _re.MULTILINE
    )

    chapters = []
    for m in pattern.finditer(description):
        timestamp, title = m.group(1), m.group(2).strip()
        parts = timestamp.split(":")
        if len(parts) == 2:
            start = int(parts[0]) * 60 + int(parts[1])
        else:
            start = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        chapters.append(Chapter(title=title, start=float(start)))

    return chapters
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run --with pytest pytest tests/test_video.py::test_get_chapters_parses_standard_format -v
```

Expected: PASS

#### AC-I9: returns [] when description has no chapter markers

- [ ] **Step 5: Write failing test (AC-I9)**

```python
# Add to tests/test_video.py
def test_get_chapters_returns_empty_when_no_chapters(mocker):
    from video import get_chapters

    mock_info = {"description": "Just a video with no chapters here."}
    mocker.patch("yt_dlp.YoutubeDL.__init__", return_value=None)
    mocker.patch("yt_dlp.YoutubeDL.extract_info", return_value=mock_info)

    assert get_chapters("dQw4w9WgXcQ") == []
```

- [ ] **Step 6: Run test to verify it fails**

```bash
uv run --with pytest pytest tests/test_video.py::test_get_chapters_returns_empty_when_no_chapters -v
```

Expected: FAIL (function not yet handling no-chapter case — though the implementation from Step 3 may already handle it; if PASS, no code change needed)

- [ ] **Step 7: Confirm implementation handles the no-chapter case**

The `pattern.finditer` on a description with no timestamp lines will yield zero matches, so `chapters` will be `[]`. No code change needed if the test passes already.

- [ ] **Step 8: Run test to verify it passes**

```bash
uv run --with pytest pytest tests/test_video.py::test_get_chapters_returns_empty_when_no_chapters -v
```

Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add scripts/video.py tests/test_video.py
git commit -m "feat(youtube): add get_chapters with description parsing (AC-I8, AC-I9)"
```

---

### Task 8: transcribe_whisper — audio cleanup guarantee

**Fulfills:** AC-I10

**Files:**
- Modify: `~/.claude/skills/youtube/scripts/video.py`
- Modify: `~/.claude/skills/youtube/tests/test_video.py`

- [ ] **Step 1: Write failing test (AC-I10)**

```python
# Add to tests/test_video.py
def test_transcribe_whisper_deletes_temp_audio_on_success(mocker, tmp_path):
    from video import transcribe_whisper
    import _cache

    # Create a fake audio file that yt-dlp "downloads"
    audio_file = tmp_path / "youtube" / "tmp" / "dQw4w9WgXcQ.m4a"
    audio_file.parent.mkdir(parents=True, exist_ok=True)
    audio_file.write_text("fake audio")

    mocker.patch("video._download_audio", return_value=audio_file)

    mock_model = mocker.MagicMock()
    mock_model.transcribe.return_value = (
        [mocker.MagicMock(text="hello", start=0.0, end=1.0)],
        mocker.MagicMock(language="en"),
    )
    mocker.patch("faster_whisper.WhisperModel", return_value=mock_model)

    transcribe_whisper("dQw4w9WgXcQ")
    assert not audio_file.exists()


def test_transcribe_whisper_deletes_temp_audio_on_failure(mocker, tmp_path):
    from video import transcribe_whisper

    audio_file = tmp_path / "youtube" / "tmp" / "dQw4w9WgXcQ.m4a"
    audio_file.parent.mkdir(parents=True, exist_ok=True)
    audio_file.write_text("fake audio")

    mocker.patch("video._download_audio", return_value=audio_file)
    mocker.patch("faster_whisper.WhisperModel", side_effect=RuntimeError("model error"))

    with pytest.raises(Exception):
        transcribe_whisper("dQw4w9WgXcQ")

    assert not audio_file.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_video.py::test_transcribe_whisper_deletes_temp_audio_on_success tests/test_video.py::test_transcribe_whisper_deletes_temp_audio_on_failure -v
```

Expected: FAIL

- [ ] **Step 3: Implement transcribe_whisper with cleanup guarantee**

```python
# Add near the top of scripts/video.py (after imports, before functions)
import faster_whisper
from pathlib import Path as _Path
from youtube_transcript_api import VideoUnavailable


class WhisperTranscriptionError(Exception):
    pass


def _download_audio(video_id: str) -> _Path:
    """Download audio-only stream to ~/.cache/youtube/tmp/. Returns path to file."""
    tmp_dir = _Path.home() / ".cache" / "youtube" / "tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_template = str(tmp_dir / f"{video_id}.%(ext)s")
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = info.get("ext", "m4a")

    result = tmp_dir / f"{video_id}.{ext}"
    logger.debug("temp audio file created: %s", result)
    return result


def transcribe_whisper(url_or_id: str, model: str = "small") -> "Transcript":
    from _models import Transcript, Snippet
    from _util import extract_video_id

    video_id = extract_video_id(url_or_id)
    logger.warning(
        "starting Whisper transcription for %s (model=%s); this may be slow", video_id, model
    )

    audio_path = _download_audio(video_id)
    try:
        whisper_model = faster_whisper.WhisperModel(model)
        segments, info = whisper_model.transcribe(str(audio_path))
        snippets = [
            Snippet(text=seg.text.strip(), start=seg.start, duration=seg.end - seg.start)
            for seg in segments
        ]
        return Transcript(
            language=info.language,
            language_code=info.language,
            is_generated=False,
            source="whisper",
            snippets=snippets,
            text=" ".join(s.text for s in snippets),
        )
    except Exception as exc:
        raise WhisperTranscriptionError(
            f"Whisper transcription failed for {video_id}: {exc}"
        ) from exc
    finally:
        if audio_path.exists():
            audio_path.unlink()
            logger.debug("temp audio file deleted: %s", audio_path)
        else:
            logger.error("temp audio file not found for cleanup: %s", audio_path)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_video.py::test_transcribe_whisper_deletes_temp_audio_on_success tests/test_video.py::test_transcribe_whisper_deletes_temp_audio_on_failure -v
```

Expected: PASS

- [ ] **Step 5: Run all video tests**

```bash
uv run --with pytest pytest tests/test_video.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/video.py tests/test_video.py
git commit -m "feat(youtube): add transcribe_whisper with cleanup guarantee (AC-I10)"
```

---

## Chunk 4: channel.py

### Task 9: MissingAPIKeyError + input validation guards

**Fulfills:** AC-U7, AC-U8 (and the MissingAPIKeyError behavior in error table)

**Files:**
- Create: `~/.claude/skills/youtube/scripts/channel.py`
- Create: `~/.claude/skills/youtube/tests/test_channel.py`

- [ ] **Step 1: Write failing tests (AC-U7, AC-U8)**

```python
# tests/test_channel.py
from __future__ import annotations
import pytest
import sys
import os
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run --with pytest pytest tests/test_channel.py -v
```

Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write channel.py with validation guards and MissingAPIKeyError**

```python
# scripts/channel.py
from __future__ import annotations
import logging
import os
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from _models import (
        ChannelProfile, Video, ContentBreakdown, ChannelComparison,
        PlaylistPage, CommentPage,
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

    video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
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
            # YouTube returns 403 for both quota-exceeded and commentsDisabled.
            # Distinguish by the error reason in the response body.
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


def _parse_duration(iso: str) -> int:
    """Parse ISO 8601 duration (e.g. PT3M45S) to seconds."""
    import re
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not m:
        return 0
    h, mins, s = m.group(1), m.group(2), m.group(3)
    return int(h or 0) * 3600 + int(mins or 0) * 60 + int(s or 0)


def get_channel(handle_or_id: str) -> "ChannelProfile":
    # Stub — full implementation in Task 10
    _api_key()  # raises MissingAPIKeyError if not set
    raise NotImplementedError
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run --with pytest pytest tests/test_channel.py -v
```

Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/channel.py tests/test_channel.py
git commit -m "feat(youtube): add channel.py with validation guards and MissingAPIKeyError (AC-U7, U8)"
```

---

### Task 10: get_channel — full implementation

**Fulfills:** AC-I1

**Files:**
- Modify: `~/.claude/skills/youtube/scripts/channel.py`
- Modify: `~/.claude/skills/youtube/tests/test_channel.py`

- [ ] **Step 1: Write integration test (AC-I1)**

```python
# Add to tests/test_channel.py
import pytest

@pytest.mark.integration
def test_get_channel_3blue1brown():
    from channel import get_channel
    ch = get_channel("@3blue1brown")
    assert ch.title == "3Blue1Brown"
    assert ch.id.startswith("UC")
    assert ch.video_count > 0
```

- [ ] **Step 2: Run test to verify it is skipped (no API key in CI) or fails**

```bash
uv run --with pytest pytest tests/test_channel.py::test_get_channel_3blue1brown -v
```

Expected: SKIP (if `YOUTUBE_API_KEY` not set) or FAIL with `NotImplementedError`

- [ ] **Step 3: Implement get_channel fully**

```python
# Replace the get_channel stub in scripts/channel.py
def get_channel(handle_or_id: str) -> "ChannelProfile":
    from _models import ChannelProfile

    # Resolve @handle to channel ID
    handle = handle_or_id.lstrip("@")
    if handle_or_id.startswith("UC") and not handle_or_id.startswith("@"):
        channel_id = handle_or_id
    else:
        data = _get("channels", part="id", forHandle=handle)
        items = data.get("items", [])
        if not items:
            raise ChannelNotFoundError(f"No channel found for handle: {handle_or_id!r}")
        channel_id = items[0]["id"]

    # Fetch full channel details
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

    # Compute upload frequency from uploads playlist
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
    """Return avg days between 10 most recent uploads. None if < 2 videos."""
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
```

- [ ] **Step 4: Run integration test (if API key available)**

```bash
uv run --with pytest pytest tests/test_channel.py::test_get_channel_3blue1brown -v
```

Expected: PASS (or SKIP if no API key)

- [ ] **Step 5: Commit**

```bash
git add scripts/channel.py tests/test_channel.py
git commit -m "feat(youtube): implement get_channel (AC-I1)"
```

---

### Task 11: get_top_videos + get_playlist + get_comments integration tests

**Fulfills:** AC-I2, AC-I3, AC-I4, AC-I5, AC-I6

**Files:**
- Modify: `~/.claude/skills/youtube/scripts/channel.py`
- Modify: `~/.claude/skills/youtube/tests/test_channel.py`

Note: `get_top_videos`, `get_playlist`, and `get_comments` bodies were written in Task 9. This task adds the integration tests and adds `get_playlist` and `get_content_breakdown`/`compare_channels` to channel.py.

- [ ] **Step 1: Write integration tests (AC-I2, AC-I3, AC-I4, AC-I5, AC-I6)**

```python
# Add to tests/test_channel.py

# Known channel and playlist for 3Blue1Brown
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
    # MrBeast publishes Shorts heavily; as of 2026-03, top-50 by viewCount
    # reliably includes sub-60s videos. If this test starts failing, verify
    # MrBeast still publishes Shorts and pick a different channel if needed.
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
    # Use a popular video with comments
    page = get_comments("aircAruvnKk", max_items=5)
    assert len(page.items) <= 5
```

- [ ] **Step 2: Add get_playlist to channel.py**

```python
# Add to scripts/channel.py
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
        # _get calls raise_for_status(); a 404 means the playlist doesn't exist
        if exc.response.status_code == 404:
            raise PlaylistNotFoundError(f"Playlist not found: {playlist_id}") from exc
        raise

    if not data.get("items"):
        return PlaylistPage(items=[], next_page_token=None, total_results=0)

    # Batch fetch durations via videos.list (1 quota unit per 50 items)
    video_ids = [
        item["contentDetails"]["videoId"]
        for item in data["items"]
    ]
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
```

- [ ] **Step 3: Add get_content_breakdown and compare_channels**

```python
# Add to scripts/channel.py
def get_content_breakdown(
    channel_id: str,
    sample_size: int = 50,
    exclude_shorts: bool = True,
) -> "ContentBreakdown":
    from _models import ContentBreakdown

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
        duration = _parse_duration(
            item["contentDetails"].get("duration", "PT0S")
        )
        from _util import is_short
        if exclude_shorts and is_short(duration):
            continue
        analyzed += 1

        category_id = item["snippet"].get("categoryId")
        if category_id:
            # category names require a videoCategories.list call; use IDs as keys
            by_category[category_id] = by_category.get(category_id, 0) + 1

        topics = (
            item.get("topicDetails", {}).get("topicCategories", [])
        )
        for topic_url in topics:
            # Extract last path segment as topic name
            topic = topic_url.rstrip("/").split("/")[-1].replace("_", " ")
            by_topic[topic] = by_topic.get(topic, 0) + 1

    return ContentBreakdown(
        by_category=by_category,
        by_topic=by_topic,
        sample_size=analyzed,
    )


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
```

- [ ] **Step 4: Run all channel tests**

```bash
uv run --with pytest pytest tests/test_channel.py -v
```

Expected: Unit tests PASS; integration tests SKIP (if no API key) or PASS (if key set)

- [ ] **Step 5: Run all video tests to confirm no regressions from channel.py additions**

```bash
uv run --with pytest pytest tests/test_video.py -v
```

Expected: All unit tests PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/channel.py tests/test_channel.py
git commit -m "feat(youtube): implement get_playlist, get_content_breakdown, compare_channels (AC-I2..I6)"
```

---

## Chunk 5: SKILL.md, get_metadata/list_transcripts, and cleanup

### Task 12: get_metadata and list_transcripts

**Fulfills:** Completes video.py surface area

**Files:**
- Modify: `~/.claude/skills/youtube/scripts/video.py`

- [ ] **Step 1: Add get_metadata and list_transcripts to video.py**

```python
# Add to scripts/video.py

def get_metadata(url_or_id: str) -> "VideoMetadata":
    from _models import VideoMetadata
    from _util import extract_video_id
    from _cache import get_metadata_cache, set_metadata_cache

    video_id = extract_video_id(url_or_id)
    cached = get_metadata_cache(video_id)
    if cached:
        logger.debug("metadata cache hit for %s", video_id)
        return VideoMetadata(**cached)
    logger.debug("metadata cache miss for %s", video_id)

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {"quiet": True, "skip_download": True, "no_warnings": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # Normalize published_date from YYYYMMDD to ISO 8601
    raw_date = info.get("upload_date", "")
    published_date = (
        f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
        if len(raw_date) == 8 else ""
    )

    data = {
        "video_id": video_id,
        "title": info.get("title", ""),
        "channel": info.get("uploader", ""),
        "duration": int(info.get("duration", 0)),
        "published_date": published_date,
        "description": info.get("description", ""),
        "tags": info.get("tags", []),
        "url": url,
    }
    set_metadata_cache(video_id, data)
    return VideoMetadata(**data)


def list_transcripts(url_or_id: str) -> list:
    from _models import TranscriptMeta
    from _util import extract_video_id
    from youtube_transcript_api import YouTubeTranscriptApi

    video_id = extract_video_id(url_or_id)
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    manual = []
    generated = []
    for t in transcript_list:
        meta = TranscriptMeta(
            language=t.language,
            language_code=t.language_code,
            is_generated=t.is_generated,
            is_translatable=t.is_translatable,
        )
        if t.is_generated:
            generated.append(meta)
        else:
            manual.append(meta)
    return manual + generated
```

- [ ] **Step 2: Run all tests**

```bash
uv run --with pytest pytest tests/ -v
```

Expected: All unit tests PASS; integration tests SKIP or PASS

- [ ] **Step 3: Commit**

```bash
git add scripts/video.py
git commit -m "feat(youtube): add get_metadata and list_transcripts"
```

---

### Task 13: SKILL.md

**Files:**
- Create: `~/.claude/skills/youtube/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
# YouTube Skill

Unified skill for YouTube channel analytics, video transcripts, playlist traversal,
comment fetching, chapter extraction, and local Whisper transcription.

## Prerequisites

- **uv** — install: https://docs.astral.sh/uv/getting-started/installation/
- `YOUTUBE_API_KEY` — required only for channel functions (`channel.py`). Get one at
  https://console.cloud.google.com/. Enable "YouTube Data API v3". No OAuth needed.

## Setup

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))

from channel import get_channel, get_top_videos, get_playlist, get_comments
from video import get_transcript, search_transcript, get_chapters, transcribe_whisper, get_metadata
```

Run with:
```bash
uv run --directory ~/.claude/skills/youtube python your_script.py
```

## Channel Functions (require YOUTUBE_API_KEY)

### `get_channel(handle_or_id) -> ChannelProfile`
Look up a channel by `@handle` or channel ID. `handle` on the result has no leading `@`.

### `get_top_videos(channel_id, n=10, exclude_shorts=True) -> list[Video]`
Top N videos by view count. `n <= 50`. Shorts (< 60s) filtered by default.
**Quota cost: 100 units (search.list)**

### `get_playlist(playlist_id, max_items=50, page_token=None, exclude_shorts=True) -> PlaylistPage`
Paginated playlist access. Pass `page.next_page_token` to get the next page.

### `get_comments(video_id, max_items=20, page_token=None) -> CommentPage`
Top-level comments sorted by relevance. `max_items <= 100`. Paginated.

### `get_content_breakdown(channel_id, sample_size=50, exclude_shorts=True) -> ContentBreakdown`
Category and topic breakdown for a channel sample.
**Quota cost: 100 units (search.list)**

### `compare_channels(handle_or_id_a, handle_or_id_b) -> ChannelComparison`
Side-by-side channel profiles + top 10 videos each.

## Video Functions (no API key needed)

### `get_transcript(url_or_id, languages=None, prefer_manual=True, fallback_whisper=False) -> Transcript`
Fetch captions. Cached in `~/.cache/youtube/transcripts.db`. Set `fallback_whisper=True`
to use local Whisper when captions are unavailable. Cannot combine `languages=` with
`fallback_whisper=True`.

### `transcribe_whisper(url_or_id, model="small") -> Transcript`
Downloads audio via yt-dlp, transcribes locally with `faster-whisper`. Model `small`
(~245 MB) downloaded to `~/.cache/huggingface/hub/` on first use.

### `get_metadata(url_or_id) -> VideoMetadata`
Video metadata via yt-dlp. Cached in `~/.cache/youtube/metadata.db`.

### `list_transcripts(url_or_id) -> list[TranscriptMeta]`
All available caption tracks. Manual tracks listed before auto-generated.

### `get_chapters(url_or_id) -> list[Chapter]`
Chapters parsed from video description. Returns `[]` if none found.

### `search_transcript(url_or_id, query) -> list[TranscriptHit]`
Case-insensitive substring search within transcript snippets. Each hit includes timestamp.

## Quota Notes

- Daily limit: 10,000 units
- `search.list`: **100 units** — called by `get_top_videos` and `get_content_breakdown`
- `videos.list`, `channels.list`, `playlistItems.list`, `commentThreads.list`: **1 unit each**

## Error Reference

| Exception | Cause |
|-----------|-------|
| `MissingAPIKeyError` | `YOUTUBE_API_KEY` not set |
| `ChannelNotFoundError` | Handle or ID doesn't exist |
| `PlaylistNotFoundError` | Playlist ID doesn't exist |
| `CommentsDisabled` | Video has comments disabled |
| `VideoUnavailable` | Video is private or deleted |
| `TranscriptsDisabled` | Video has no captions at all |
| `NoTranscriptFound` | No captions in requested language |
| `InvalidPageTokenError` | Expired or wrong-function page token |
| `WhisperTranscriptionError` | yt-dlp download or model failure |
```

- [ ] **Step 2: Commit**

```bash
git add SKILL.md
git commit -m "docs(youtube): add SKILL.md"
```

---

### Task 14: Delete old skills + final verification

**Files:**
- Delete: `~/.claude/skills/youtube-intel/` (entire directory)
- Delete: `~/.claude/skills/yt-transcript/` (entire directory)

- [ ] **Step 1: Run full test suite one final time**

```bash
cd ~/.claude/skills/youtube
uv run --with pytest --with pytest-mock pytest tests/ -v
```

Expected: All unit tests PASS; integration tests SKIP or PASS

- [ ] **Step 2: Delete youtube-intel**

```bash
rm -rf ~/.claude/skills/youtube-intel
```

- [ ] **Step 3: Delete yt-transcript**

```bash
rm -rf ~/.claude/skills/yt-transcript
```

- [ ] **Step 4: Verify old skills are gone**

```bash
ls ~/.claude/skills/ | grep -E "youtube|yt-"
```

Expected: Only `youtube` appears

- [ ] **Step 5: Stage deletions and commit**

```bash
cd ~/.claude/skills
git add -A
git commit -m "feat(youtube): complete youtube skill; remove youtube-intel and yt-transcript"
```
