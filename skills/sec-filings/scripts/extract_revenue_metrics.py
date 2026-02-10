from __future__ import annotations

from sec_filings import get_latest_filing, FilingType

def extract_revenue_section(ticker, company_name, filing_type=FilingType.ANNUAL):
    """Extract revenue and financial metrics from MD&A section."""
    print(f"\n{'='*80}")
    print(f"{company_name} ({ticker}) - REVENUE & METRICS EXTRACTION")
    print(f"{'='*80}\n")

    filing = get_latest_filing(ticker, filing_type)
    print(f"Filing: {filing.form} filed {filing.date}\n")

    # MD&A typically starts around page 25-35 in 10-Ks
    # Look for revenue, growth, metrics
    for page_num in range(25, 45):
        try:
            content = filing.get_content(page=page_num)
            text = content.text.lower()

            # Check if this page has revenue discussion
            if ('revenue' in text and ('million' in text or 'billion' in text)) or \
               ('fiscal year' in text and 'results of operations' in text):
                print(f"\n## PAGE {page_num} - Revenue Discussion Found\n")
                # Print relevant sections
                full_text = filing.get_content(page=page_num).text
                lines = full_text.split('\n')

                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in ['revenue', 'fiscal year', 'total revenue', 'net revenue']):
                        # Print context
                        start = max(0, i-1)
                        end = min(len(lines), i+4)
                        print('\n'.join(lines[start:end]))
                        print()

                break  # Found the revenue section

        except Exception as e:
            if 'out of bounds' in str(e):
                break
            continue

companies = [
    ("COUR", "Coursera", FilingType.ANNUAL),
    ("UDMY", "Udemy", FilingType.ANNUAL),
    ("SKIL", "Skillsoft", FilingType.ANNUAL),
    ("CRM", "Salesforce", FilingType.ANNUAL),
    ("HUBS", "HubSpot", FilingType.ANNUAL),
]

if __name__ == "__main__":
    for ticker, name, filing_type in companies:
        try:
            extract_revenue_section(ticker, name, filing_type)
        except Exception as e:
            print(f"ERROR with {name}: {e}\n")
