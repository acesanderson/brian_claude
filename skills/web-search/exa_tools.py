from __future__ import annotations

import os
from typing import Any

_MISSING_KEY_ERROR = {"error": "Missing EXA_API_KEY environment variable"}


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
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"results": []}  # stub — replaced in Task 10


async def exa_contents(
    urls: list[str],
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"results": [], "failed_urls": []}  # stub — replaced in Task 13


async def exa_similar(
    url: str,
    num_results: int = 10,
    use_text: bool = False,
    max_chars: int = 4000,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"results": []}  # stub — replaced in Task 14


async def exa_answer(question: str) -> dict[str, Any]:
    if not os.getenv("EXA_API_KEY"):
        return _MISSING_KEY_ERROR
    return {"answer": "", "citations": []}  # stub — replaced in Task 15
