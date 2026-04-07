## Introduction
**Vector Research** is a diagnostic framework designed for **Systemic Gap Analysis**. Unlike standard keyword search, which retrieves explicit facts, Vector Research identifies the **"Negative Space"** in a target domain—the discrepancies between what a system *claims* to be doing and what its *activity* proves.

### Use Case: When to Use
* **Organizational Navigation:** Mapping a team's unstated needs or technical debt before a lateral move or pitch.
* **Strategic Intelligence:** Identifying the "hidden roadmap" of a competitor or open-source project.
* **Due Diligence:** Verifying the maturity of a technical stack by contrasting "Marketing Intent" with "Engineering Reality."

### When NOT to Use
* **Fact Retrieval:** Do not use for simple "Who/What/When" questions where the answer is a single, static datum.
* **Subjective Analysis:** Do not use for aesthetic, moral, or purely qualitative evaluations.
* **Low-Signal Environments:** Do not use if the target lacks a digital "exhaust trail" (e.g., zero public activity or logs).

### Governance
**STRICT RULE:** This skill is **OPT-IN ONLY**. The agent must not trigger the Vector Research Loop unless explicitly invoked by the user (e.g., via `/vector` or "Perform a vector research spec").

---

## 1. Functional Primitives (Capabilities)
* **`IDENTIFY`**: Establish the boundaries of the target namespace and inventory the "Sensor Array" (Glean, Jira, Playwright, Perplexity etc.).
* **`PROBE`**: Execute high-entropy "tracing shots" to find the **Center of Gravity** (dependencies) and **Heat** (friction).
* **`TRIANGULATE`**: Contrast multiple data types (e.g., *Roadmaps* vs. *Recent Commits*) to find the **Delta ($\Delta$)**.
* **`ASSERT`**: Validate if a finding meets the **Minimum Viable Intel (MVI)** threshold.

## 2. Operational Logic (The "Vector" Loop)

### Phase 1: Environmental Initialization (`INIT`)
1.  **Inventory Sensors**: Catalog all accessible data sources.
2.  **Baseline Intent**: Identify the stated primary mission/objectives of the namespace.
3.  **Establish Consensus**: Document the "official" version of the target's current state.

### Phase 2: High-Aperture Reconnaissance (`RED`)
Execute three orthogonal probes:
* **The Gravity Shot**: "Which node/project is the most critical dependency for the rest of the system?"
* **The Friction Shot**: "Where is the highest density of 'stalled,' 'blocked,' or 'reverted' activity?"
* **The Silence Shot**: "What stated goal from the Roadmap has zero footprint in recent activity logs?"

### Phase 3: Convergence & Validation (`GREEN`)
1.  **Cross-Verify**: A "Gap" must be visible across at least two independent sensors (e.g., Jira AND a Slack thread).
2.  **Diagnose Constraint**: Determine if the gap is caused by **Capacity** (labor), **Capability** (skill), or **Infrastructure** (tooling).

## 3. Acceptance Criteria (Definition of Done)
The research is complete only when the agent delivers the **MVI Payload**:
1.  **The Anchor**: One verified high-priority project.
2.  **The Friction**: The specific bottleneck preventing its progress.
3.  **The Wedge**: A clear justification for why a specific intervention (e.g., your specific skill set) resolves that friction.

## 4. Constraints & Guardrails
* **Minimalism**: Avoid summaries. Only report **Deltas**.
* **Recency Bias**: Weight activity from the last 30 days more heavily than documentation older than 6 months.
* **Logic over Sentiment**: Prioritize structural friction (broken builds, stale PRs) over interpersonal complaints.
