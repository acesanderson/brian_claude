from __future__ import annotations

import pytest


MOCK_RESPONSE = {
    "web": {
        "results": [
            {"url": "https://www.gartner.com/reviews/product/sap-s-4hana-1020798628", "title": "SAP"},
            {"url": "https://www.gartner.com/reviews/product/oracle-erp-cloud", "title": "Oracle"},
        ]
    }
}


def test_slug_extracted_from_first_matching_url(monkeypatch):
    import gartner
    import httpx

    class MockResp:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return MOCK_RESPONSE

    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: MockResp())
    slug = gartner._brave_search_product_slug("SAP S/4HANA")
    assert slug == "sap-s-4hana-1020798628"


def test_raises_when_no_product_urls_found(monkeypatch):
    import gartner
    import httpx

    class MockResp:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"web": {"results": [{"url": "https://other.com/foo"}]}}

    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    monkeypatch.setattr(httpx, "get", lambda *a, **kw: MockResp())
    with pytest.raises(ValueError, match="No Gartner product page found"):
        gartner._brave_search_product_slug("Nonexistent Product")


def test_raises_when_api_key_missing(monkeypatch):
    import gartner
    monkeypatch.delenv("BRAVE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="BRAVE_API_KEY"):
        gartner._brave_search_product_slug("anything")
