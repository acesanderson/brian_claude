"""Standalone fetch tools extracted from Conduit for MCP server use."""
from __future__ import annotations

import io
import mimetypes
from typing import Any

import httpx


async def web_search(query: str) -> dict[str, str]:
    """
    Performs a web search using the Brave Search API.
    Requires BRAVE_API_KEY environment variable.
    """
    import os

    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return {"error": "Missing BRAVE_API_KEY environment variable"}

    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": 5}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, headers=headers, params=params, timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

        results = []
        web_results = data.get("web", {}).get("results", [])

        if not web_results:
            return {"result": "No results found."}

        for i, item in enumerate(web_results, 1):
            title = item.get("title", "No Title")
            link = item.get("url", "")
            description = item.get("description", "")
            results.append(
                f"[{i}] Title: {title}\n    URL: {link}\n    Snippet: {description}"
            )

        return {
            "result": "\n---\n".join(results),
            "next_step_hint": "Use fetch_url to see full page content.",
        }
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


def _convert_html_to_md(html_text: str) -> str:
    """Convert HTML to clean markdown."""
    import markdownify
    import readabilipy

    ret = readabilipy.simple_json_from_html_string(html_text, use_readability=True)
    if not ret["content"]:
        return "<error>Page failed to be simplified from HTML</error>"

    return markdownify.markdownify(ret["content"], heading_style=markdownify.ATX)


def _convert_binary_to_md(content_bytes: bytes, extension: str) -> str:
    """Convert PDF/Office docs to markdown using MarkItDown."""
    from markitdown import MarkItDown

    md = MarkItDown()
    stream = io.BytesIO(content_bytes)

    try:
        result = md.convert_stream(stream, file_extension=extension)
        return result.text_content
    except Exception as e:
        return f"<error>MarkItDown failed to convert {extension} file: {str(e)}</error>"


def _paginate_content(full_content: str, url: str, page: int) -> dict[str, Any]:
    """Paginate content for easier viewing."""
    lines = full_content.splitlines()

    # Generate Table of Contents
    toc = [
        {"text": line, "line": i + 1}
        for i, line in enumerate(lines)
        if line.strip().startswith("#")
    ]

    # Viewport Slicing (~8000 chars per page)
    chars_per_page = 8000
    total_chars = len(full_content)
    total_pages = (total_chars // chars_per_page) + 1

    start_idx = (page - 1) * chars_per_page
    end_idx = start_idx + chars_per_page
    viewport_text = full_content[start_idx:end_idx]

    if start_idx >= total_chars and total_chars > 0:
        return {
            "error": f"Page {page} out of bounds. Total pages: {total_pages}",
            "url": url,
        }

    return {
        "metadata": {
            "url": url,
            "current_page": page,
            "total_pages": total_pages,
            "total_characters": total_chars,
            "is_truncated": page < total_pages,
        },
        "table_of_contents": toc,
        "content": viewport_text,
    }


async def fetch_url(url: str, page: int = 1) -> dict[str, Any]:
    """
    Fetch a URL and convert it to clean Markdown.
    Supports HTML, PDF, Office documents.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=30,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            return {"error": f"Failed to fetch {url}: {str(e)}"}

    # MIME Type Dispatcher
    content_type = response.headers.get("content-type", "").lower().split(";")[0]
    extension = mimetypes.guess_extension(content_type) or ""

    try:
        if content_type in ["text/html", "application/xhtml+xml"]:
            full_md = _convert_html_to_md(response.text)

        elif content_type in [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/rtf",
        ]:
            full_md = _convert_binary_to_md(response.content, extension)

        elif content_type == "application/json":
            full_md = f"```json\n{response.text}\n```"

        else:
            # Sniff for HTML if MIME is missing/generic
            if "<html" in response.text[:100].lower():
                full_md = _convert_html_to_md(response.text)
            else:
                full_md = response.text

    except Exception as e:
        return {"error": f"Conversion error for {url}: {str(e)}"}

    return _paginate_content(full_md, url, page)
