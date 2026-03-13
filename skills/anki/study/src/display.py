from __future__ import annotations

REFERENCE_MAX_CHARS = 500   # hard cap enforced at write time
DISPLAY_MAX_LINES = 8       # visual lines shown for reference and LLM response
ASK_MAX_TOKENS = 250        # max_tokens passed to LLM


def truncate_for_display(text: str, width: int, max_lines: int = DISPLAY_MAX_LINES) -> str:
    """
    Wrap text at `width` chars, keep first `max_lines` visual lines.
    Appends dim ellipsis marker if truncated.
    `width` must be provided by the caller from console.width — never hardcoded.
    """
    visual_lines: list[str] = []
    raw_lines = text.splitlines() or [""]
    for raw_line in raw_lines:
        if not raw_line:
            visual_lines.append("")
        else:
            while len(raw_line) > width:
                visual_lines.append(raw_line[:width])
                raw_line = raw_line[width:]
            visual_lines.append(raw_line)
        if len(visual_lines) >= max_lines:
            break

    total_visual = sum(
        max(1, -(-len(l) // width)) if l else 1
        for l in raw_lines
    )
    was_truncated = total_visual > max_lines

    result = "\n".join(visual_lines[:max_lines])
    if was_truncated:
        result += "\n[dim]…[/dim]"
    return result


def reference_key_markup(has_reference: bool) -> str:
    """Return Rich markup for the [r] reference action key."""
    if has_reference:
        return "[bold magenta][r] reference[/bold magenta]"
    return "[dim][r] [s]reference[/s][/dim]"
