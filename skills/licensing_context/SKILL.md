---
name: licensing-context
type: context
description: Provides context about LinkedIn Learning's content licensing model, which is Brian's dedicated workstream. This provides organizational, strategic, historical, and industry context for Brian's job.
---

# Content Licensing: Context Artifact

**Last Updated:** February 5, 2026 **Owner:** Brian Anderson, Senior Content Manager, LinkedIn Learning Solutions

---

## 1. LinkedIn Business Context

### Corporate Structure & Strategic Shift

LinkedIn (a Microsoft subsidiary) has consolidated **LinkedIn Learning** and **Editorial** under VP **Dan Roth**. This restructure signals a pivot in how content value is defined:

- **Strategic Mandate**: In the AI era, the company's competitive moat is the **Network** (1B+ members).
- **North Star Metric**: Grow Daily Active Users (DAU) from **80M to 200M** (~18-month target).
- **Role of Content**: Content is prioritized primarily to drive DAU and time-on-platform.

### The State of LinkedIn Learning (FY26)

**Status**: "Legacy Business"

- **Investment**: Product/engineering funding is significantly reduced, focused on compliance and maintenance for the Enterprise business.
- **Production Pivot**: Moving from a "Studio Production House" (Lynda.com legacy) to a **Platform Aggregator**.
- **Old Model**: 100% Organic, owned IP, high-cost studio production.
- **New Model**: **80% Licensed / 20% Organic** target (2-year horizon).
- **Implication**: Studios have slowed; production teams are consolidating to serve broader Editorial needs (podcasts, executive interviews).

### Competitive Landscape: Coursera

- **Revenue Mix**: $122.8M Consumer revenue (66% of total), driven by "Coursera Plus."
- **Payout Model**: Shifted to engagement-based creator compensation (similar to Spotify model).
- **Cash Position**: Strong balance sheet ($775M cash, no debt).
- **Strategic Irony**: While LinkedIn pivots _to_ licensing, Coursera is investing $17M in _organic_ content production to secure IP ownership and agility.

---

## 2. Primary Initiative: Content Licensing

### Strategy: The "80/20" Flip

**Goal**: Aggressively scale the library by ingesting third-party content to replace organic production.

- **Current State**: ~4,000 Licensed courses vs. ~19,500 Organic.
- **Target State**: Flip composition to 80% Licensed within 2 years.

### Target "Genre" & Partners

- **Scope**: "All of the Above"—Publishers, Universities, and individual Influencers.
- **Format Constraint**:
    - **Video**: Primary target. Easy ingestion.
    - **Multimedia**: Supported but manual. Must be **sequential** (Video Node → Text Node).
    - **Excluded**: SCORM, interactive labs (too engineering-heavy), "ungraded plugins."

### Partner Taxonomy

|Category|Definition|Strategic Value|
|---|---|---|
|**Tier One Brands**|Brands that provide value across the LinkedIn ecosystem|Credibility + reach across LinkedIn ecosystem|
|**Industry Brands**|Brands well-known within a specific industry with products outside of training|Industry credibility and curriculum depth for learning library|
|**Publishers/Aggregators**|Content companies whose core business is producing/distributing educational material|Catalog volume and gap-filling at scale|
|**Universities/Research**|Academic institutions with research credibility and formal credential authority|Academic prestige, compliance appeal, credential weight (theoretical at this time)|
|**Individual Influencers**|Subject matter experts with personal audience/following|DAU/engagement alignment, consumer thesis fit, speed to ingest|

### Commercial Models

**The Standard Deal**:

- **Structure**: Revenue Share (Royalty).
    
    - _Formula_: Revenue × Usage Rate (Active Subs) × View Share × Royalty Rate.
    - _Terms_: Standard **15%** (Non-exclusive) or **20%** (Exclusive).
- Alternative comp: advances against royalties are possible; as are direct grants.
    
- **The "Exposure" Pitch**: For Tier 1 corporates (Google, Adobe), royalties are often **0%**.
    
    - _Value Prop_: Distribution to 30M+ enterprise learners and 1B+ members.
    - _Objection Handling_: Partner splits content into "Premium" (monetized on own site) vs. "Thought Leadership" (brand reach on LinkedIn).

