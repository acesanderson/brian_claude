# Course Inventory Schema Reference

Source file: `/Users/bianders/.claude/skills/courselist_all (1).xlsx`
49,887 rows x 64 columns (all locales). en_US active = ~10,700 rows.

## Key Columns

### Identity
| Column | Type | Notes |
|--------|------|-------|
| `Course ID` | int | Unique per row |
| `Course Name` | str | Localized title |
| `Course Name EN` | str | English title (null for some non-EN rows) |
| `LIL URL` | str | Full LinkedIn Learning URL |
| `Locale` | str | e.g. `en_US`, `de_DE`, `fr_FR` |
| `Original Course ID` | float | For translated/adapted: points to source |
| `Equivalent English Course` | float | Maps non-EN course to its EN counterpart |

### Status & Visibility
| Column | Values |
|--------|--------|
| `Activation Status` | ACTIVE, ARCHIVED, CANCELLED, RETIRED, PENDING |
| `Display to Public` | Yes / No |
| `Display to QA` | Yes / No |
| `Localization Type` | ORIGINAL, TRANSLATED, ADAPTED |

### Taxonomy
| Column | Values |
|--------|--------|
| `Internal Library` | Business, Technology, Creative |
| `Internal Subject` | ~40 values — top: Business Software and Applications, Graphic Design, Human Skills, Leadership and Management, Programming Languages, Artificial Intelligence, Marketing, Certification Prep, Data Science, Web Development, Cloud Computing, Networking and System Administration |
| `Framework Topic` | Sparse; more granular than Subject |
| `Framework Subject` | Very sparse (43k nulls) |
| `Content Type` | TOOLS, SKILLS, INSPIRATION |
| `LI Level` | Beginner, Intermediate, Advanced, General, Beginner + Intermediate |
| `Manager Level` | General, Individual Contributor, Manager, Senior Manager, C-Suite |
| `Skills` | Comma-separated skill tags (localized) |
| `Skills EN` | Comma-separated skill tags (English) — use this for analysis |

### Instructor
| Column | Notes |
|--------|-------|
| `Instructor ID` | May be multi-value (comma-separated) for co-instructors |
| `Instructor Name` | May be multi-value for co-instructors |
| `Author Payment Category` | Internal payment tier |
| `Contract Type` | PERPETUAL, STANDARD, LICENSED, STAFF_INSTRUCTOR, EMPLOYEE, NO_CONTRACT |

### Dates
| Column | Notes |
|--------|-------|
| `Course Release Date` | Original publish date |
| `Course Updated Date` | Last content update |
| `Course Archive Date` | When archived (if applicable) |
| `Course Retire Date` | When retired (if applicable) |
| `Series End Date` | For serial courses |

### Content Metrics
| Column | Notes |
|--------|-------|
| `Visible Duration` | **Seconds** (median active en_US course ≈ 3,790s ≈ 63 min) |
| `Visible Video Count` | Number of video segments |
| `Has Assessment` | Yes / No |
| `Has Challenge/Solution` | Yes / No |
| `Has CEU` | Yes / No (4,839 rows = Yes) |
| `Has Exercise Files` | Yes / No |
| `Media Type` | Video, Audio, Interactive, Text (or combinations) |
| `Delivery Mode` | ALL_AT_ONCE (most), SERIAL |

### Special Flags
| Column | Notes |
|--------|-------|
| `Free Course` | Almost entirely null |
| `Certification Library` | "Certifications" when present (~8,336 rows) |
| `Gen AI Feature Flag` | "Has Prompted Course Summary" or "Disable coach" |
| `Hands-On Practice` | Yes / No |
| `Unlocked for Viva Learning` | Yes / No |
| `Github Codespace` | Yes / No |

## Locale Distribution (top)
| Locale | Count |
|--------|-------|
| en_US | 26,787 |
| de_DE | 6,139 |
| es_ES | 4,793 |
| fr_FR | 4,486 |
| ja_JP | 2,129 |
| pt_BR | 1,451 |
| zh_CN | 871 |
| pl_PL | 634 |

## Activation Status Distribution
| Status | Count |
|--------|-------|
| ACTIVE | 25,284 |
| ARCHIVED | 12,323 |
| CANCELLED | 5,128 |
| RETIRED | 4,435 |
| PENDING | 2,717 |

## Data Quirks
- `Instructor Name` / `Instructor ID` can be comma-separated for co-instructors — split before grouping
- `Skills EN` is comma-separated — use `skills_explode()` from `load.py` for per-skill analysis
- `Visible Duration` is in **seconds**, not minutes
- `Contract Type` can be multi-value (comma-separated), e.g. `"LICENSED, STANDARD"`
- Translated/adapted courses share `Original Course ID` with the source English course
- `LI Level` values appear in English and translated forms (same column) — filter `Locale == "en_US"` or use English value strings
