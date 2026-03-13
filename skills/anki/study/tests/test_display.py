from __future__ import annotations
from src.display import truncate_for_display, reference_key_markup


def test_truncate_long_text_stays_within_max_lines():
    """AC: truncate_for_display('a'*1000, width=80, max_lines=8) returns ≤8 display lines."""
    result = truncate_for_display("a" * 1000, width=80, max_lines=8)
    lines = [l for l in result.splitlines() if l.strip() != "[dim]…[/dim]"]
    assert len(lines) <= 8


def test_truncate_long_text_appends_ellipsis():
    """Truncated output ends with the dim ellipsis marker."""
    result = truncate_for_display("a" * 1000, width=80, max_lines=8)
    assert "[dim]…[/dim]" in result


def test_truncate_short_text_unchanged():
    """AC: short text returns unchanged, no ellipsis."""
    result = truncate_for_display("short text", width=80, max_lines=8)
    assert result == "short text"
    assert "[dim]…[/dim]" not in result


def test_truncate_exact_max_lines_no_ellipsis():
    """Text with exactly max_lines lines (all short) is not truncated."""
    text = "\n".join(["line"] * 8)
    result = truncate_for_display(text, width=80, max_lines=8)
    assert "[dim]…[/dim]" not in result
    assert result.count("\n") == 7  # 8 lines = 7 newlines


def test_truncate_width_enforced():
    """A single line longer than width is split into multiple visual lines."""
    result = truncate_for_display("x" * 200, width=80, max_lines=8)
    for line in result.splitlines():
        if line != "[dim]…[/dim]":
            assert len(line) <= 80


def test_reference_key_markup_no_reference():
    """AC: has_reference=False produces markup with [s]reference[/s]."""
    markup = reference_key_markup(has_reference=False)
    assert "[s]reference[/s]" in markup


def test_reference_key_markup_has_reference():
    """AC: has_reference=True produces markup with [bold magenta][r] reference[/bold magenta]."""
    markup = reference_key_markup(has_reference=True)
    assert "[bold magenta][r] reference[/bold magenta]" in markup
