# /// script
# dependencies = ["jinja2"]
# ///
from __future__ import annotations
from conduit.async_ import ConduitAsync, GenerationParams, ConduitOptions, Verbosity
from conduit.config import settings
from conduit.core.prompt.prompt_loader import PromptLoader

import argparse
import sys
from pathlib import Path


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
prompt_loader = PromptLoader(PROMPTS_DIR)


async def judge(draft: str, model: str) -> str:
    prompt = prompt_loader["judge"]
    params = GenerationParams(model=model)
    options = ConduitOptions(
        project_name="deslop",
        verbosity=Verbosity.SILENT,
        cache=settings.default_cache("deslop"),
    )
    conduit = ConduitAsync(prompt)
    input_variables = {"draft": draft}
    response = await conduit.run(
        input_variables=input_variables, params=params, options=options
    )
    return str(response.content)


async def revise(draft: str, critique: str, model: str) -> str:
    prompt = prompt_loader["reviser"]
    params = GenerationParams(model=model)
    options = ConduitOptions(
        project_name="deslop",
        verbosity=Verbosity.SILENT,
        cache=settings.default_cache("deslop"),
    )
    conduit = ConduitAsync(prompt)
    input_variables = {"draft": draft, "critique": critique}
    response = await conduit.run(
        input_variables=input_variables, params=params, options=options
    )
    return str(response.content)


async def deslop(
    draft: str, judge_model: str = "gemini3", reviser_model: str = "opus"
) -> str:
    critique = await judge(draft, judge_model)
    revision = await revise(draft, critique, reviser_model)
    return revision


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Strip AI-isms from a blog post draft.",
        usage="deslop [--judge MODEL] [--reviser MODEL] [file]  or  cat post.md | deslop",
    )
    parser.add_argument("file", nargs="?", help="Input file (or pipe via stdin)")
    parser.add_argument(
        "--judge", default="gemini3", help="Model for the judge pass (default: gemini3)"
    )
    parser.add_argument(
        "--reviser", default="opus", help="Model for the reviser pass (default: opus)"
    )
    args = parser.parse_args()

    if not sys.stdin.isatty():
        draft = sys.stdin.read().strip()
    elif args.file:
        draft = Path(args.file).read_text().strip()
    else:
        parser.print_usage(sys.stderr)
        sys.exit(1)

    print(deslop(draft, judge_model=args.judge, reviser_model=args.reviser))


if __name__ == "__main__":
    main()
