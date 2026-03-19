from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_segment_list_extracts_and_deduplicates():
    import gartner
    html = (FIXTURES / "segment_list.html").read_text()
    segments = gartner._parse_segment_list(html)
    slugs = [s["slug"] for s in segments]
    assert "cloud-erp" in slugs
    assert slugs.count("cloud-erp") == 1
    assert len(segments) >= 10


def test_parse_segment_list_raises_on_too_few():
    import gartner
    html = "<html><body><a href='/reviews/market/cloud-erp'>Cloud ERP</a></body></html>"
    with pytest.raises(ValueError, match="Content validation failed"):
        gartner._parse_segment_list(html)


def test_parse_segment_returns_ranked_products():
    import gartner
    html = (FIXTURES / "segment.html").read_text()
    products = gartner._parse_segment(html)
    assert len(products) >= 1
    assert products[0]["rank"] == 1
    assert "name" in products[0]
    assert products[0]["slug"] == "sap-s-4hana"
    assert products[0]["rating"] == 4.3
    assert products[0]["review_count"] == 1240


def test_parse_segment_raises_on_no_products():
    import gartner
    with pytest.raises(ValueError, match="Content validation failed"):
        gartner._parse_segment("<html><body>no products here</body></html>")


def test_parse_product_extracts_from_ldjson():
    import gartner
    html = (FIXTURES / "product.html").read_text()
    product = gartner._parse_product(html)
    assert product["overall_rating"] == 4.5
    assert product["review_count"] == 1847
    assert "SEO" in product["description"]


def test_parse_product_raises_on_no_structured_data():
    import gartner
    with pytest.raises(ValueError, match="Content validation failed"):
        gartner._parse_product("<html><body>no structured data here</body></html>")
