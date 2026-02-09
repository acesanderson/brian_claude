#!/usr/bin/env python3
"""MCP Server exposing web_search and fetch_url tools."""
from __future__ import annotations

import asyncio

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from fetch_tools import web_search, fetch_url

server = Server("conduit-websearch")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="web_search",
            description=(
                "Search the web using Brave Search API. Returns top 5 results with "
                "titles, URLs, and snippets. Use this to discover information, "
                "find training platform URLs, or research companies."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query (e.g., 'Zapier training courses')"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="fetch_url",
            description=(
                "Fetch a URL and convert to clean Markdown. Supports HTML, PDF, "
                "Office docs (docx/pptx/xlsx). Automatically paginates long content."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number for paginated content (default: 1)",
                        "default": 1
                    }
                },
                "required": ["url"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "web_search":
        query = arguments["query"]
        result = await web_search(query)

        # Format the result
        if "error" in result:
            text = f"❌ Error: {result['error']}"
        else:
            text = result.get("result", "No results")
            if "next_step_hint" in result:
                text += f"\n\n💡 {result['next_step_hint']}"

        return [TextContent(type="text", text=text)]

    elif name == "fetch_url":
        url = arguments["url"]
        page = arguments.get("page", 1)
        result = await fetch_url(url, page)

        # Format the result
        if "error" in result:
            text = f"❌ Error: {result['error']}"
        else:
            metadata = result.get("metadata", {})
            content = result.get("content", "")
            toc = result.get("table_of_contents", [])

            # Build formatted output
            parts = [
                f"# Fetched: {url}",
                f"**Page:** {metadata.get('current_page', 1)}/{metadata.get('total_pages', 1)}",
                f"**Characters:** {metadata.get('total_characters', 0):,}",
            ]

            if toc:
                parts.append("\n## Table of Contents")
                parts.extend([f"- {item['text']}" for item in toc[:20]])
                if len(toc) > 20:
                    parts.append(f"... and {len(toc) - 20} more headings")

            parts.append("\n## Content\n")
            parts.append(content)

            if metadata.get("is_truncated"):
                parts.append(
                    f"\n\n---\n*Content truncated. "
                    f"Use page={metadata['current_page'] + 1} to continue.*"
                )

            text = "\n".join(parts)

        return [TextContent(type="text", text=text)]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
