from __future__ import annotations

import argparse
import asyncio
import json
import sys

try:
    from exa_tools import exa_answer, exa_contents, exa_search, exa_similar
except ImportError:
    print(
        json.dumps(
            {"error": "exa-py not installed. Run: uv sync --directory ~/.claude/skills/web-search"}
        ),
        file=sys.stderr,
    )
    sys.exit(1)

VALID_CATEGORIES = {
    "company",
    "financial report",
    "news",
    "people",
    "personal site",
    "research paper",
    "tweet",
}


def _fail(message: str) -> None:
    print(json.dumps({"error": message}), file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Exa semantic search CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    search_p = sub.add_parser("search")
    search_p.add_argument("query")
    search_p.add_argument("--num-results", type=int, default=10)
    search_p.add_argument("--category", default=None)
    search_p.add_argument("--include-domains", nargs="+", default=None)
    search_p.add_argument("--exclude-domains", nargs="+", default=None)
    search_p.add_argument("--start-date", default=None)
    search_p.add_argument("--end-date", default=None)
    search_p.add_argument("--text", action="store_true", default=False)
    search_p.add_argument("--highlights", action="store_true", default=False)
    search_p.add_argument("--max-chars", type=int, default=4000)

    contents_p = sub.add_parser("contents")
    contents_p.add_argument("urls", nargs="+")
    contents_p.add_argument("--text", action="store_true", default=False)
    contents_p.add_argument("--highlights", action="store_true", default=False)
    contents_p.add_argument("--max-chars", type=int, default=4000)

    similar_p = sub.add_parser("similar")
    similar_p.add_argument("url")
    similar_p.add_argument("--num-results", type=int, default=10)
    similar_p.add_argument("--text", action="store_true", default=False)
    similar_p.add_argument("--highlights", action="store_true", default=False)
    similar_p.add_argument("--max-chars", type=int, default=4000)
    similar_p.add_argument("--start-date", default=None)
    similar_p.add_argument("--end-date", default=None)

    answer_p = sub.add_parser("answer")
    answer_p.add_argument("question")

    args = parser.parse_args()

    # Validation is added task-by-task in subsequent tasks.

    if args.command == "search":
        result = asyncio.run(
            exa_search(
                args.query,
                num_results=args.num_results,
                category=args.category,
                include_domains=args.include_domains,
                exclude_domains=args.exclude_domains,
                start_date=args.start_date,
                end_date=args.end_date,
                use_text=args.text,
                max_chars=args.max_chars,
            )
        )
    elif args.command == "contents":
        urls = list(dict.fromkeys(args.urls))  # deduplicate, preserve order
        result = asyncio.run(
            exa_contents(urls, use_text=args.text, max_chars=args.max_chars)
        )
    elif args.command == "similar":
        result = asyncio.run(
            exa_similar(
                args.url,
                num_results=args.num_results,
                use_text=args.text,
                max_chars=args.max_chars,
                start_date=args.start_date,
                end_date=args.end_date,
            )
        )
    elif args.command == "answer":
        result = asyncio.run(exa_answer(args.question))

    if "error" in result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
