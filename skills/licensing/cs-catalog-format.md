# CS-Approval Catalog Format

When generating a Google Sheet for CS review, use this exact structure.

## Tab 1 — "Tier Definitions"

| Tier | What it means | Typical signals |
|---|---|---|
| T1 | Review first — highest structural fit | Foundational/overview courses; proven LiL demand topics; priority domains (AI/ML, cybersecurity, cloud, leadership, finance) |
| T2 | Review second — complementary fit | Clear coverage gaps; niche-but-relevant; no LiL equivalent |
| T3 | Review if bandwidth — licensable long tail | Viable but specialized; CS decides |
| T4 (SKIP) | Structurally ineligible — do not review | Exam prep, retake exams, product tool training (platform-locked), locale duplicates, youth/teen programs |

This tier taxonomy is structural only — it signals review order based on observable criteria. It does not predict CS decisions or reflect editorial quality judgments.

## Tab 2 — "Course catalog"

Columns (in order):

| Column | Header | Notes |
|---|---|---|
| A | `tier (descriptions in first tab)` | T1 / T2 / T3 / T4 (SKIP) |
| B | `title` | Cleaned title — see series handling below |
| C | `description` | From catalog; for series parts, append "Part N of the [Series Name]." sentence |
| D | `level` | Strict enum: `Beginner` \| `Intermediate` \| `Advanced` |
| E | `duration` | Prefix with `~` — all values are estimates (e.g., `~30 min`, `~1 hour`) |
| F+ | partner-specific | e.g., `price`, `url`, `date_scraped` |
| last-1 | `license? (x)` | CS marks with x |
| last | `CS notes` | CS freeform |

Sort order: T1 → T2 → T3 → T4 (SKIP). The "T4 (SKIP)" label sorts correctly after T3 lexicographically.

## Level Enum Mapping

Normalize raw partner values before writing:
- "Introductory", "Beginner", "Foundational", "101", "Basic" → `Beginner`
- "Professional", "Intermediate", "Practitioner", "200-level" → `Intermediate`
- "Advanced", "Expert", "300-level" → `Advanced`

## Series Handling

When course titles follow the pattern `"Topic -- Series Name (Part N)"`:
- Strip the ` -- Series Name (Part N)` from the title — keep only the topic name
- Append `"Part N of the Series Name."` as a sentence at the end of the description

## Deduplication Rules

- **Online vs. non-online:** normalize title by stripping `" - Online"` / `": Online"` suffix (case-insensitive). Keep the online variant when both exist; drop the offline duplicate.
- **Locale variants** (`--- EN-AU`, `--- EN-CA`, `--- EN-GB`, `--- ZH-SG`, `--- DE-DE`, etc.): drop all locale variants. If no base English version exists for a locale variant, include it but flag in CS notes.
- **Professional certificate bundles:** manually verify that courses listed individually are not also counted as part of a bundle row. Do not double-count content.

## Duration Sources (in priority order)

1. CPE credits in description field (`CPE Credits: N` → `~N hours`)
2. Scraped from course page (look for clock icon pattern in HTML)
3. Median placeholder for the partner's catalog (label clearly, e.g., `~30 min`)
