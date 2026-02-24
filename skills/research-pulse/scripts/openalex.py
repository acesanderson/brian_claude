"""
OpenAlex API wrapper for research intelligence.

No auth required. Set OPENALEX_EMAIL env var for the polite pool (recommended).
Docs: https://docs.openalex.org/
"""
from __future__ import annotations

import datetime
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

BASE_URL = "https://api.openalex.org"
_MAILTO = os.environ.get("OPENALEX_EMAIL", "")
_UA = (
    f"research-pulse/0.1 (mailto:{_MAILTO})"
    if _MAILTO
    else "research-pulse/0.1"
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Work:
    id: str
    title: str
    year: int | None
    cited_by_count: int
    doi: str | None
    primary_topic: str | None


@dataclass
class WorkSearchResult:
    query: str
    total_count: int
    by_year: dict[str, int]   # "YYYY" -> publication count, sorted ascending
    top_works: list[Work]     # sorted by cited_by_count desc


@dataclass
class InstitutionProfile:
    id: str
    name: str
    country: str
    works_count: int
    cited_by_count: int
    h_index: int | None
    top_fields: list[str]        # research areas by score, top 10
    works_by_year: dict[str, int]  # "YYYY" -> works_count


@dataclass
class TrendingTopic:
    id: str
    name: str
    recent_count: int    # publications in the recent window
    baseline_count: int  # publications in the baseline window
    growth_pct: float    # (recent - baseline) / baseline * 100


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get(path: str, **params) -> dict:
    """Make a GET request to the OpenAlex API."""
    if _MAILTO:
        params.setdefault("mailto", _MAILTO)
    # Keep | : , * unencoded — used in filter values and cursor
    parts = []
    for k, v in params.items():
        if v is not None:
            parts.append(
                f"{urllib.parse.quote(str(k))}="
                f"{urllib.parse.quote(str(v), safe='|:,*')}"
            )
    url = f"{BASE_URL}/{path}?{'&'.join(parts)}"
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def _paginate(
    path: str,
    *,
    filter_str: str,
    sort: str = "cited_by_count:desc",
    max_results: int = 200,
) -> list[dict]:
    """Fetch up to max_results items via cursor pagination."""
    per_page = min(max_results, 200)
    results: list[dict] = []
    cursor = "*"
    while len(results) < max_results:
        data = _get(
            path,
            filter=filter_str,
            sort=sort,
            per_page=per_page,
            cursor=cursor,
        )
        batch = data.get("results", [])
        results.extend(batch)
        next_cursor = data["meta"].get("next_cursor")
        if not next_cursor or not batch:
            break
        cursor = next_cursor
    return results[:max_results]


def _parse_work(raw: dict) -> Work:
    pt = raw.get("primary_topic")
    return Work(
        id=raw.get("id", ""),
        title=raw.get("title") or "",
        year=raw.get("publication_year"),
        cited_by_count=raw.get("cited_by_count", 0),
        doi=raw.get("doi"),
        primary_topic=pt["display_name"] if pt else None,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_works(
    query: str,
    years_back: int = 5,
    max_results: int = 200,
) -> WorkSearchResult:
    """
    Search works by keyword/topic, return publication volume over time.

    Args:
        query: free-text search applied to title + abstract
        years_back: how many years of history to include
        max_results: max works to return (cursor-paginated internally)

    Returns WorkSearchResult with total_count, by_year dict, and top_works.
    """
    year_cutoff = datetime.date.today().year - years_back
    filter_str = (
        f"title_and_abstract.search:{query},"
        f"publication_year:>{year_cutoff - 1}"
    )

    # Publication volume by year (one request)
    group_resp = _get(
        "works",
        filter=filter_str,
        group_by="publication_year",
        per_page=200,
    )
    by_year = {
        item["key"]: item["count"]
        for item in group_resp.get("group_by", [])
    }
    total = group_resp["meta"]["count"]

    # Top works by citation count (cursor-paginated)
    raw_works = _paginate("works", filter_str=filter_str, max_results=max_results)

    return WorkSearchResult(
        query=query,
        total_count=total,
        by_year=dict(sorted(by_year.items())),
        top_works=[_parse_work(w) for w in raw_works],
    )


def institution_profile(name: str) -> InstitutionProfile:
    """
    Look up an institution by name and return its research output profile.

    Matches the first result from OpenAlex institution search.
    Returns works_count, cited_by_count, h_index, top research fields, and
    annual publication trends.
    """
    resp = _get("institutions", search=name, per_page=1)
    items = resp.get("results", [])
    if not items:
        raise ValueError(f"No institution found matching: {name!r}")
    inst = items[0]

    # topics: list of {display_name, count, ...} sorted by count desc
    topics = inst.get("topics") or []
    top_fields = [
        t["display_name"]
        for t in sorted(topics, key=lambda t: t.get("count", 0), reverse=True)[:10]
    ]

    works_by_year: dict[str, int] = {
        str(entry["year"]): entry["works_count"]
        for entry in (inst.get("counts_by_year") or [])
    }

    stats = inst.get("summary_stats") or {}

    return InstitutionProfile(
        id=inst.get("id", ""),
        name=inst.get("display_name", ""),
        country=inst.get("country_code", ""),
        works_count=inst.get("works_count", 0),
        cited_by_count=inst.get("cited_by_count", 0),
        h_index=stats.get("h_index"),
        top_fields=top_fields,
        works_by_year=dict(sorted(works_by_year.items())),
    )


def trending_topics(
    top_n: int = 20,
    recent_years: int = 2,
    baseline_years: int = 2,
    min_recent_count: int = 500,
) -> list[TrendingTopic]:
    """
    Return academic topics growing fastest by publication volume.

    Compares a recent window vs. the prior baseline window.
    Only topics appearing in both windows with >= min_recent_count recent
    publications are included. Sorted by growth_pct descending.

    Args:
        top_n: number of topics to return
        recent_years: size of the recent window in years
        baseline_years: size of the baseline window in years
        min_recent_count: minimum publications in recent window (noise filter)
    """
    year_now = datetime.date.today().year
    recent_end = year_now - 1
    recent_start = recent_end - recent_years + 1
    baseline_end = recent_start - 1
    baseline_start = baseline_end - baseline_years + 1

    recent_filter = "|".join(str(y) for y in range(recent_start, recent_end + 1))
    baseline_filter = "|".join(str(y) for y in range(baseline_start, baseline_end + 1))

    recent_resp = _get(
        "works",
        filter=f"publication_year:{recent_filter}",
        group_by="primary_topic.id",
        per_page=200,
    )
    baseline_resp = _get(
        "works",
        filter=f"publication_year:{baseline_filter}",
        group_by="primary_topic.id",
        per_page=200,
    )

    recent_groups = {
        item["key"]: (item["key_display_name"], item["count"])
        for item in recent_resp.get("group_by", [])
        if item["key"] not in ("", "unknown")
    }
    baseline_groups: dict[str, int] = {
        item["key"]: item["count"]
        for item in baseline_resp.get("group_by", [])
        if item["key"] not in ("", "unknown")
    }

    trends: list[TrendingTopic] = []
    for topic_id, (name, recent_count) in recent_groups.items():
        if recent_count < min_recent_count:
            continue
        baseline_count = baseline_groups.get(topic_id, 0)
        if baseline_count == 0:
            continue  # skip brand-new topics with no baseline
        growth_pct = (recent_count - baseline_count) / baseline_count * 100
        trends.append(TrendingTopic(
            id=topic_id,
            name=name,
            recent_count=recent_count,
            baseline_count=baseline_count,
            growth_pct=round(growth_pct, 1),
        ))

    trends.sort(key=lambda t: t.growth_pct, reverse=True)
    return trends[:top_n]
