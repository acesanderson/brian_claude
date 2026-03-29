#!/usr/bin/env python3
"""CLI for web search and URL fetching."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from fetch_tools import fetch_url, web_search


def main() -> None:
    parser = argparse.ArgumentParser(description="Web search and URL fetch")
    sub = parser.add_subparsers(dest="command", required=True)

    search_p = sub.add_parser("search")
    search_p.add_argument("query")

    fetch_p = sub.add_parser("fetch")
    fetch_p.add_argument("url")
    fetch_p.add_argument("--page", type=int, default=1)
    fetch_p.add_argument("--proxy", action="store_true", default=False, help="Route through Oxylabs residential proxy")
    fetch_p.add_argument("--browser", action="store_true", default=False, help="Use Playwright + Oxylabs for JS-rendered/bot-protected pages")

    args = parser.parse_args()

    if args.command == "search":
        result = asyncio.run(web_search(args.query))
    else:
        result = asyncio.run(fetch_url(args.url, args.page, use_proxy=args.proxy, use_browser=args.browser))

    if "error" in result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
