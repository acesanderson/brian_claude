# JSON Schema Reference

## Complete Output Schema

```json
{
  "partner": "string — Provider name",
  "base_url": "string — Starting URL",
  "crawl_date": "string — ISO date (YYYY-MM-DD)",
  "total_courses": "integer — Including cross-listings",
  "unique_courses": "integer — Deduplicated count",
  
  "crawl_metadata": {
    "structure_detected": "string — e.g., 'navigation + embedded_json'",
    "data_source": "string — hidden_input_json | ld_json | api | html",
    "categories_found": ["array of category names"],
    "learning_paths_found": ["array of path names"],
    "pages_crawled": "integer",
    "headless_browser_required": "boolean",
    "crawl_duration_seconds": "integer",
    "obstacles_encountered": ["array of obstacle types"],
    "notes": "string — Implementation details"
  },
  
  "available_resources": {
    "transcripts": {"available": "boolean", "notes": "string|null"},
    "video_downloads": {"available": "boolean", "notes": "string|null"},
    "table_of_contents": {"available": "boolean", "notes": "string|null"},
    "slide_decks": {"available": "boolean", "notes": "string|null"},
    "exercise_files": {"available": "boolean", "notes": "string|null"},
    "quizzes_assessments": {"available": "boolean", "notes": "string|null"},
    "api_access": {"available": "boolean", "notes": "string|null"},
    "bulk_catalog": {"available": "boolean", "notes": "string|null"}
  },
  
  "courses": [
    {
      "title": "string — Course title (required)",
      "url": "string — Direct link (required)",
      "type": "string — On-Demand Course, Virtual Training, etc. (required)",
      "gated": "boolean — Behind auth wall",
      "gating_type": "string|null — email, login, paywall, sso",
      "topic": "string|null — Category/subject",
      "learning_path": "string|null — Parent collection",
      "duration": "integer|null — Minutes (normalized)",
      "duration_raw": "string|null — Original string",
      "format": "string|null — video, multimedia, interactive",
      "level": "string|null — Beginner, Intermediate, Advanced",
      "description": "string|null",
      "instructor": "string|null",
      "free": "boolean",
      "pricing": "object|null — {member: '$X', non_member: '$Y'}",
      "cert_included": "boolean",
      "extra_metadata": {
        "cross_listed_in": ["array of other paths"],
        "prerequisites": "string|null",
        "skills_covered": ["array"],
        "release_date": "string|null",
        "last_updated": "string|null",
        "enrollment_count": "integer|null",
        "rating": "number|null",
        "chapters": ["array of chapter titles"],
        "ce_credits": "string|null",
        "target_audience": "string|null"
      }
    }
  ],
  
  "summary": {
    "total_courses": "integer",
    "unique_courses": "integer",
    "cross_listed_courses": "integer",
    "completeness_score": "float — 0.0 to 1.0",
    "topics": {"topic_name": "count"},
    "learning_paths": {"path_name": "count"},
    "types": {"type_name": "count"},
    "duration_range_minutes": [min, max],
    "total_content_hours": "float",
    "levels": {"Beginner": 0, "Intermediate": 0, "Advanced": 0, "unknown": 0},
    "pricing": {"free": 0, "paid": 0},
    "gating": {"gated": 0, "ungated": 0},
    "fields_coverage": {
      "title": "count",
      "url": "count",
      "type": "count",
      "topic": "count",
      "duration": "count",
      "level": "count",
      "description": "count",
      "instructor": "count"
    }
  },
  
  "licensing_assessment": {
    "volume_score": "string — high, medium, low, insufficient",
    "volume_notes": "string",
    "format_fit": "string — likely, possible, unlikely, unknown",
    "format_notes": "string",
    "brand_topic_fit": "string — strong, moderate, weak, unclear",
    "brand_notes": "string",
    "potential_blockers": ["array of concerns"],
    "recommended_next_step": "string"
  }
}
```

## Resource Detection Methods

| Resource | Look For |
|----------|----------|
| transcripts | Transcript toggle, .vtt/.srt references |
| video_downloads | Direct .mp4 links, download buttons |
| slide_decks | .pdf, .pptx download links |
| table_of_contents | Expandable module/chapter lists |
| exercise_files | .zip, GitHub links |
| quizzes_assessments | Quiz modules, graded components |
| api_access | /api/ routes, GraphQL endpoints |
| bulk_catalog | Sitemap, RSS feed, catalog export |

## Completeness Score Calculation

```python
completeness_score = populated_fields / (total_courses * num_tracked_fields)
```

Tracked fields: title, url, type, topic, duration, level, description, instructor