### Operational Constraints

- **Ingestion**: **Manual**. BD hands off files to Production.
- **Updates**: Static snapshots. If a partner updates their course, it requires a manual re-ingest.
- **Tools**: **Cosmo** (Content Management's Production database) and **Tableau** (Reporting).

---

## 3. Tangible Opportunity Heuristic

A licensing opportunity is **tangible** when it passes all three gates:

### Gate 1: ADDRESSABLE (Content exists and is ingestible)

**Format Fit:**

|Criterion|Pass|Fail|
|---|---|---|
|Format|Standalone video or sequential multimedia|SCORM, interactive labs, platform-dependent elements|
|Length|30min–2hr per course, chunkable to 5–15min segments|Outside range or monolithic|
|Volume|5+ courses|<5 (unless exceptional)|
|Production|Comparable to LiL organic|Webinar recording, AI voice/avatar|
|Tone|Learner-focused, objective|Sales-y, product-marketing, steers to partner tool without candor|
|Brand-topic fit|Topic resonant with partner's recognized expertise|Glaringly incongruent (e.g., Palantir on data ethics, Meta on responsible AI, Oracle on DEI)|
|Availability|Finished, not freely online (email-gate OK, YouTube only if exceptional)|Requires co-dev, freely on YouTube|
|Language|English|Other|
|Credential|Not a cert program (unless partner prioritizes reach over validation)|Cert program with validation focus|

**Pete's Partner Qualification Checklist:**

- We strongly prefer licensing deals for 5+ courses
- We don't license content that's freely available online (exceptions: if it is email-gated on partner platform, that's less of a concern; if it's on YouTube, the content needs to be exceptionally compelling to compensate for this)
- We only license content that matches the quality of the courses we create ourselves (in terms of instructional design and production quality)
- We don't license any content that's aggressively (or even mildly) "sales-y" or comes across as content marketing. The focus has to be on the learner.
- One reason we often find that branded courses (i.e. produced by the platform owner or software manufacturer) aren't a good match for licensing: the courses aren't objective enough (e.g. trying to steer the learner to the brand's tool, providing candid advice about where a tool isn't the best option, etc.)
- Topics covered should be consistent with a brand's recognized marketplace expertise
- We only consider for licensing finished, ready-to-license videos. That is, if the courses haven't yet been created we won't advise on the creation of them.
- For a course to be compatible with LiL it needs to be:
    - standalone video (i.e. nothing that requires interaction with an instructor) or multimedia (text/images/urls)
    - somewhere between 30 minutes and 2 hours long
    - either currently split up into individual segments that are ~5-15 minutes long, or capable of being chunked up into these smaller sections
    - free from any kind of aggressive cross-marketing or CTA-style promotions (licensor branding in the form of watermarks or title card/outro slides is fine)

### Gate 2: ALIGNED (Partner has a reason to say yes)

|Lever|Description|Typical Partner Type|
|---|---|---|
|**Exposure**|Distribution to 30M+ enterprise learners, 1B+ members; often 0% royalty|Tier 1 brands, Industry brands with marketing motivation|
|**Revenue**|15% non-exclusive / 20% exclusive royalty; advances or grants possible|Publishers, smaller orgs, individual influencers|
|**Awareness/Sales Enablement**|LiL as top-of-funnel for partner's own learning platform (e.g., Cybrary licenses security courses seeing enterprise audience as sales enablement for their platform)|Learning platforms with their own subscription business|
|**Commitment Fulfillment**|Public upskilling pledges|Tier 1 brands with stated goals (Adobe 30M by 2030, SAP 12M by 2030, Cisco 1M)|

### Gate 3: ACCEPTABLE (Library need exists)

Content Strategy (Mary Treseler's team) retains "Go/No-Go" authority on partners based on library needs. The rubric will take the form of segment-level guidance (e.g., "Segment A (devops) is moving to licensing, Segment B (human skills) will be organic").

This gate is validated through bi-weekly alignment meetings with Mary. Kim and Pete are working on getting that snapshot from Mary and her team.

---

## 4. Sourcing Methods

### Signal-Based

Industry scan for companies with public upskilling commitments, new training platforms, recent course catalog launches. Can be operationalized through LLM engineering (Perplexity, web search with Gemini/OpenAI/Anthropic, deep research with Google).

**Best for**: Tier 1 whale hunting (NVIDIA, SAP, IBM). Not a volume play.

### Gap-Based

Start from library gaps (once Mary's rubric is documented), reverse-engineer who creates content in those segments. LLM workflow that identifies partners then validates the opportunity for an arbitrary skill (Kubernetes, Negotiation, Time Management, etc.).

**Best for**: Highest strategic value, but depends on Mary's rubric stabilizing.

### Analog-Based

Look at who Coursera, Udemy, Pluralsight have licensed and ask "why not us?"

**Available data**: Scraped Coursera and Udemy catalogs with partners/instructors/courses, enrollment and review data for sorting.

**Additional source**: Prof Cert partners who have endorsed LiL content but haven't licensed to us. Low-hanging fruit.

**Best for**: Fastest path to volume. Partners have demonstrated willingness to license.

### Inbound-Opportunistic

Interest form for Prof Certs sometimes surfaces prospective licensors (e.g., SANS). Sales reps occasionally put good ideas on radar.

**Caveat**: Often noisy. Need clear expectation management—reps cannot promise anything to partners until BD validates the opportunity.

---

## 5. Partnership Portfolio & Pipeline

### Notable Existing Licensors

- **Tech**: Microsoft Press, Google Cloud, Oracle University, MongoDB, Snowflake, GitHub, Atlassian University, Unity, Docker.
- **Business/Strategy**: Boston Consulting Group (BCG), MIT Sloan Management Review, Deloitte Insights, Harvard Business Publishing (HBS) (currently in discussion)
- **Publishers**: Packt, Macmillan, HarperCollins.

### The "Hit List" (Tier 1 Targets)

_These partners are targets for **both** Licensing (Volume) and Professional Certificates (Sweetener)._

- **Active / Imminent**: **Anthropic** (Contract likely signing this week).
- **High Priority**: Google (Main), SAP, IBM, NVIDIA.

### Partner Leverage: Public Commitments

_Use these external commitments to pitch distribution/scale._

- **Adobe**: Committed to upskilling **30M people** in AI literacy by 2030.
- **SAP**: Committed to training **12M people** in AI skills by 2030.
- **Cisco**: Committed to training **1M people** in AI skills.

---

## 6. Complex Partnership Example: HBS (Boundary Case)

HBS represents a future-forward example of a complex, multi-modal partnership structure. This is an outlier, not the typical licensing play.

**Deal Structure:**

|Opportunity|Example|Responsibilities|Ownership|Distribution|
|---|---|---|---|---|
|Net new|Record LinkedIn-Learning style courses on-site/remote with HBS faculty, with ability to publish as professional certificate|HBS to make instructors available; drive design of learning materials; grant licensing rights|HBS retains IP rights|Exclusive on LinkedIn platform; in front of paywall (unlocked)|
|Current Sana.ai content|License available content|HBS to grant LI licensing rights|HBS retains IP rights|Non-exclusive LinkedIn Learning platform|
|Promotional|Thought-leadership segments recorded on-site/remote with HBS faculty|HBS to make instructors available; drive design of learning materials; grant licensing rights|User-generated content|Feed/Public through individual profiles|

**Outlier Terms:**

- $1M direct grant
- HBS retains IP for courses LiL produces
- Three SOWs for individual opportunities under master Licensing agreement

**Why it's a boundary case**: Combines licensing + net-new production + promotional content. Not replicable at scale, but demonstrates strategic flexibility for unicorn partners.

---

## 7. Governance: The "Mary" Bottleneck

**The Rule**: The Content Strategy team (led by Mary Treseler) retains "Go/No-Go" authority on partners based on library needs.

**The Workflow**:

1. **Sole Point of Contact**: Mary Treseler.
2. **No Direct Access**: BD (Brian/Kim) does _not_ work directly with individual Content Managers (CMs) anymore.
3. **Cadence**: Bi-weekly alignment meetings with Mary to agree on topics/audiences.
4. **Execution**: Once aligned, BD executes independently (contracts, ingestion) without round-by-round CM review.

---

## 8. Secondary Initiative: Professional Certificates

**Status**: **Strategic "Sweetener"** (Not a Volume Play)

- **Role**: A discretionary "upgrade" for Tier 1 licensing partners with strong brand resonance.
- **Acquisition Targets**: Met. Sufficient liquidity achieved (~90% of job titles covered).
- **Microsoft Dependency**: The **Microsoft Elevate** (formerly GSI) program drives ~50% of engagement but is owned by **Faith Brill**, not Brian/Manish.

### The Pitch: "Turn Your Content into a Credential"

We do not ask partners to build new content. We ask to **syndicate** their best existing content and wrap it in a LinkedIn assessment.

- **The Offer**: "We ingest your video courses (4–10 hours). We wrap it in a 40–60 question exam. We issue a co-branded credential to the world's largest professional network."
- **The Value**: Zero infrastructure cost for the partner; instant access to 30M+ enterprise learners.

### Current Friction

- **Enterprise Gap**: Certificates are not supported by third-party LMSs (unlike standard courses).
- **Reporting Gap**: L&D admins lack visibility/assignment tools for certificates.

---

## 9. Organizational Chart & Key Players

### Leadership (The "Split")

- **Dan Roth** (VP, Content Development & Ed)
    - **Colin Doody** (Sr. Director, BD) — **Your Boss**
        - **Brian Anderson** (Sr. BD Manager)
        - **Manish Gupta** (Sr. BD Manager)
        - **Kim Norbuta** (Sr. BD Manager) — _Licensing Lead (Tech bias)_
        - **Pete Meyers** (Principal BD Manager) — _Licensing Lead (Business bias)_
    - **Shea Hanson** (Director, Content Management)
    - **Mary Treseler** (Director, Content Management) — **The Strategy Gatekeeper**
        - _Managers of Content_ (The "MOCs") — lead teams of content managers.
        - _Content Managers (The "CMs") — No direct access for BD_

### Team Swimlanes

- **Kim & Pete**: Historic leads for Tech/Business licensing. EQ-heavy relationship with Content Strategy.
- **Brian & Manish**: "Leaning in" to drive volume. Brian brings historic licensing process expertise.
- **Cert Prep (Special Case)**: **Aishwarya Aravind**, a CM on Mary's team, owns the "Cert Prep" segment for the library. She is building this segment _entirely_ with licensed content.
- **New Hires**: Two additional headcount opening to support the volume mandate.

---

## 10. Strategic Analysis: Enterprise vs. Consumer

### The Enterprise Headwind

- **Threat**: AI is disrupting the corporate "course-based" upskilling model (real-time answers > courses).
- **Resource Freeze**: Learning is viewed as legacy; no appetite for deep product work to fix Enterprise gaps (LMS integration, Reporting).

### The Consumer / Network Thesis

- **Hypothesis**: Future value lies in the **Consumer** segment where learning behaviors drive **DAU**.
- **Implication**: Licensing targets should prioritize content that generates daily habits and conversation (News, Analysis, Trends) over purely episodic "How-To" courses.

---

## 11. Next Steps & Open Questions

1. **Volume vs. Ops**: How do we hit the 80% target with manual ingestion? (Is there an "Ingestion Squad" budget?)
2. **Resource Allocation**: Confirm the % split of time Brian/Manish should dedicate to Licensing vs. Prof Certs (Consult Colin).
3. **Governance Test**: Monitor the "Mary as Sole POC" model for bottlenecks as volume increases.
4. **Sourcing Operationalization**: Build workflows for analog-based sourcing (Coursera/Udemy scrape analysis, Prof Cert partner mining) as fastest path to volume.
5. **Gap-Based Dependency**: Wait for Mary's segment-level rubric to stabilize before investing heavily in gap-based sourcing.
