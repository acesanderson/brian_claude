from __future__ import annotations

import re
from urllib.parse import urlparse, parse_qs


def extract_video_id(url_or_id: str) -> str:
    if re.match(r"^[A-Za-z0-9_-]{11}$", url_or_id):
        return url_or_id

    parsed = urlparse(url_or_id)

    if parsed.netloc in ("youtu.be", "www.youtu.be"):
        vid = parsed.path.lstrip("/")
        if vid:
            return vid[:11]

    if "youtube.com" in parsed.netloc and parsed.path == "/watch":
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]

    if "youtube.com" in parsed.netloc and parsed.path.startswith("/embed/"):
        vid = parsed.path[7:]
        if vid:
            return vid[:11]

    raise ValueError(f"Cannot extract video ID from: {url_or_id!r}")


def is_short(duration_seconds: int) -> bool:
    return duration_seconds < 60
