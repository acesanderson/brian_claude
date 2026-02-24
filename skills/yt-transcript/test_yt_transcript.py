"""
Exploratory test for youtube-transcript-api v1.2.4.
Tests against https://www.youtube.com/watch?v=aircAruvnKk (3b1b neural networks).

Run:
    python3 test_yt_transcript.py

Requires:
    pip install youtube-transcript-api>=1.2.4
"""

from __future__ import annotations

from youtube_transcript_api import (
    YouTubeTranscriptApi,
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

VIDEO_ID = "aircAruvnKk"

api = YouTubeTranscriptApi()

# ── 1. List available transcripts ─────────────────────────────────────────────
print("[1] api.list() — available transcripts")
tl = api.list(VIDEO_ID)
manually_created = list(tl._manually_created_transcripts.values())
generated = list(tl._generated_transcripts.values())

print(f"  Manually created ({len(manually_created)}):")
for t in manually_created[:5]:
    print(f"    {t.language_code:10s}  {t.language}")
if len(manually_created) > 5:
    print(f"    ... and {len(manually_created) - 5} more")

print(f"  Auto-generated ({len(generated)}):")
for t in generated:
    print(f"    {t.language_code:10s}  {t.language}")

# ── 2. Manual vs generated preference ─────────────────────────────────────────
print("\n[2] find_manually_created_transcript(['en'])")
manual_en = tl.find_manually_created_transcript(["en"])
print(f"  language={manual_en.language!r}, is_generated={manual_en.is_generated}")

print("\n[3] find_generated_transcript(['en'])")
gen_en = tl.find_generated_transcript(["en"])
print(f"  language={gen_en.language!r}, is_generated={gen_en.is_generated}")

# ── 3. Fetch and inspect snippet shape ────────────────────────────────────────
print("\n[4] manual_en.fetch() — first 10 snippets")
fetched = manual_en.fetch()
print(f"  video_id:     {fetched.video_id}")
print(f"  language:     {fetched.language}")
print(f"  is_generated: {fetched.is_generated}")
print(f"  total snippets: {len(fetched.snippets)}")

print("\n  First 10 snippets:")
for snippet in fetched.snippets[:10]:
    print(f"    [{snippet.start:7.2f}s +{snippet.duration:.2f}s]  {snippet.text!r}")

# ── 4. to_raw_data() ──────────────────────────────────────────────────────────
print("\n[5] to_raw_data() — shape check")
raw = fetched.to_raw_data()
print(f"  len: {len(raw)}")
print(f"  first entry: {raw[0]}")
print(f"  keys: {list(raw[0].keys())}")

# ── 5. Plain-text concatenation ───────────────────────────────────────────────
print("\n[6] Full plain text (first 500 chars)")
full_text = " ".join(s["text"] for s in raw)
print(f"  Total chars: {len(full_text)}")
print(f"  Preview: {full_text[:500]!r}")

# ── 6. api.fetch() direct shortcut ────────────────────────────────────────────
print("\n[7] api.fetch() — prefers manual over generated")
direct = api.fetch(VIDEO_ID, languages=["en"])
print(f"  language: {direct.language!r}, is_generated: {direct.is_generated}")
assert not direct.is_generated, "Expected manual transcript, got generated"

# ── 7. Video ID extraction from URLs ─────────────────────────────────────────
print("\n[8] URL format parsing (manual check)")
import re

URL_FORMATS = [
    "https://www.youtube.com/watch?v=aircAruvnKk",
    "https://youtu.be/aircAruvnKk",
    "https://www.youtube.com/embed/aircAruvnKk",
    "https://youtube.com/watch?v=aircAruvnKk&t=42s",
    "aircAruvnKk",  # bare ID passthrough
]

def extract_video_id(url_or_id: str) -> str:
    patterns = [
        r"[?&]v=([A-Za-z0-9_-]{11})",
        r"youtu\.be/([A-Za-z0-9_-]{11})",
        r"embed/([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    raise ValueError(f"Cannot extract video ID from: {url_or_id!r}")

for url in URL_FORMATS:
    vid = extract_video_id(url)
    assert vid == "aircAruvnKk", f"Got {vid!r} from {url!r}"
    print(f"  OK  {url!r} -> {vid!r}")

print("\n\nAll checks passed — v1.2.4 works, response shapes confirmed.")
