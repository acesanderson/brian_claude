from __future__ import annotations

import os
from typing import Any


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
    return {"results": []}


async def exa_contents(
    urls: list[str],
    use_text: bool = False,
    max_chars: int = 4000,
) -> dict[str, Any]:
    return {"results": [], "failed_urls": []}


async def exa_similar(
    url: str,
    num_results: int = 10,
    use_text: bool = False,
    max_chars: int = 4000,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    return {"results": []}


async def exa_answer(question: str) -> dict[str, Any]:
    return {"answer": "", "citations": []}
