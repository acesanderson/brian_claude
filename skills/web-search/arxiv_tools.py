from __future__ import annotations

import asyncio
import re
import xml.etree.ElementTree as ET
from typing import Any

import httpx

_BASE = "https://export.arxiv.org/api/query"
_ATOM = "http://www.w3.org/2005/Atom"
_ARXIV_NS = "http://arxiv.org/schemas/atom"
_OPENSEARCH = "http://a9.com/-/spec/opensearch/1.1/"
# arXiv asks for a descriptive User-Agent so they can contact abusers
_HEADERS = {"User-Agent": "web-search-skill/1.0 (academic research tool; respectful automated access)"}

_VERSION_RE = re.compile(r"v\d+$")
_RETRY_STATUSES = {429, 503}


def _strip_version(arxiv_id: str) -> str:
    return _VERSION_RE.sub("", arxiv_id)


def _parse_entry(entry: ET.Element, max_abstract: int = 500) -> dict[str, Any]:
    def find(name: str) -> ET.Element | None:
        return entry.find(f"{{{_ATOM}}}{name}")

    id_el = find("id")
    raw_id = (id_el.text or "").strip() if id_el is not None else ""
    arxiv_id = _strip_version(raw_id.split("/abs/")[-1]) if "/abs/" in raw_id else raw_id

    title_el = find("title")
    title = " ".join((title_el.text or "").split()) if title_el is not None else ""

    summary_el = find("summary")
    abstract = " ".join((summary_el.text or "").split()) if summary_el is not None else ""
    if len(abstract) > max_abstract:
        abstract = abstract[:max_abstract] + "..."

    authors = [
        " ".join((name.text or "").split())
        for author in entry.findall(f"{{{_ATOM}}}author")
        for name in [author.find(f"{{{_ATOM}}}name")]
        if name is not None and name.text
    ]

    published_el = find("published")
    published = (published_el.text or "")[:10] if published_el is not None else ""

    categories = [
        cat.get("term", "")
        for cat in entry.findall(f"{{{_ATOM}}}category")
        if cat.get("term")
    ]

    primary_el = entry.find(f"{{{_ARXIV_NS}}}primary_category")
    primary_cat = primary_el.get("term", "") if primary_el is not None else (categories[0] if categories else "")

    return {
        "title": title,
        "arxiv_id": arxiv_id,
        "url": f"https://arxiv.org/abs/{arxiv_id}",
        "authors": authors,
        "published": published,
        "primary_category": primary_cat,
        "categories": categories,
        "abstract": abstract,
    }


def _classify_error(e: Exception) -> dict[str, Any]:
    msg = str(e).lower()
    if "timeout" in msg:
        return {"error": "Request timed out calling arXiv API"}
    if "connection" in msg or "network" in msg:
        return {"error": f"Network error calling arXiv API: {e}"}
    return {"error": f"arXiv API error: {e}"}


async def _get(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, Any] | None = None,
    max_retries: int = 3,
) -> httpx.Response:
    delay = 2.0
    for attempt in range(max_retries + 1):
        r = await client.get(url, params=params, headers=_HEADERS)
        if r.status_code not in _RETRY_STATUSES or attempt == max_retries:
            return r
        await asyncio.sleep(delay)
        delay *= 2
    return r


async def arxiv_search(
    query: str,
    num_results: int = 10,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_abstract: int = 500,
) -> dict[str, Any]:
    search_query = f"all:{query}"
    if category:
        search_query = f"cat:{category} AND {search_query}"

    params: dict[str, Any] = {
        "search_query": search_query,
        "start": 0,
        "max_results": num_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await _get(client, _BASE, params=params)
            r.raise_for_status()
            root = ET.fromstring(r.text)
    except Exception as e:
        return _classify_error(e)

    entries = root.findall(f"{{{_ATOM}}}entry")
    results = [_parse_entry(e, max_abstract) for e in entries]

    if start_date:
        results = [r for r in results if r["published"] >= start_date]
    if end_date:
        results = [r for r in results if r["published"] <= end_date]

    total_el = root.find(f"{{{_OPENSEARCH}}}totalResults")
    total = int(total_el.text) if total_el is not None and total_el.text else len(results)

    return {"results": results, "total": total}


async def arxiv_paper(paper_id: str, max_abstract: int = 500) -> dict[str, Any]:
    paper_id = _strip_version(paper_id)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await _get(client, _BASE, params={"id_list": paper_id})
            r.raise_for_status()
            root = ET.fromstring(r.text)
    except Exception as e:
        return _classify_error(e)

    entries = root.findall(f"{{{_ATOM}}}entry")
    if not entries:
        return {"error": f"No paper found with arXiv ID: {paper_id}"}

    return _parse_entry(entries[0], max_abstract)
