# Find Partner Contacts

Technique for identifying cold outreach targets at external partner companies.
Validated against CrowdStrike (2026-03-03). Produces name + title sufficient for
cold outreach (LinkedIn profile lookup or email reverse-engineering).

---

## Role Hierarchy

Work top-down. Stop at the first tier that yields a confirmed lead.

| Tier | Roles to target | Notes |
|---|---|---|
| **P0** | Director/VP/Head of Training, Director of Education, Head of Education Services | Owns the external training program |
| **P0** | Any title containing the company's academy name (e.g., "CrowdStrike University") | Signals direct ownership of the program |
| **P1** | Customer Education, Customer Enablement, Technical Education, Education Services | Customer-facing learning roles |
| **P1** | Customer Success with training/enablement in title | CS owns training at some orgs |
| **P2** | Partnerships, BD, Marketing | Low-yield fallback only |
| **Discard** | L&D, HR, Talent Development, People Ops | Internal-facing — wrong audience |
| **Discard** | C-suite, Corporate Strategy, Product, Engineering | Too senior / wrong function |

---

## Source Hierarchy

### What works (search snippets — do NOT fetch profile pages)

**1. ZoomInfo — highest yield for title-first discovery**
```
site:zoominfo.com [company] "director" OR "VP" OR "head" "training" OR "education" OR "university"
site:zoominfo.com [company] "training" OR "education" OR "university" director OR manager OR lead
```
Snippets include name + title. Do not fetch the ZoomInfo profile page (403).

**2. RocketReach — confirms and adds names**
```
site:rocketreach.co [company] "training" OR "education" OR "enablement" director OR manager OR VP
```
Snippets include name + title + location. Do not fetch profile pages (403).

**3. Cross-reference any promising name**
Once a name surfaces, run: `"[First Last]" "[Company]"` across all sources.
Non-gated confirmations: Adapt.io, theorg.com, personal bios, company blog author pages, conference speaker pages.

**4. LinkedIn (name surface only — not title discovery)**
```
site:linkedin.com/in "[company]" "training" OR "education" OR "university"
```
Snippets rarely include current title. Use only to surface names for cross-referencing, not for title confirmation.

**5. Perplexity (sonar-pro)**
```
ask --raw --model sonar-pro "Who leads [program name] / customer training at [Company]? ..."
```
Useful for well-known programs. Often returns no named individuals. Run in parallel, treat as bonus.

### What doesn't work (do not attempt fetches)

| Source | Failure mode |
|---|---|
| `linkedin.com/in/*` profile fetch | 429 Request Denied |
| `zoominfo.com/p/*` profile fetch | 403 Forbidden |
| `rocketreach.co/*` profile fetch | 403 Forbidden |
| `craft.co/*/executives` | 403 Forbidden |
| `comparably.com/*` | 403 / process kill |
| `theorg.com/org/*/teams` | Returns nearly empty page |

---

## Workflow

```
1. Run ZoomInfo + RocketReach searches in parallel (title-first)
2. Collect names + titles from snippets
3. Cross-reference each promising name: "[Name]" "[Company]"
4. Discard by role hierarchy (L&D, HR, Corp Strategy, C-suite)
5. Rank survivors by tier
6. Record confirmed leads in partners/<slug>/notes.md
```

---

## Output format (for partners/<slug>/notes.md)

```markdown
## Outreach Targets

| Name | Title | Tier | Source | Notes |
|---|---|---|---|---|
| Amy Hughey | Director of Training | P0 | ZoomInfo, RocketReach, Adapt.io | Austin TX. Previously at [prior company]. |
| Audrie Murphy | Training & Enablement PM, Customer Success | P1 | RocketReach | CA-based. Execution-level but owns customer enablement. |
```

---

## Notes

- Former employees (e.g., "Former CMO") appear in searches — always check "currently at [company]" context.
- Multiple people named the same name on LinkedIn are common — cross-reference location/background to confirm identity.
- If ZoomInfo/RocketReach yield nothing, try the company's own blog author pages (`[company].com/blog/author/`) — training leaders sometimes publish.
- Conference speaker pages (RSA, Black Hat, company user conferences) sometimes name training org leads.
