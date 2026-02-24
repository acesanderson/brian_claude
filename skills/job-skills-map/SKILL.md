---
name: onet_api
description: >
  Query the O*NET Web Services API to map occupations to their required competencies.
  Use when the user wants to search for occupations by keyword and get O*NET-SOC codes,
  get a breakdown of skills, knowledge, abilities, and technology tools for a specific
  occupation, or run a "course gap analysis" that outputs teachable competencies ranked
  by importance score. Trigger phrases include "what skills does a [job title] need",
  "O*NET competencies for [occupation]", "course topics for [role]", "gap analysis for
  [job]", "what should I teach for [occupation]", "find SOC code for [keyword]".
  Requires ONET_API_KEY (v2.0) or ONET_USERNAME + ONET_PASSWORD (v1.9) env vars.
---

# Job Skills Map

Wraps the O*NET Web Services API via `scripts/onet.py`.

## Auth

| Env var | API version |
|---------|-------------|
| `ONET_API_KEY` | v2.0 (current) |
| `ONET_USERNAME` + `ONET_PASSWORD` | v1.9 (legacy, from developers registration) |

Get credentials: https://services.onetcenter.org/developers/

If neither is set, the script exits with an error message.

## Workflow

### 1. Search occupations

```bash
python3 scripts/onet.py search "data engineer"
```

Output: `{ "keyword", "total", "results": [{"code", "title", "tags"}] }`

Pick the SOC code (e.g. `15-1243.01`) that best matches the user's intent.

### 2. Get full breakdown

```bash
python3 scripts/onet.py breakdown 15-1243.01
```

Output: `{ "code", "breakdown": { "knowledge", "skills", "abilities", "technology_skills" } }`

Each competency item: `{ "id", "name", "description", "importance" }` (importance 0-100).
Technology items: `{ "name", "category", "hot_technology", "in_demand" }`.

### 3. Course gap analysis

```bash
python3 scripts/onet.py gap-analysis 15-1243.01
```

Output:
```json
{
  "occupation_code": "15-1243.01",
  "course_topics": [
    {"category": "knowledge", "id": "2.C.3.e", "name": "Computers and Electronics",
     "description": "...", "importance": 90.0},
    {"category": "skills", "id": "2.A.1.e", "name": "Critical Thinking",
     "description": "...", "importance": 82.5}
  ],
  "technology_tools": [
    {"name": "Apache Spark", "category": "Data base management system software",
     "hot_technology": true, "in_demand": true}
  ]
}
```

`course_topics` merges knowledge + skills + abilities, sorted by `importance` descending (0-100 scale).
`technology_tools` is listed separately — no importance score; use `hot_technology`/`in_demand` as relevance signals.

## Presenting gap analysis to the user

Format `course_topics` as a ranked table: **Rank | Category | Name | Importance | Description snippet**.
Show the top ~20 topics. Then list notable tech tools (flag `hot_technology: true` ones clearly).

Suggest course title mappings. Example: "Computers and Electronics (knowledge, 90)" → "Computer Architecture & Systems Fundamentals".

## Dependency

```
pip install requests
```

## API reference

See `references/api_docs.md` for endpoint schemas, v1.9 vs v2.0 response differences, error codes, and common SOC codes.
