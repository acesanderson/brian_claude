#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx>=0.27",
#   "click>=8.0",
# ]
# ///
"""Firecrawl CLI — optimized for agentic use. All output is JSON to stdout, errors to stderr."""

from __future__ import annotations

import json
import os
import sys
import time
from typing import TYPE_CHECKING

import click
import httpx

if TYPE_CHECKING:
    pass

BASE_URL = os.environ.get("FIRECRAWL_URL", "http://172.16.0.4:3002").rstrip("/")
API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
DEFAULT_POLL_INTERVAL = 2.0
DEFAULT_TIMEOUT = 300.0


def _headers() -> dict[str, str]:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["Authorization"] = f"Bearer {API_KEY}"
    return h


def _post(path: str, body: dict) -> dict:
    with httpx.Client(headers=_headers(), timeout=300) as c:
        resp = c.post(f"{BASE_URL}{path}", json=body)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        click.echo(f"error: HTTP {e.response.status_code}: {e.response.text}", err=True)
        sys.exit(1)
    return resp.json()


def _get(path: str) -> dict:
    with httpx.Client(headers=_headers(), timeout=60) as c:
        resp = c.get(f"{BASE_URL}{path}")
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        click.echo(f"error: HTTP {e.response.status_code}: {e.response.text}", err=True)
        sys.exit(1)
    return resp.json()


