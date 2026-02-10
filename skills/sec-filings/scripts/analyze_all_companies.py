from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass

from sec_filings import get_latest_filing, FilingType

@dataclass
class CompanyAnalysis:
    ticker: str
    name: str
    filing_date: str
    filing_form: str

    def analyze_filing(self):
        """Analyze a company's filing for learning platform insights."""
        print(f"\n{'='*80}")
        print(f"ANALYZING: {self.name} ({self.ticker})")
        print(f"{'='*80}\n")

        # Get filing
        if self.ticker == "SAP":
            filing = get_latest_filing(self.ticker, FilingType.ANNUAL_FOREIGN)
        else:
            filing = get_latest_filing(self.ticker, FilingType.ANNUAL)

        print(f"Filing: {filing.form} filed {filing.date}")
        print(f"URL: {filing.url}\n")

        # Get first page for metadata
        first_page = filing.get_content(page=1)
        total_pages = first_page.metadata['total_pages']
        print(f"Total pages: {total_pages}\n")

        # Search for key terms across pages
        search_terms = [
            "learning", "education", "training", "course", "certificate",
            "AI", "artificial intelligence", "machine learning",
            "revenue", "growth", "compete", "competition", "risk"
        ]

        results = {
            "revenue_mentions": [],
            "ai_mentions": [],
            "learning_mentions": [],
            "competition_mentions": []
        }

        # Sample key pages
        pages_to_check = [5, 10, 15, 20, 25, 30, 35, 40]
        pages_to_check = [p for p in pages_to_check if p <= total_pages]

        for page_num in pages_to_check:
            try:
                content = filing.get_content(page=page_num)
                text_lower = content.text.lower()

                # Check for mentions
                if any(term in text_lower for term in ["revenue", "growth", "fiscal"]):
                    results["revenue_mentions"].append(page_num)

                if any(term in text_lower for term in ["ai", "artificial intelligence", "machine learning"]):
                    results["ai_mentions"].append(page_num)

                if any(term in text_lower for term in ["learning", "education", "training", "course"]):
                    results["learning_mentions"].append(page_num)

                if any(term in text_lower for term in ["compete", "competition", "competitive"]):
                    results["competition_mentions"].append(page_num)

            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                continue

        print(f"Revenue/Growth mentions on pages: {results['revenue_mentions']}")
        print(f"AI mentions on pages: {results['ai_mentions']}")
        print(f"Learning mentions on pages: {results['learning_mentions']}")
        print(f"Competition mentions on pages: {results['competition_mentions']}")

        return results


companies = [
    CompanyAnalysis("COUR", "Coursera", "2025-02-24", "10-K"),
    CompanyAnalysis("UDMY", "Udemy", "2025-02-19", "10-K"),
    CompanyAnalysis("SKIL", "Skillsoft", "2025-04-14", "10-K"),
    CompanyAnalysis("GOOGL", "Alphabet/Google", "2026-02-05", "10-K"),
    CompanyAnalysis("CRM", "Salesforce", "2025-03-05", "10-K"),
    CompanyAnalysis("HUBS", "HubSpot", "2025-02-12", "10-K"),
    CompanyAnalysis("SAP", "SAP", "2025-02-27", "20-F"),
]

if __name__ == "__main__":
    for company in companies:
        try:
            company.analyze_filing()
        except Exception as e:
            print(f"\nERROR analyzing {company.name}: {e}\n")
            continue
