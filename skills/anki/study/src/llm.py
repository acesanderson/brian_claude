from __future__ import annotations
import asyncio
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader

if TYPE_CHECKING:
    from src.models import Card

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_MODEL = "gpt-oss:latest"


def _render_prompt(deck_name: str, card: Card, query: str) -> str:
    env = Environment(loader=FileSystemLoader(str(_PROMPTS_DIR)))
    tmpl = env.get_template("ask.md.j2")
    return tmpl.render(
        deck_name=deck_name,
        front=card.front,
        back=card.back,
        reference=card.reference,
        user_query=query,
    )


async def _call_llm(prompt: str) -> str:
    from headwater_client.client.headwater_client_async import HeadwaterAsyncClient
    from headwater_api.classes import BatchRequest
    from conduit.domain.request.generation_params import GenerationParams
    from conduit.domain.config.conduit_options import ConduitOptions
    from src.display import ASK_MAX_TOKENS

    params = GenerationParams(model=_MODEL, output_type="text", max_tokens=ASK_MAX_TOKENS)
    options = ConduitOptions(project_name="anki-ask", include_history=False)
    req = BatchRequest(prompt_strings_list=[prompt], params=params, options=options)
    async with HeadwaterAsyncClient() as client:
        resp = await client.conduit.query_batch(req)
    if not resp.results:
        raise RuntimeError("LLM returned empty results list")
    return resp.results[0].last.content  # NOTE: verify attribute on first live run


def ask_card(deck_name: str, card: Card, query: str) -> str:
    """
    One-shot LLM call. Raises ValueError if query is empty.
    Raises on network/model error — no retry.
    """
    if not query.strip():
        raise ValueError("query cannot be empty")
    prompt = _render_prompt(deck_name, card, query)
    t0 = time.monotonic()
    result = asyncio.run(_call_llm(prompt))
    elapsed = time.monotonic() - t0
    logger.info(
        "ask_card card_id=%d model=%s prompt_chars=%d response_chars=%d elapsed=%.2fs",
        card.id, _MODEL, len(prompt), len(result), elapsed,
    )
    return result
