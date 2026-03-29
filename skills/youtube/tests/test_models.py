from __future__ import annotations

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/youtube/scripts"))


def test_whisper_transcript_cannot_have_is_generated_true():
    from _models import Transcript
    with pytest.raises(ValueError, match="is_generated must be False"):
        Transcript(
            language="English",
            language_code="en",
            is_generated=True,
            source="whisper",
            snippets=[],
            text="",
        )


def test_whisper_transcript_valid_when_is_generated_false():
    from _models import Transcript
    t = Transcript(
        language="English",
        language_code="en",
        is_generated=False,
        source="whisper",
        snippets=[],
        text="",
    )
    assert t.source == "whisper"
    assert t.is_generated is False
