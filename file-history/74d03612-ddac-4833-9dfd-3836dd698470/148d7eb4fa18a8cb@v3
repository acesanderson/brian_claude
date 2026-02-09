---
name: find-catalogues
description: Discover training portal URLs for companies. Use when the user needs to find course catalog or training platform URLs for one or more companies before scraping them. Takes company names as input and outputs structured data with discovered training platform URLs. Trigger phrases include "find training URLs for [companies]", "discover course catalogs for [companies]", "locate learning platforms for [companies]", or when preparing to scrape multiple companies without known URLs.
---

# Find Catalogues

Discover training portal URLs for companies using web search and reconnaissance.

**Required MCP Tools:** This skill uses `web_search` and `fetch_url` from the `conduit-websearch` MCP server. These tools provide:
- `web_search` - Brave Search API with reliable results
- `fetch_url` - Advanced URL fetching with HTML→Markdown conversion, PDF/Office doc support

## Input

**Company names** - One or more company names (e.g., "Zapier", "KodeKloud", "DeepLearning.AI")

## Output

Structured JSON mapping each company to its discovered training platform URL(s):

```json
{
  "Zapier": {
    "primary_url": "https://learn.zapier.com/courses",
    "alternative_urls": ["https://zapier.com/university"],
    "confidence": "high",
    "notes": "Dedicated learning platform with structured course catalog"
  },
  "KodeKloud": {
    "primary_url": "https://kodekloud.com/courses/",
    "alternative_urls": [],
    "confidence": "high",
    "notes": "Main site with /courses path"
  }
}
```

## Workflow

For each company:

### 1. Web Search for Training Platforms

**Use the `web_search` MCP tool** to search for variations:
- `"{company name}" training courses`
- `"{company name}" learning platform`
- `"{company name}" academy`
- `"{company name}" certification courses`
- `"{company name}" education portal`

The `web_search` tool uses Brave Search API and returns structured results with titles, URLs, and snippets.

### 2. Identify Candidate URLs

Look for:
- Dedicated learning domains (e.g., `learn.company.com`, `academy.company.com`, `university.company.com`)
- Main site training sections (e.g., `company.com/training`, `company.com/courses`, `company.com/learn`)
- Third-party platforms (e.g., Skilljar, Thinkific, Teachable hosting)

Common patterns:
- `learn.{domain}` or `academy.{domain}` or `training.{domain}`
- `{domain}/courses` or `{domain}/learning` or `{domain}/training`
- `{domain}/education` or `{domain}/certifications`

### 3. Validate URL Quality

**Use the `fetch_url` MCP tool** to verify each candidate URL:
- Does it contain a course catalog or listing?
- Is it publicly accessible (not behind authentication)?
- Does it have structured course data?

The `fetch_url` tool converts HTML/PDF/Office docs to clean Markdown and handles anti-bot protection better than standard fetching.

**Confidence levels:**
- `high` - Dedicated learning platform with clear course catalog
- `medium` - Training section exists but structure unclear
- `low` - Limited information, may require authentication
- `none` - No training platform found

### 4. Return Results

Output JSON with:
- `primary_url` - Best candidate for scraping
- `alternative_urls` - Other potential training URLs found
- `confidence` - Assessment of URL quality
- `notes` - Brief description of platform type and any obstacles

## Output Format

Save results to `training_urls.json`:

```json
{
  "discovery_date": "2026-02-09",
  "companies_searched": 14,
  "companies_found": 12,
  "results": {
    "Company Name": {
      "primary_url": "https://...",
      "alternative_urls": ["https://..."],
      "confidence": "high|medium|low|none",
      "notes": "Description of platform"
    }
  }
}
```

## Best Practices

1. **Search broadly** - Use `web_search` with multiple query variations
2. **Verify thoroughly** - Use `fetch_url` to confirm URLs contain actual course catalogs
3. **Note obstacles** - Document authentication walls, CAPTCHA, or other barriers discovered by `fetch_url`
4. **Prioritize official platforms** - Prefer company-owned domains over third-party hosted content
5. **Be concise** - Keep notes brief but informative

## Tool Usage Tips

- **`web_search`** returns top 5 results - scan all of them for learning platform domains
- **`fetch_url`** handles HTML, PDF, and Office docs - perfect for checking different page types
- **Paginated content** - If `fetch_url` shows truncated content, use `page=2` to continue reading
- **Anti-bot protection** - `fetch_url` uses proper User-Agent headers and handles redirects

## Example Usage

**Input:** `["Zapier", "KodeKloud", "DeepLearning.AI"]`

**Process:**
1. **Search for Zapier:**
   - Use `web_search("Zapier training courses")` → Find `learn.zapier.com` in results
   - Use `fetch_url("https://learn.zapier.com")` → Verify course catalog structure
   - Record: `primary_url: "https://learn.zapier.com"`, `confidence: "high"`

2. **Search for KodeKloud:**
   - Use `web_search("KodeKloud courses")` → Find `kodekloud.com/courses`
   - Use `fetch_url("https://kodekloud.com/courses/")` → Confirm 180+ courses visible
   - Record: `primary_url: "https://kodekloud.com/courses/"`, `confidence: "high"`

3. **Search for DeepLearning.AI:**
   - Use `web_search("DeepLearning.AI catalog")` → Find `www.deeplearning.ai/courses`
   - Use `fetch_url("https://www.deeplearning.ai/courses/")` → Confirm course listings
   - Record: `primary_url: "https://www.deeplearning.ai/courses/"`, `confidence: "high"`

4. **Save results to `training_urls.json`** with discovered URLs and confidence ratings