def _poll(path: str, job_id: str, interval: float, timeout: float) -> dict:
    """Poll GET /v1/{path}/{job_id} until status reaches a terminal state."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        data = _get(f"/v1/{path}/{job_id}")
        status = data.get("status", "")
        if status in ("completed", "failed", "cancelled"):
            return data
        time.sleep(interval)
    click.echo(f"error: timed out waiting for {path}/{job_id} after {timeout}s", err=True)
    sys.exit(1)


def _out(data: dict | list) -> None:
    click.echo(json.dumps(data, indent=2))


# ── shared option factories ────────────────────────────────────────────────────

def _wait_opts(f):
    f = click.option("--wait/--no-wait", default=True, show_default=True,
                     help="Poll until async job completes")(f)
    f = click.option("--poll-interval", default=DEFAULT_POLL_INTERVAL,
                     metavar="SECS", show_default=True,
                     help="Seconds between status polls")(f)
    f = click.option("--poll-timeout", default=DEFAULT_TIMEOUT,
                     metavar="SECS", show_default=True,
                     help="Give up polling after N seconds")(f)
    return f


def _fmt_opt(f):
    return click.option(
        "-f", "--format", "fmt",
        type=click.Choice(["markdown", "html", "rawHtml", "links", "screenshot"]),
        default="markdown", show_default=True,
        help="Content format for scraped pages",
    )(f)


def _proxy_opt(f):
    return click.option(
        "--proxy", default=None,
        type=click.Choice(["basic", "stealth"]),
        help="Proxy tier — use 'stealth' for bot-protected pages",
    )(f)


# ── CLI group ─────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """Firecrawl — web scraping CLI. Server: {url}

    All commands write JSON to stdout. Pass output through jq for filtering.
    Async commands (crawl, batch, extract) poll until complete by default.
    """.format(url=BASE_URL)


# ── scrape ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("url")
@_fmt_opt
@_proxy_opt
@click.option("--only-main/--no-only-main", default=True, show_default=True,
              help="Strip navigation/ads, keep main body")
@click.option("--include-tags", multiple=True, metavar="TAG",
              help="Restrict extraction to these HTML tags (repeatable)")
@click.option("--exclude-tags", multiple=True, metavar="TAG",
              help="Remove these HTML tags before extraction (repeatable)")
@click.option("--wait-for", default=0, metavar="MS",
              help="Extra wait time for JS-heavy pages")
@click.option("--schema", default=None, metavar="JSON",
              help="JSON schema for structured LLM extraction")
@click.option("--prompt", default=None, metavar="TEXT",
              help="Natural-language extraction prompt (use with --schema or alone)")
@click.option("--system-prompt", default=None, metavar="TEXT",
              help="System prompt override for LLM extraction")
@click.option("--timeout", default=None, type=int, metavar="MS",
              help="Firecrawl scrape timeout in milliseconds (default: 30000; use higher for LLM extraction with slow models)")
def scrape(url, fmt, proxy, only_main, include_tags, exclude_tags, wait_for,
           schema, prompt, system_prompt, timeout):
    """Scrape a single URL and return its content.

    With --schema / --prompt, runs LLM extraction and returns structured JSON.
    Otherwise returns the page in the requested --format (default: markdown).

    Examples:

      fc scrape https://example.com

      fc scrape https://example.com --format html

      fc scrape https://example.com --prompt "extract all prices"

      fc scrape https://example.com --schema '{"type":"object","properties":{"title":{"type":"string"}}}'
    """
    use_llm = bool(schema or prompt)
    resolved_timeout = timeout if timeout is not None else (60000 if use_llm else None)
    body: dict = {
        "url": url,
        "formats": ["json"] if use_llm else [fmt],
        "onlyMainContent": only_main,
    }
    if resolved_timeout is not None:
        body["timeout"] = resolved_timeout
    if proxy:
        body["proxy"] = proxy
    if include_tags:
        body["includeTags"] = list(include_tags)
    if exclude_tags:
        body["excludeTags"] = list(exclude_tags)
    if wait_for:
        body["waitFor"] = wait_for
    if use_llm:
        opts: dict = {}
        if schema:
            opts["schema"] = json.loads(schema)
        if prompt:
            opts["prompt"] = prompt
        if system_prompt:
            opts["systemPrompt"] = system_prompt
        body["jsonOptions"] = opts

    _out(_post("/v1/scrape", body))


# ── crawl ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("url")
@_fmt_opt
@click.option("-n", "--limit", default=100, show_default=True,
              help="Max pages to crawl")
@click.option("--depth", default=None, type=int, metavar="N",
              help="Max link-follow depth from start URL")
@click.option("--include", "include_paths", multiple=True, metavar="REGEX",
              help="Only follow paths matching this regex (repeatable)")
@click.option("--exclude", "exclude_paths", multiple=True, metavar="REGEX",
              help="Skip paths matching this regex (repeatable)")
@click.option("--only-main/--no-only-main", default=True, show_default=True)
@_proxy_opt
@_wait_opts
def crawl(url, fmt, limit, depth, include_paths, exclude_paths, only_main, proxy,
          wait, poll_interval, poll_timeout):
    """Crawl a site recursively, scraping each discovered page.

    Returns the crawl job ID immediately with --no-wait, or blocks until
    complete (default). Use `fc status crawl <id>` to check manually.

    Examples:

      fc crawl https://docs.example.com --limit 50

      fc crawl https://example.com --include 'blog/.*' --depth 3

      fc crawl https://example.com --no-wait
    """
    scrape_opts: dict = {"formats": [fmt], "onlyMainContent": only_main}
    if proxy:
        scrape_opts["proxy"] = proxy
    body: dict = {"url": url, "limit": limit, "scrapeOptions": scrape_opts}
    if depth is not None:
        body["maxDepth"] = depth
    if include_paths:
        body["includePaths"] = list(include_paths)
    if exclude_paths:
        body["excludePaths"] = list(exclude_paths)

    resp = _post("/v1/crawl", body)
    job_id = resp.get("id")
    if not job_id:
        _out(resp)
        return

    if not wait:
        _out({"job_id": job_id, "status": "pending", "start_url": url})
        return

    _out(_poll("crawl", job_id, poll_interval, poll_timeout))


# ── map ───────────────────────────────────────────────────────────────────────

@cli.command("map")
@click.argument("url")
@click.option("--include", "include_paths", multiple=True, metavar="REGEX")
@click.option("--exclude", "exclude_paths", multiple=True, metavar="REGEX")
@click.option("-n", "--limit", default=5000, show_default=True,
              help="Max URLs to return")
@click.option("--search", default=None, metavar="TERM",
              help="Filter returned URLs to those containing TERM")
def map_cmd(url, include_paths, exclude_paths, limit, search):
    """Return all discoverable URLs from a site without scraping content.

    Much faster than crawl when you only need the URL list.

    Examples:

      fc map https://example.com

      fc map https://example.com --search pricing

      fc map https://example.com | jq '.links[]'
    """
    body: dict = {"url": url, "limit": limit}
    if include_paths:
        body["includePaths"] = list(include_paths)
    if exclude_paths:
        body["excludePaths"] = list(exclude_paths)
    if search:
        body["search"] = search
    _out(_post("/v1/map", body))


# ── search ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("query")
@click.option("-n", "--limit", default=5, show_default=True,
              help="Number of search results")
@click.option("--scrape/--no-scrape", "do_scrape", default=False,
              help="Also scrape the full content of each result")
@_fmt_opt
@click.option("--req-timeout", default=60000, show_default=True,
              metavar="MS", help="Per-request timeout in milliseconds")
def search(query, limit, do_scrape, fmt, req_timeout):
    """Search the web and optionally scrape each result.

    Without --scrape, returns metadata (title, URL, snippet) only.
    With --scrape, returns full page content in --format for each result.

    Examples:

      fc search "firecrawl python" --limit 10

      fc search "site:docs.example.com api reference" --scrape

      fc search "python async patterns" --scrape --format html
    """
    body: dict = {"query": query, "limit": limit, "timeout": req_timeout}
    if do_scrape:
        body["scrapeOptions"] = {"formats": [fmt]}
    _out(_post("/v1/search", body))


# ── batch ─────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("urls", nargs=-1, required=True)
@_fmt_opt
@click.option("--only-main/--no-only-main", default=True, show_default=True)
@_proxy_opt
@_wait_opts
def batch(urls, fmt, only_main, proxy, wait, poll_interval, poll_timeout):
    """Scrape multiple URLs in parallel as a single job.

    More efficient than running scrape N times. Use --no-wait to get a job
    ID you can poll with `fc status batch <id>`.

    Examples:

      fc batch https://a.com https://b.com https://c.com

      fc batch $(cat urls.txt) --format html

      fc batch https://a.com https://b.com --no-wait
    """
    body: dict = {"urls": list(urls), "formats": [fmt], "onlyMainContent": only_main}
    if proxy:
        body["proxy"] = proxy
    resp = _post("/v1/batch/scrape", body)
    job_id = resp.get("id")
    if not job_id:
        _out(resp)
        return

    if not wait:
        _out({"job_id": job_id, "status": "pending", "url_count": len(urls)})
        return

    _out(_poll("batch/scrape", job_id, poll_interval, poll_timeout))


# ── extract ───────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("urls", nargs=-1, required=True)
@click.option("--schema", default=None, metavar="JSON",
              help="JSON schema defining the structure to extract")
@click.option("--prompt", default=None, metavar="TEXT",
              help="Natural-language extraction instruction")
@click.option("--system-prompt", default=None, metavar="TEXT")
@_wait_opts
def extract(urls, schema, prompt, system_prompt, wait, poll_interval, poll_timeout):
    """LLM-powered structured extraction across one or more URLs.

    Combines scraping + LLM reasoning to pull typed data from pages.
    Ideal when you need consistent structure across many pages.

    Examples:

      fc extract https://example.com/product --prompt "get product name and price"

      fc extract https://a.com https://b.com \\
        --schema '{"type":"object","properties":{"price":{"type":"number"}}}'
    """
    body: dict = {"urls": list(urls)}
    if schema:
        body["schema"] = json.loads(schema)
    if prompt:
        body["prompt"] = prompt
    if system_prompt:
        body["systemPrompt"] = system_prompt

    resp = _post("/v1/extract", body)
    job_id = resp.get("id")
    if not job_id:
        _out(resp)
        return

    if not wait:
        _out({"job_id": job_id, "status": "pending"})
        return

    _out(_poll("extract", job_id, poll_interval, poll_timeout))


# ── status ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("verb", type=click.Choice(["crawl", "batch", "extract"]))
@click.argument("job_id")
def status(verb, job_id):
    """Check the current status of an async job.

    VERB is one of: crawl, batch, extract

    Examples:

      fc status crawl abc123

      fc status batch xyz789
    """
    path_map = {"crawl": "crawl", "batch": "batch/scrape", "extract": "extract"}
    _out(_get(f"/v1/{path_map[verb]}/{job_id}"))


# ── cancel ────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("job_id")
def cancel(job_id):
    """Cancel a running crawl job.

    Example:

      fc cancel abc123
    """
    with httpx.Client(headers=_headers(), timeout=30) as c:
        resp = c.delete(f"{BASE_URL}/v1/crawl/{job_id}")
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        click.echo(f"error: HTTP {e.response.status_code}: {e.response.text}", err=True)
        sys.exit(1)
    _out(resp.json())


if __name__ == "__main__":
    cli()
