from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

_RETRY_STATUSES = {429, 503}

_BASE = "https://api.semanticscholar.org/graph/v1"
_SEARCH_FIELDS = "title,abstract,authors,year,citationCount,url,paperId,externalIds"
_PAPER_FIELDS = (
    "title,abstract,authors,year,citationCount,url,paperId,externalIds,"
    "references.title,references.authors,references.year,"
    "citations.title,citations.authors,citations.year"
)


def _build_headers() -> dict[str, str]:
    key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    return {"x-api-key": key} if key else {}


def _shape_paper(p: dict[str, Any], max_abstract: int = 500) -> dict[str, Any]:
    out: dict[str, Any] = {
        "title": p.get("title") or "",
        "paper_id": p.get("paperId") or "",
        "url": p.get("url") or "",
        "authors": [a.get("name", "") for a in (p.get("authors") or [])],
    }
    if p.get("year"):
        out["year"] = p["year"]
    if p.get("citationCount") is not None:
        out["citation_count"] = p["citationCount"]
    abstract = p.get("abstract") or ""
    if abstract:
        out["abstract"] = abstract[:max_abstract] + ("..." if len(abstract) > max_abstract else "")
    ext = p.get("externalIds") or {}
    if ext.get("ArXiv"):
        out["arxiv_id"] = ext["ArXiv"]
    if ext.get("DOI"):
        out["doi"] = ext["DOI"]
    return out


async def _get(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    max_retries: int = 3,
) -> httpx.Response:
    delay = 2.0
    for attempt in range(max_retries + 1):
        r = await client.get(url, params=params, headers=headers)
        if r.status_code not in _RETRY_STATUSES or attempt == max_retries:
            return r
        await asyncio.sleep(delay)
        delay *= 2
    return r


def _classify_error(e: Exception) -> dict[str, Any]:
    msg = str(e).lower()
    if "401" in msg or "403" in msg or "unauthorized" in msg:
        return {"error": "Semantic Scholar auth failed. Check SEMANTIC_SCHOLAR_API_KEY."}
    if "429" in msg or "rate" in msg:
        return {"error": "Semantic Scholar rate limit hit. Set SEMANTIC_SCHOLAR_API_KEY for higher limits."}
    if "timeout" in msg:
        return {"error": "Request timed out calling Semantic Scholar API"}
    return {"error": f"Semantic Scholar API error: {e}"}


async def ss_search(
    query: str,
    num_results: int = 10,
    fields_of_study: list[str] | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    max_abstract: int = 500,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "query": query,
        "limit": num_results,
        "fields": _SEARCH_FIELDS,
    }
    if fields_of_study:
        params["fieldsOfStudy"] = ",".join(fields_of_study)
    if year_start or year_end:
        start = str(year_start) if year_start else ""
        end = str(year_end) if year_end else ""
        params["year"] = f"{start}-{end}"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await _get(client, f"{_BASE}/paper/search", params=params, headers=_build_headers())
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return _classify_error(e)

    papers = data.get("data") or []
    return {
        "results": [_shape_paper(p, max_abstract) for p in papers],
        "total": data.get("total", len(papers)),
    }


async def ss_paper(paper_id: str, max_abstract: int = 500) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await _get(
                client,
                f"{_BASE}/paper/{paper_id}",
                params={"fields": _PAPER_FIELDS},
                headers=_build_headers(),
            )
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        return _classify_error(e)

    out = _shape_paper(data, max_abstract)
    refs = data.get("references") or []
    out["references"] = [
        {
            "title": ref.get("title") or "",
            "authors": [a.get("name", "") for a in (ref.get("authors") or [])],
            "year": ref.get("year"),
        }
        for ref in refs[:20]
    ]
    cites = data.get("citations") or []
    out["citations"] = [
        {
            "title": c.get("title") or "",
            "authors": [a.get("name", "") for a in (c.get("authors") or [])],
            "year": c.get("year"),
        }
        for c in cites[:20]
    ]
    return out
