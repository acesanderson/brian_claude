"""
SEC EDGAR filings fetcher.

Fetches 10-K, 10-Q, and 20-F filings using the SEC EDGAR API.
Requires stock ticker (not company name).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import httpx
import markdownify

if TYPE_CHECKING:
    from collections.abc import Iterator


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_FILING_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"

USER_AGENT = "CompanyResearch research@example.com"

CHARS_PER_PAGE = 8000


class FilingType(Enum):
    ANNUAL = "10-K"
    ANNUAL_FOREIGN = "20-F"
    QUARTERLY = "10-Q"


class TickerNotFoundError(Exception):
    """Raised when ticker is not found in SEC database."""


class NoFilingsError(Exception):
    """Raised when no filings of the requested type exist."""


@dataclass
class FilingContent:
    """Paginated filing content."""

    text: str
    metadata: dict
    table_of_contents: list[dict]


@dataclass
class Filing:
    """SEC filing metadata and content access."""

    form: str
    date: str
    cik: str
    accession: str
    document: str

    @property
    def url(self) -> str:
        return SEC_FILING_URL.format(
            cik=int(self.cik),
            accession=self.accession.replace("-", ""),
            document=self.document,
        )

    def get_content(self, page: int = 1) -> FilingContent:
        """Fetch and paginate filing content as markdown."""
        headers = {"User-Agent": USER_AGENT}
        response = httpx.get(
            self.url, headers=headers, timeout=30, follow_redirects=True
        )
        response.raise_for_status()

        md_content = markdownify.markdownify(response.text, heading_style="ATX")
        return _paginate(md_content, page)


def _paginate(content: str, page: int) -> FilingContent:
    """Paginate content for manageable chunks."""
    lines = content.splitlines()

    toc = [
        {"heading": line.strip(), "line": i + 1}
        for i, line in enumerate(lines)
        if line.strip().startswith("#")
    ]

    total_chars = len(content)
    total_pages = max(1, (total_chars + CHARS_PER_PAGE - 1) // CHARS_PER_PAGE)

    start = (page - 1) * CHARS_PER_PAGE
    end = start + CHARS_PER_PAGE

    if start >= total_chars and total_chars > 0:
        raise ValueError(f"Page {page} out of bounds. Total pages: {total_pages}")

    metadata = {
        "current_page": page,
        "total_pages": total_pages,
        "total_characters": total_chars,
        "has_more": page < total_pages,
    }

    return FilingContent(
        text=content[start:end],
        metadata=metadata,
        table_of_contents=toc if page == 1 else [],
    )


def _get_cik(ticker: str) -> str:
    """Look up CIK from ticker using SEC's ticker map."""
    headers = {"User-Agent": USER_AGENT}
    response = httpx.get(SEC_TICKERS_URL, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()
    ticker_upper = ticker.upper()

    for entry in data.values():
        if entry.get("ticker") == ticker_upper:
            return str(entry["cik_str"]).zfill(10)

    raise TickerNotFoundError(
        f"Ticker '{ticker}' not found in SEC database. "
        "Verify the ticker is correct and the company is publicly traded on a US exchange."
    )


def _fetch_submissions(cik: str) -> dict:
    """Fetch company submissions from SEC."""
    headers = {"User-Agent": USER_AGENT}
    url = SEC_SUBMISSIONS_URL.format(cik=cik.zfill(10))
    response = httpx.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def _iter_filings(cik: str, filing_type: FilingType) -> Iterator[Filing]:
    """Iterate through filings of the specified type, most recent first."""
    data = _fetch_submissions(cik)
    recent = data["filings"]["recent"]

    forms = recent["form"]
    dates = recent["filingDate"]
    accessions = recent["accessionNumber"]
    documents = recent["primaryDocument"]

    target_form = filing_type.value

    for form, date, accession, document in zip(forms, dates, accessions, documents):
        if form == target_form:
            yield Filing(
                form=form,
                date=date,
                cik=cik,
                accession=accession,
                document=document,
            )


def get_filings(
    ticker: str,
    filing_type: FilingType,
    limit: int = 5,
) -> list[Filing]:
    """
    Get recent filings of the specified type.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        filing_type: Type of filing to retrieve
        limit: Maximum number of filings to return

    Returns:
        List of Filing objects, most recent first

    Raises:
        TickerNotFoundError: If ticker is not in SEC database
        NoFilingsError: If no filings of the specified type exist
    """
    cik = _get_cik(ticker)
    filings = list(_iter_filings(cik, filing_type))[:limit]

    if not filings:
        raise NoFilingsError(
            f"No {filing_type.value} filings found for {ticker}. "
            "The company may file under a different form type."
        )

    return filings


def get_latest_filing(ticker: str, filing_type: FilingType) -> Filing:
    """
    Get the most recent filing of the specified type.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL")
        filing_type: Type of filing to retrieve

    Returns:
        Most recent Filing object

    Raises:
        TickerNotFoundError: If ticker is not in SEC database
        NoFilingsError: If no filings of the specified type exist
    """
    filings = get_filings(ticker, filing_type, limit=1)
    return filings[0]
