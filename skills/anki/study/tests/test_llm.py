from __future__ import annotations
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from src.models import Card


def _make_card(reference: str | None = None) -> Card:
    now = datetime.now(tz=timezone.utc)
    return Card(
        id=1, deck_id=1, front="What is X?", back="X is Y.",
        tags=[], created_at=now, state="new", due=now,
        interval=0, ease_factor=2500, reps=0, lapses=0,
        step_index=0, suspended=False, reference=reference,
    )


def test_ask_card_empty_query_raises():
    """AC: ask_card with empty query raises ValueError."""
    from src.llm import ask_card
    with pytest.raises(ValueError, match="query cannot be empty"):
        ask_card("ML", _make_card(), query="")


def test_ask_card_whitespace_query_raises():
    """AC: ask_card with whitespace-only query raises ValueError."""
    from src.llm import ask_card
    with pytest.raises(ValueError, match="query cannot be empty"):
        ask_card("ML", _make_card(), query="   ")


def test_ask_card_calls_headwater_and_returns_text():
    """ask_card calls LLM and returns the response string."""
    from src.llm import ask_card

    mock_conv = MagicMock()
    mock_conv.last.content = "Here is the explanation."
    mock_resp = MagicMock()
    mock_resp.results = [mock_conv]

    mock_client = AsyncMock()
    mock_client.conduit.query_batch = AsyncMock(return_value=mock_resp)

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("headwater_client.client.headwater_client_async.HeadwaterAsyncClient", return_value=mock_ctx):
        result = ask_card("ML", _make_card(), query="Explain further.")

    assert result == "Here is the explanation."


def test_ask_card_without_reference_renders_template_correctly():
    """Template renders without reference section when card.reference is None."""
    from src.llm import _render_prompt
    card = _make_card(reference=None)
    prompt = _render_prompt("ML", card, "Why?")
    assert "Reference" not in prompt
    assert "What is X?" in prompt
    assert "Why?" in prompt


def test_ask_card_with_reference_includes_reference_in_template():
    """Template includes reference section when card.reference is set."""
    from src.llm import _render_prompt
    card = _make_card(reference="See RFC 9999.")
    prompt = _render_prompt("ML", card, "Why?")
    assert "See RFC 9999." in prompt
