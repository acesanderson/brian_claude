from __future__ import annotations

from pathlib import Path

from conduit.async_ import ConduitAsync, ConduitOptions, GenerationParams, Verbosity
from conduit.config import settings
from conduit.core.prompt.prompt_loader import PromptLoader

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
prompt_loader = PromptLoader(PROMPTS_DIR)


async def judge(draft: str, model: str = "gemini3") -> str:
    prompt = prompt_loader["judge"]
    params = GenerationParams(model=model)
    options = ConduitOptions(
        project_name="deslop",
        verbosity=Verbosity.PROGRESS,
        cache=settings.default_cache("deslop"),
    )
    conduit = ConduitAsync(prompt)
    response = await conduit.run(input_variables={"draft": draft}, params=params, options=options)
    return str(response.content)


async def revise(draft: str, critique: str, model: str = "opus") -> str:
    prompt = prompt_loader["reviser"]
    params = GenerationParams(model=model)
    options = ConduitOptions(
        project_name="deslop",
        verbosity=Verbosity.PROGRESS,
        cache=settings.default_cache("deslop"),
    )
    conduit = ConduitAsync(prompt)
    response = await conduit.run(
        input_variables={"draft": draft, "critique": critique}, params=params, options=options
    )
    return str(response.content)


async def fix(draft: str, judge_model: str = "gemini3", reviser_model: str = "opus") -> str:
    critique = await judge(draft, judge_model)
    revision = await revise(draft, critique, reviser_model)
    return revision
