from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CACHE_DIR = Path(__file__).parent / "cache"
SEGMENT_LIST_TTL = 7 * 24 * 3600   # 7 days
SEGMENT_TTL = 24 * 3600            # 1 day
PRODUCT_TTL = 24 * 3600            # 1 day

BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
PRODUCT_URL_RE = re.compile(r"gartner\.com/reviews/product/([^\"&\s/?]+)")

# Confirmed from live HTML inspection (2026-03-18):
# Product pages embed a <script type="application/ld+json" data-testid="product-structured-data">
# block containing schema.org/Product with aggregateRating (ratingValue, reviewCount).
# This is more reliable than CSS class matching — Gartner uses hashed CSS module names
# (e.g. product-ratings_exp-value__Zuof7) that change on each deploy.


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def _cache_get(key: str, ttl_seconds: int) -> dict | None:
    path = _cache_path(key)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl_seconds:
        return None
    return json.loads(path.read_text())


def _cache_set(key: str, data: dict) -> dict:
    path = _cache_path(key)
    CACHE_DIR.mkdir(exist_ok=True)
    stored = {**data, "cached_at": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(stored))
    return stored


# ---------------------------------------------------------------------------
# Browser fetch
# ---------------------------------------------------------------------------

def _fetch_with_browser(url: str) -> str:
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    username = os.getenv("OXY_NAME")
    password = os.getenv("OXY_PASSWORD")
    if not username or not password:
        raise ValueError("Missing OXY_NAME or OXY_PASSWORD environment variables")

    proxy = {
        "server": "http://pr.oxylabs.io:7777",
        "username": f"customer-{username}",
        "password": password,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            proxy=proxy,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
            pg = ctx.new_page()
            Stealth().apply_stealth_sync(pg)
            response = pg.goto(url, timeout=60000, wait_until="load")
            if response and response.status == 403:
                raise RuntimeError(f"HTTP 403 from {url}")
            pg.wait_for_timeout(4000)
            html = pg.content()
        finally:
            browser.close()

    return html


def _fetch_with_retry(url: str, validate_fn: Callable[[str], bool]) -> str:
    last_error = "Unknown error"
    for attempt in range(3):
        if attempt > 0:
            wait = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait)
        try:
            html = _fetch_with_browser(url)
            if not validate_fn(html):
                last_error = "Content validation failed (possible CAPTCHA or partial load)"
                continue
            return html
        except ValueError:
            raise  # credential error — not retryable
        except Exception as e:
            last_error = str(e)
    raise RuntimeError(f"Fetch failed after 3 attempts. Last error: {last_error}")


# ---------------------------------------------------------------------------
# HTML parsers
# ---------------------------------------------------------------------------

def _parse_segment_list(html: str) -> list[dict]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    seen: set[str] = set()
    segments = []
    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        if href.startswith("/reviews/market/"):
            slug = href.split("/reviews/market/")[1].rstrip("/")
            if slug and slug not in seen:
                seen.add(slug)
                segments.append({"slug": slug, "name": a.get_text(strip=True)})
    if len(segments) < 10:
        raise ValueError(
            f"Content validation failed: only {len(segments)} segments found (expected >=10)"
        )
    return segments


def _parse_segment(html: str) -> list[dict]:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    product_links = soup.find_all("a", href=lambda h: h and "/reviews/product/" in h)
    if not product_links:
        raise ValueError("Content validation failed: no product links found")
    seen: set[str] = set()
    products = []
    for a in product_links:
        href: str = a["href"]
        slug = href.split("/reviews/product/")[1].rstrip("/")
        if slug in seen:
            continue
        seen.add(slug)
        name = a.get_text(strip=True)
        if not name:
            continue
        container = a.find_parent()  # immediate parent element
        rating = None
        review_count = None
        if container:
            rating_match = re.search(r"(\d+\.\d+)\s*/\s*5", container.get_text())
            if rating_match:
                rating = float(rating_match.group(1))
            count_match = re.search(r"([\d,]+)\s+reviews?", container.get_text(), re.IGNORECASE)
            if count_match:
                review_count = int(count_match.group(1).replace(",", ""))
        products.append({
            "rank": len(products) + 1,
            "name": name,
            "slug": slug,
            "rating": rating,
            "review_count": review_count,
        })
    if not products:
        raise ValueError("Content validation failed: no products parsed")
    if not any(p["rating"] is not None for p in products):
        raise ValueError("Content validation failed: no rating data extracted from any product")
    return products


