# O*NET Web Services API Reference

## Versions & Auth

| Version | Base URL | Auth |
|---------|----------|------|
| v2.0 (current) | `https://api-v2.onetcenter.org` | `X-API-Key: <key>` header |
| v1.9 (legacy) | `https://services.onetcenter.org/ws` | HTTP Basic Auth (username:password) |

Credentials (both versions): register at https://services.onetcenter.org/developers/

v1.9 credentials are username+password; v2.0 generates an API key in the account dashboard.

---

## Endpoints Used by `onet.py`

### Search

```
GET /mnm/search?keyword=<phrase>&end=<n>
```

Response:
```json
{
  "keyword": "data engineer",
  "total": 12,
  "career": [
    {"code": "15-1243.01", "title": "Data Warehousing Specialists", "tags": {"bright_outlook": true}}
  ]
}
```

### Competency Details (skills / knowledge / abilities)

```
GET /online/occupations/{soc_code}/details/{resource}?end=200
```

`resource` = `skills` | `knowledge` | `abilities`

**v2.0 response element:**
```json
{"id": "2.A.1.b", "name": "Active Listening", "description": "...", "importance": 75}
```
`importance` is 0-100.

**v1.9 response element:**
```json
{
  "id": "2.A.1.b", "name": "Active Listening", "description": "...",
  "scale": [
    {"id": "IM", "name": "Importance", "value": 4.25},
    {"id": "LV", "name": "Level",      "value": 3.50}
  ]
}
```
v1.9 importance scale is 1-5; `onet.py` normalizes to 0-100: `(value - 1) / 4 * 100`.

### Technology Skills

```
GET /online/occupations/{soc_code}/summary/technology_skills?end=200
```

Response:
```json
{
  "category": [
    {
      "title": "Development environment software",
      "example": [
        {"title": "Git", "hot_technology": true, "in_demand": true, "percentage": 45}
      ]
    }
  ]
}
```
No importance scores for tech tools. `hot_technology` and `in_demand` flags can be used as proxies for relevance.

---

## Pagination

All list endpoints support `start` (default 1) and `end` (default 20, max 2000).
`onet.py` uses `end=200` which is sufficient for all occupation competency lists.
If a response includes a `"next"` field, additional pages exist.

## Error Codes

| Code | Meaning |
|------|---------|
| 401 | Auth failed (wrong credentials or missing header) |
| 404 | SOC code not found or endpoint path wrong |
| 422 | Bad parameters |
| 429 | Rate limited — retry after 200ms |

---

## Common SOC Codes (for quick testing)

| Occupation | Code |
|-----------|------|
| Software Developers | 15-1252.00 |
| Data Scientists | 15-2051.00 |
| Data Engineers (Data Warehousing) | 15-1243.01 |
| Information Security Analysts | 15-1212.00 |
| Network Architects | 15-1241.00 |
| Cloud Architects | 15-1299.09 |
