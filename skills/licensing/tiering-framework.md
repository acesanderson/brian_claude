# Course Tiering Framework

After a catalog is scraped, assign every course a tier before sending to partners or CS. This
replaced the old gap-first approach (avoid overlap with LiL library). The new approach: include
everything, let CS decide on overlap. Tier is a signal of expected impact, not a pass/fail gate.

| Tier | Definition | Typical signals |
|---|---|---|
| **T1** | Super foundational — highest guaranteed ALs | Intro/overview courses; CS priority domains (risk mgmt, cybersecurity, cloud, leadership); topics with proven LiL demand |
| **T2** | Complementary — not in library, compelling | Critical coverage gaps; niche-but-relevant topics; courses with no LiL equivalent |
| **T3** | Licensable long tail | Viable but more specialized; CS decides whether to include |
| **T4 (SKIP)** | Clearly not wanted | Exam prep, youth/teen programs, retake exams, product tool training, EN-AU locale duplicates, generic soft skills with no construction/domain anchor |

## Workflow

Assign tiers in `catalog.json` (add a `"tier"` key per course), write a tiered
Google Sheet sorted T1 → T2 → T3 → T4 (SKIP), register in `google_docs.json`, append to catalog
index. Update partner `notes.md` and `pipeline.md` with sheet URL and tier counts.

## What to Share

**When sending to partners:** Share T1+T2 as the proposed licensing scope. T3 is available but
not leading with it. T4 (SKIP) rows stay off partner-facing docs.

**When sending to CS for Gate A:** Share full tiered sheet (T1–T3). Overlap with existing LiL
library is not a disqualifier — CS makes that call.