def _parse_product(html: str) -> dict:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    script = soup.find("script", attrs={"data-testid": "product-structured-data"})
    if not script:
        raise ValueError("Content validation failed: no product structured data found")
    data = json.loads(script.get_text())
    agg = data.get("aggregateRating", {})
    return {
        "overall_rating": float(agg.get("ratingValue", 0)),
        "review_count": int(agg.get("reviewCount", 0)),
        "description": data.get("description", ""),
    }


# ---------------------------------------------------------------------------
# Brave search — product slug resolution
# ---------------------------------------------------------------------------

def _brave_search_product_slug(name: str) -> str:
    import httpx

    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        raise ValueError("Missing BRAVE_API_KEY environment variable")

    resp = httpx.get(
        BRAVE_API_URL,
        headers={"X-Subscription-Token": api_key, "Accept": "application/json"},
        params={"q": f"site:gartner.com/reviews/product {name}", "count": 5},
        timeout=10,
    )
    resp.raise_for_status()

    for result in resp.json().get("web", {}).get("results", []):
        m = PRODUCT_URL_RE.search(result.get("url", ""))
        if m:
            return m.group(1)

    raise ValueError(f"No Gartner product page found for: {name}")


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def op_segment_list(refresh: bool) -> dict:
    key = "segment-list"
    if not refresh:
        cached = _cache_get(key, SEGMENT_LIST_TTL)
        if cached is not None:
            return {**cached, "cached": True}

    html = _fetch_with_retry(
        "https://www.gartner.com/reviews/home",
        lambda h: h.count("/reviews/market/") >= 10,
    )
    segments = _parse_segment_list(html)
    data = _cache_set(key, {"segments": segments, "cached": False})
    return data


def op_segment(slug: str, refresh: bool) -> dict:
    key = f"segment-{slug}"
    if not refresh:
        cached = _cache_get(key, SEGMENT_TTL)
        if cached is not None:
            return {**cached, "cached": True}

    html = _fetch_with_retry(
        f"https://www.gartner.com/reviews/market/{slug}",
        lambda h: "/reviews/product/" in h,
    )
    products = _parse_segment(html)
    data = _cache_set(key, {"slug": slug, "products": products, "cached": False})
    return data


def _get_product_slug(name: str) -> str:
    """Resolve product name to Gartner slug, with caching."""
    normalized = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    key = f"slug-{normalized}"
    cached = _cache_get(key, PRODUCT_TTL)
    if cached is not None:
        return cached["slug"]
    slug = _brave_search_product_slug(name)
    _cache_set(key, {"slug": slug})
    return slug


def op_product(name: str, refresh: bool) -> dict:
    slug = _get_product_slug(name)
    key = f"product-{slug}"
    if not refresh:
        cached = _cache_get(key, PRODUCT_TTL)
        if cached is not None:
            return {**cached, "cached": True}

    url = f"https://www.gartner.com/reviews/product/{slug}"
    html = _fetch_with_retry(
        url,
        lambda h: '"product-structured-data"' in h,
    )
    profile = _parse_product(html)
    data = _cache_set(key, {
        "name": name,
        "slug": slug,
        "url": url,
        **profile,
        "cached": False,
    })
    return data


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Gartner Peer Insights scraper")
    sub = parser.add_subparsers(dest="command", required=True)

    sl = sub.add_parser("segment-list")
    sl.add_argument("--refresh", action="store_true", default=False)

    seg = sub.add_parser("segment")
    seg.add_argument("slug")
    seg.add_argument("--refresh", action="store_true", default=False)

    prod = sub.add_parser("product")
    prod.add_argument("name")
    prod.add_argument("--refresh", action="store_true", default=False)

    args = parser.parse_args()

    try:
        if args.command == "segment-list":
            result = op_segment_list(args.refresh)
        elif args.command == "segment":
            result = op_segment(args.slug, args.refresh)
        else:
            result = op_product(args.name, args.refresh)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
