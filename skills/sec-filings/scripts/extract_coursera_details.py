from __future__ import annotations

from sec_filings import get_latest_filing, FilingType

# Get Coursera's latest 10-K
filing = get_latest_filing("COUR", FilingType.ANNUAL)
print(f"# COURSERA (COUR) - 10-K Filed {filing.date}\n")
print(f"URL: {filing.url}\n")

# Extract key pages based on our scan
key_pages = {
    5: "Business Overview & AI Initiatives",
    10: "Business Metrics & Platform Growth",
    15: "Risk Factors & Competition",
    20: "Risk Factors (continued)",
    25: "MD&A - Revenue & Growth",
    30: "MD&A - Financial Performance"
}

for page_num, section in key_pages.items():
    print(f"\n{'='*80}")
    print(f"PAGE {page_num}: {section}")
    print(f"{'='*80}\n")

    try:
        content = filing.get_content(page=page_num)
        # Print key excerpts
        text = content.text

        # Extract AI mentions
        if "AI" in text or "artificial intelligence" in text.lower():
            print("\n## AI Mentions:")
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'AI' in line or 'artificial intelligence' in line.lower():
                    # Print context (3 lines before and after)
                    context_start = max(0, i-2)
                    context_end = min(len(lines), i+3)
                    print('\n'.join(lines[context_start:context_end]))
                    print("\n---")

        # Print full page for pages with revenue/metrics
        if page_num in [10, 25, 30]:
            print(f"\n## Full Page Content:\n{text[:4000]}")  # First 4000 chars

    except Exception as e:
        print(f"Error: {e}")
