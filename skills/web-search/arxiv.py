from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from datetime import date as _date

try:
    from arxiv_tools import arxiv_paper, arxiv_search
except ImportError:
    print(
        json.dumps({"error": "httpx not installed. Run: uv sync --directory ~/.claude/skills/web-search"}),
        file=sys.stderr,
    )
    sys.exit(1)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _fail(message: str) -> None:
    print(json.dumps({"error": message}), file=sys.stderr)
    sys.exit(1)


def _validate_date(value: str) -> _date:
    if not _DATE_RE.match(value):
        _fail(f"Invalid date format: {value!r}. Expected YYYY-MM-DD")
    try:
        return _date.fromisoformat(value)
    except ValueError:
        _fail(f"Invalid date: {value!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="arXiv preprint search CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    search_p = sub.add_parser("search")
    search_p.add_argument("query")
    search_p.add_argument("--num-results", type=int, default=10)
    search_p.add_argument(
        "--category",
        default=None,
        help="arXiv category filter, e.g. cs.AI, cs.LG, stat.ML",
    )
    search_p.add_argument("--start-date", default=None, help="YYYY-MM-DD")
    search_p.add_argument("--end-date", default=None, help="YYYY-MM-DD")
    search_p.add_argument("--max-abstract", type=int, default=500)

    paper_p = sub.add_parser("paper")
    paper_p.add_argument("arxiv_id", help="arXiv paper ID, e.g. 2307.06435")
    paper_p.add_argument("--max-abstract", type=int, default=500)

    args = parser.parse_args()

    if args.command == "search":
        if not 1 <= args.num_results <= 100:
            _fail("--num-results must be between 1 and 100")
        start = _validate_date(args.start_date) if args.start_date else None
        end = _validate_date(args.end_date) if args.end_date else None
        if start and end and start > end:
            _fail("--start-date must be before or equal to --end-date")
        result = asyncio.run(
            arxiv_search(
                args.query,
                num_results=args.num_results,
                category=args.category,
                start_date=args.start_date,
                end_date=args.end_date,
                max_abstract=args.max_abstract,
            )
        )
    elif args.command == "paper":
        result = asyncio.run(arxiv_paper(args.arxiv_id, max_abstract=args.max_abstract))

    if "error" in result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
