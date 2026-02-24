"""
arXiv API client.

Wraps the arXiv Atom/XML API (export.arxiv.org/api/query).
No auth required. Rate-limited to 1 request per 3 seconds per arXiv policy.
"""
from __future__ import annotations

import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"
OPENSEARCH_NS = "{http://a9.com/-/spec/opensearch/1.1/}"

RATE_LIMIT_SECS = 3.0

_last_request_time: float = 0.0


@dataclass
class Paper:
    id: str          # short ID, e.g. "2401.12345"
    title: str
    authors: list[str]
    abstract: str
    published: str   # "YYYY-MM-DD"
    category: str    # primary category, e.g. "cs.CL"
    url: str         # "https://arxiv.org/abs/2401.12345"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _throttle() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < RATE_LIMIT_SECS:
        time.sleep(RATE_LIMIT_SECS - elapsed)
    _last_request_time = time.monotonic()


def _fetch(params: dict) -> ET.Element:
    _throttle()
    response = httpx.get(ARXIV_API_URL, params=params, timeout=30)
    response.raise_for_status()
    return ET.fromstring(response.text)


def _parse_papers(root: ET.Element) -> list[Paper]:
    papers = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        raw_id = entry.findtext(f"{ATOM_NS}id") or ""
        arxiv_id = raw_id.split("/abs/")[-1].split("v")[0] if "/abs/" in raw_id else raw_id

        title = (entry.findtext(f"{ATOM_NS}title") or "").strip().replace("\n", " ")
        abstract = (entry.findtext(f"{ATOM_NS}summary") or "").strip().replace("\n", " ")

        published_raw = entry.findtext(f"{ATOM_NS}published") or ""
        published = published_raw[:10]  # "2024-01-15T00:00:00Z" -> "2024-01-15"

        authors = [
            name.text.strip()
            for author in entry.findall(f"{ATOM_NS}author")
            if (name := author.find(f"{ATOM_NS}name")) is not None and name.text
        ]

        primary_cat_el = entry.find(f"{ARXIV_NS}primary_category")
        category = primary_cat_el.get("term", "") if primary_cat_el is not None else ""

        url = f"https://arxiv.org/abs/{arxiv_id}"

        papers.append(Paper(
            id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            published=published,
            category=category,
            url=url,
        ))
    return papers


def _total_results(root: ET.Element) -> int:
    el = root.find(f"{OPENSEARCH_NS}totalResults")
    return int(el.text) if el is not None and el.text else 0


def _quote_if_phrase(query: str) -> str:
    """Wrap multi-word queries in quotes for exact phrase matching."""
    if " " in query.strip() and not query.strip().startswith('"'):
        return f'"{query.strip()}"'
    return query.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_papers(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
) -> list[Paper]:
    """
    Search papers by keyword or phrase.

    Args:
        query: Search term (phrase or keyword). Multi-word phrases are auto-quoted.
        max_results: Up to 2000 per request.
        sort_by: "relevance", "submittedDate", or "lastUpdatedDate".

    Returns:
        List of Paper dicts, sorted as requested.
    """
    params = {
        "search_query": f"all:{_quote_if_phrase(query)}",
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending",
    }
    root = _fetch(params)
    return _parse_papers(root)


def get_volume_over_time(
    topic: str,
    months: int = 24,
    granularity: str = "month",
) -> list[dict]:
    """
    Count paper submissions per time period for a topic.

    Makes one API request per period (max_results=1, reads totalResults).
    Prints progress to stderr. At 3s/request, 24 months ~= 72 seconds.

    Args:
        topic: Search phrase (same auto-quoting as search_papers).
        months: How many months back to cover.
        granularity: "month" or "quarter".

    Returns:
        List of {"period": "2024-01", "count": 42} dicts in chronological order.
    """
    now = datetime.now(timezone.utc)

    if granularity == "month":
        periods = _month_ranges(now, months)
    elif granularity == "quarter":
        periods = _quarter_ranges(now, months)
    else:
        raise ValueError(f"granularity must be 'month' or 'quarter', got {granularity!r}")

    quoted = _quote_if_phrase(topic)
    results = []
    total = len(periods)

    for i, (label, start, end) in enumerate(periods, 1):
        print(f"  [{i}/{total}] {label}...", file=sys.stderr, flush=True)
        query = f"all:{quoted} AND submittedDate:[{start} TO {end}]"
        params = {
            "search_query": query,
            "max_results": 1,
            "sortBy": "submittedDate",
        }
        root = _fetch(params)
        count = _total_results(root)
        results.append({"period": label, "count": count})

    return results


def get_recent_papers(
    category: str,
    days: int = 30,
    max_results: int = 50,
) -> list[Paper]:
    """
    Get recent papers for an arXiv category.

    Args:
        category: arXiv category code, e.g. "cs.AI", "cs.CL", "stat.ML".
                  See references/categories.md for full list.
        days: How many days back to search.
        max_results: Number of results to return.

    Returns:
        List of Papers, most recent first.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    start_str = cutoff.strftime("%Y%m%d%H%M")
    end_str = now.strftime("%Y%m%d%H%M")

    query = f"cat:{category} AND submittedDate:[{start_str} TO {end_str}]"
    params = {
        "search_query": query,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    root = _fetch(params)
    return _parse_papers(root)


def get_author_papers(
    author_name: str,
    max_results: int = 10,
) -> list[Paper]:
    """
    Get recent papers by an author.

    Args:
        author_name: Full name or last name (e.g. "Yann LeCun" or "LeCun").
                     arXiv author search is fuzzy; verify matches by inspecting results.
        max_results: Number of results to return.

    Returns:
        List of Papers, most recently submitted first.
    """
    params = {
        "search_query": f"au:{_quote_if_phrase(author_name)}",
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    root = _fetch(params)
    return _parse_papers(root)


# ---------------------------------------------------------------------------
# Date range helpers
# ---------------------------------------------------------------------------

def _month_ranges(now: datetime, months: int) -> list[tuple[str, str, str]]:
    """Return (label, start_str, end_str) for each of the past N calendar months."""
    ranges = []
    year = now.year
    month = now.month

    for _ in range(months):
        month -= 1
        if month == 0:
            month = 12
            year -= 1

        label = f"{year}-{month:02d}"
        start = f"{year}{month:02d}010000"

        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1
        end = f"{next_year}{next_month:02d}010000"

        ranges.append((label, start, end))

    ranges.reverse()
    return ranges


def _quarter_ranges(now: datetime, months: int) -> list[tuple[str, str, str]]:
    """Return (label, start_str, end_str) for each quarter covering the past N months."""
    num_quarters = (months + 2) // 3
    ranges = []
    year = now.year
    quarter = (now.month - 1) // 3  # 0-indexed

    for _ in range(num_quarters):
        quarter -= 1
        if quarter < 0:
            quarter = 3
            year -= 1

        q_month = quarter * 3 + 1
        label = f"{year}-Q{quarter + 1}"
        start = f"{year}{q_month:02d}010000"

        end_month = q_month + 3
        end_year = year
        if end_month > 12:
            end_month -= 12
            end_year += 1
        end = f"{end_year}{end_month:02d}010000"

        ranges.append((label, start, end))

    ranges.reverse()
    return ranges
