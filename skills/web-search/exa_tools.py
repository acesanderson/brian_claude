from __future__ import annotations

import os
from typing import Any

from exa_py import AsyncExa

_MISSING_KEY_ERROR = {"error": "Missing EXA_API_KEY environment variable"}


def _shape_result(r: Any, use_text: bool) -> dict[str, Any]:
    """Map an SDK result object to the output contract shape.

    Strips: requestId, costDollars, image, favicon, highlightScores, id.
    Omits published_date and author if absent (not null).
    """
    out: dict[str, Any] = {"title": r.title or "", "url": r.url}
    if getattr(r, "published_date", None):
        out["published_date"] = r.published_date
    if getattr(r, "author", None):
        out["author"] = r.author
    if use_text:
        out["text"] = r.text or ""
    else:
        out["highlights"] = r.highlights or []
    return out


def _classify_error(e: Exception, endpoint: str) -> dict[str, Any]:
    msg = str(e).lower()
    if "401" in msg or "unauthorized" in msg or "authentication" in msg:
        return {"error": "Exa authentication failed. Check EXA_API_KEY."}
    if "timeout" in msg:
        return {"error": f"Request timed out calling Exa {endpoint}"}
    if "connection" in msg or "network" in msg:
        return {"error": f"Network error calling Exa {endpoint}: {e}"}
    return {"error": f"Exa API error: {e}"}


async def exa_search(
    query: str,
    num_results: int = 10,
    category: str | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return _MISSING_KEY_ERROR

    contents: dict[str, Any]
    if use_text:
        contents = {"text": {"max_characters": max_chars}}
    else:
        contents = {"highlights": {"max_characters": max_chars}}

    kwargs: dict[str, Any] = {
        "num_results": num_results,
        "contents": contents,
    }
    if category:
        kwargs["category"] = category
    if include_domains:
        kwargs["include_domains"] = include_domains
    if exclude_domains:
        kwargs["exclude_domains"] = exclude_domains
    if start_date:
        kwargs["start_published_date"] = start_date + "T00:00:00.000Z"
    if end_date:
        kwargs["end_published_date"] = end_date + "T23:59:59.999Z"

    try:
        client = AsyncExa(api_key=api_key)
        response = await client.search(query, **kwargs)
        return {"results": [_shape_result(r, use_text) for r in response.results]}
    except Exception as e:
        return _classify_error(e, "/search")


async def exa_contents(
    urls: list[str],
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return _MISSING_KEY_ERROR

    # get_contents takes text/highlights as direct kwargs, not a contents dict
    contents_kwargs: dict[str, Any]
    if use_text:
        contents_kwargs = {"text": {"max_characters": max_chars}}
    else:
        contents_kwargs = {"highlights": {"max_characters": max_chars}}

    try:
        client = AsyncExa(api_key=api_key)
        response = await client.get_contents(urls, **contents_kwargs)
    except Exception as e:
        return _classify_error(e, "/contents")

    results = []
    failed_urls = []

    returned_ids = {r.url for r in response.results}

    for url in urls:
        if url in returned_ids:
            match = next(r for r in response.results if r.url == url)
            results.append(_shape_result(match, use_text))
        else:
            failed_urls.append(url)

    return {"results": results, "failed_urls": failed_urls}


async def exa_similar(
    url: str,
    num_results: int = 10,
    use_text: bool = False,
    max_chars: int = 4000,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return _MISSING_KEY_ERROR

    contents: dict[str, Any]
    if use_text:
        contents = {"text": {"max_characters": max_chars}}
    else:
        contents = {"highlights": {"max_characters": max_chars}}

    kwargs: dict[str, Any] = {
        "num_results": num_results,
        "contents": contents,
    }
    if start_date:
        kwargs["start_published_date"] = start_date + "T00:00:00.000Z"
    if end_date:
        kwargs["end_published_date"] = end_date + "T23:59:59.999Z"

    try:
        client = AsyncExa(api_key=api_key)
        response = await client.find_similar(url, **kwargs)
        return {"results": [_shape_result(r, use_text) for r in response.results]}
    except Exception as e:
        return _classify_error(e, "/findSimilar")


async def exa_answer(question: str) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"answer": "", "citations": []}  # stub — replaced in Task 15
