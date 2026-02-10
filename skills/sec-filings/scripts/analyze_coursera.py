from __future__ import annotations

from sec_filings import get_latest_filing, FilingType

# Get Coursera's latest 10-K
filing = get_latest_filing("COUR", FilingType.ANNUAL)
print(f"Analyzing Coursera 10-K filed {filing.date}")
print(f"Total pages: {filing.get_content(page=1).metadata['total_pages']}\n")

# Try several pages to find where business content starts
for page_num in [5, 10, 15]:
    print(f"\n{'='*80}")
    print(f"PAGE {page_num} - First 2000 chars")
    print(f"{'='*80}")
    content = filing.get_content(page=page_num)
    print(content.text[:2000])
