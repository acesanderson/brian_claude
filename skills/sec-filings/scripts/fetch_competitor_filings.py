from __future__ import annotations

from sec_filings import get_latest_filing, FilingType, TickerNotFoundError, NoFilingsError

COMPANIES = {
    "COUR": "Coursera",
    "UDMY": "Udemy",
    "SKIL": "Skillsoft",
    "GOOGL": "Alphabet/Google",
    "CRM": "Salesforce",
    "HUBS": "HubSpot",
    "SAP": "SAP"
}

def fetch_filings_for_company(ticker: str, company_name: str):
    """Fetch latest annual and quarterly filings for a company."""
    print(f"\n{'='*80}")
    print(f"{company_name} ({ticker})")
    print(f"{'='*80}")

    results = {
        "ticker": ticker,
        "company": company_name,
        "annual": None,
        "quarterly": None,
        "errors": []
    }

    # Try to get annual filing (10-K first, then 20-F for foreign companies)
    for filing_type in [FilingType.ANNUAL, FilingType.ANNUAL_FOREIGN]:
        try:
            annual = get_latest_filing(ticker, filing_type)
            results["annual"] = annual
            print(f"\n✓ Annual Report ({annual.form})")
            print(f"  Filed: {annual.date}")
            print(f"  URL: {annual.url}")
            break
        except NoFilingsError:
            if filing_type == FilingType.ANNUAL_FOREIGN:
                results["errors"].append(f"No annual filings (tried 10-K and 20-F)")
            continue
        except TickerNotFoundError as e:
            results["errors"].append(f"Ticker not found: {e}")
            print(f"\n✗ Error: {e}")
            return results

    # Try to get quarterly filing
    try:
        quarterly = get_latest_filing(ticker, FilingType.QUARTERLY)
        results["quarterly"] = quarterly
        print(f"\n✓ Quarterly Report ({quarterly.form})")
        print(f"  Filed: {quarterly.date}")
        print(f"  URL: {quarterly.url}")
    except NoFilingsError:
        results["errors"].append("No quarterly filings (10-Q)")
        print(f"\n✗ No quarterly filings found")
    except TickerNotFoundError as e:
        results["errors"].append(f"Ticker not found: {e}")
        print(f"\n✗ Error: {e}")

    return results

def main():
    all_results = []

    for ticker, company_name in COMPANIES.items():
        results = fetch_filings_for_company(ticker, company_name)
        all_results.append(results)

    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    for result in all_results:
        status = []
        if result["annual"]:
            status.append(f"{result['annual'].form} ({result['annual'].date})")
        else:
            status.append("No annual")

        if result["quarterly"]:
            status.append(f"{result['quarterly'].form} ({result['quarterly'].date})")
        else:
            status.append("No quarterly")

        print(f"{result['company']:25} ({result['ticker']:5}): {' | '.join(status)}")

        if result["errors"]:
            for error in result["errors"]:
                print(f"  ⚠ {error}")

    return all_results

if __name__ == "__main__":
    results = main()
