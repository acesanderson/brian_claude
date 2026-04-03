from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from deslop.fix import fix, judge
from deslop.score import AIWritingScore, AIWritingScoreVerbose, rate_blog_post


def _read_input(file: str | None) -> str:
    if file:
        return Path(file).read_text().strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def _format_score_terse(score: AIWritingScore, label: str | None = None) -> str:
    prefix = f"{label}: " if label else ""
    return (
        f"{prefix}"
        f"lexical={score.lexical.score:.2f}  "
        f"structural={score.structural.score:.2f}  "
        f"rhetorical={score.rhetorical.score:.2f}  "
        f"overall={score.overall:.2f}"
    )


def _format_score_verbose(score: AIWritingScoreVerbose, label: str | None = None) -> str:
    parts = []
    if label:
        parts.append(f"=== {label} ===\n")
    for dim_name in ("lexical", "structural", "rhetorical"):
        dim = getattr(score, dim_name)
        parts.append(f"[{dim_name}]  score={dim.score:.2f}")
        parts.append(f"  evidence:  {dim.evidence}")
        parts.append(f"  rationale: {dim.rationale}")
        parts.append("")
    parts.append(f"overall: {score.overall:.2f}")
    return "\n".join(parts)


def cmd_score(args: argparse.Namespace) -> None:
    posts_path = Path("~/blog/_posts/").expanduser()

    if args.all:
        files = sorted(posts_path.glob("*.md"))
        results: list[tuple[Path, AIWritingScore]] = []
        for f in files:
            text = f.read_text()
            score = rate_blog_post(text, verbose=False)
            results.append((f, score))
        if args.ranked:
            results.sort(key=lambda x: x[1].overall, reverse=True)
        for f, score in results:
            print(_format_score_terse(score, label=f.name))
        return

    text = _read_input(args.file)
    if not text:
        print("error: provide a file, use --all, or pipe text via stdin", file=sys.stderr)
        sys.exit(1)

    score = rate_blog_post(text, verbose=args.verbose)
    label = Path(args.file).name if args.file else None
    if args.verbose:
        print(_format_score_verbose(score, label=label))
    else:
        print(_format_score_terse(score, label=label))


def cmd_judge(args: argparse.Namespace) -> None:
    text = _read_input(args.file)
    if not text:
        print("error: provide a file or pipe text via stdin", file=sys.stderr)
        sys.exit(1)
    critique = asyncio.run(judge(text, model=args.model))
    print(critique)


def cmd_fix(args: argparse.Namespace) -> None:
    text = _read_input(args.file)
    if not text:
        print("error: provide a file or pipe text via stdin", file=sys.stderr)
        sys.exit(1)
    result = asyncio.run(fix(text, judge_model=args.judge, reviser_model=args.reviser))
    if args.inplace and args.file:
        Path(args.file).write_text(result)
    else:
        print(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="deslop",
        description="Detect and strip AI-generated writing patterns from blog posts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # score
    p_score = subparsers.add_parser("score", help="Score a post for AI-generated patterns.")
    p_score.add_argument("file", nargs="?", help="Input file (or pipe via stdin)")
    p_score.add_argument("--all", action="store_true", help="Score all posts in ~/blog/_posts/")
    p_score.add_argument(
        "--ranked", action="store_true", help="With --all: sort by overall score descending"
    )
    p_score.add_argument(
        "--verbose", "-v", action="store_true", help="Include editorial rationale per dimension"
    )

    # judge
    p_judge = subparsers.add_parser("judge", help="Flag AI-isms without rewriting.")
    p_judge.add_argument("file", nargs="?", help="Input file (or pipe via stdin)")
    p_judge.add_argument("--model", default="gemini3", help="Model for the judge pass (default: gemini3)")

    # fix
    p_fix = subparsers.add_parser("fix", help="Run full judge + reviser pipeline.")
    p_fix.add_argument("file", nargs="?", help="Input file (or pipe via stdin)")
    p_fix.add_argument("--judge", default="gemini3", dest="judge", help="Model for the judge pass (default: gemini3)")
    p_fix.add_argument("--reviser", default="opus", help="Model for the reviser pass (default: opus)")
    p_fix.add_argument("--inplace", action="store_true", help="Write result back to the input file")

    args = parser.parse_args()

    if args.command == "score":
        cmd_score(args)
    elif args.command == "judge":
        cmd_judge(args)
    elif args.command == "fix":
        cmd_fix(args)


if __name__ == "__main__":
    main()
