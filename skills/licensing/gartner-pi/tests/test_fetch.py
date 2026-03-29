from __future__ import annotations

import pytest


def test_retry_succeeds_on_second_attempt(monkeypatch):
    import gartner

    calls = []

    def mock_fetch(url: str) -> str:
        calls.append(url)
        if len(calls) < 2:
            raise RuntimeError("HTTP 403")
        return "<html><body>valid</body></html>"

    monkeypatch.setattr(gartner, "_fetch_with_browser", mock_fetch)
    monkeypatch.setattr(gartner.time, "sleep", lambda _: None)

    result = gartner._fetch_with_retry("https://example.com", lambda h: "valid" in h)
    assert "valid" in result
    assert len(calls) == 2


def test_retry_raises_after_three_failures(monkeypatch):
    import gartner

    monkeypatch.setattr(gartner, "_fetch_with_browser", lambda _: "<html>captcha</html>")
    monkeypatch.setattr(gartner.time, "sleep", lambda _: None)
    monkeypatch.setattr(gartner.random, "uniform", lambda a, b: 0)

    with pytest.raises(RuntimeError, match="3 attempts"):
        gartner._fetch_with_retry("https://example.com", lambda h: False)
