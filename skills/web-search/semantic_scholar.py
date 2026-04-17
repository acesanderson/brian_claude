from __future__ import annotations

import argparse
import asyncio
import json
import sys

try:
    from semantic_scholar_tools import ss_paper, ss_search
except ImportError:
    print(
        json.dumps({"error": "httpx not installed. Run: uv sync --directory ~/.claude/skills/web-search"}),
        file=sys.stderr,
    )
    sys.exit(1)


def _fail(message: str) -> None:
    print(json.dumps({"error": message}), file=sys.stderr)
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic Scholar academic search CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    search_p = sub.add_parser("search")
    search_p.add_argument("query")
    search_p.add_argument("--num-results", type=int, default=10)
    search_p.add_argument("--fields-of-study", nargs="+", default=None,
                          metavar="FIELD",
                          help='e.g. "Computer Science" "Medicine"')
    search_p.add_argument("--year-start", type=int, default=None)
    search_p.add_argument("--year-end", type=int, default=None)
    search_p.add_argument("--max-abstract", type=int, default=500)

    paper_p = sub.add_parser("paper")
    paper_p.add_argument(
        "paper_id",
        help=(
            "Semantic Scholar paper ID, DOI (10.18653/v1/...), "
            "or arXiv ID prefixed with arXiv: (e.g. arXiv:2307.06435)"
        ),
    )
    paper_p.add_argument("--max-abstract", type=int, default=500)

    args = parser.parse_args()

    if args.command == "search":
        if not 1 <= args.num_results <= 100:
            _fail("--num-results must be between 1 and 100")
        if args.year_start and args.year_end and args.year_start > args.year_end:
            _fail("--year-start must be <= --year-end")
        result = asyncio.run(
            ss_search(
                args.query,
                num_results=args.num_results,
                fields_of_study=args.fields_of_study,
                year_start=args.year_start,
                year_end=args.year_end,
                max_abstract=args.max_abstract,
            )
        )
    elif args.command == "paper":
        result = asyncio.run(ss_paper(args.paper_id, max_abstract=args.max_abstract))

    if "error" in result:
        print(json.dumps(result), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
