# Inbound Partner Vetting

Triggers: "they reached out", "submitted the form", "inbound from", "is this legit",
"how real is", "vet this org".

Run when an inbound lead arrives from an organization that is NOT a well-known brand.
Governance is the primary signal.

## Research

Use `conduit batch -m sonar-pro` to ask these 5 questions in parallel:

1. **Named leadership**: "Who founded [org] and who are the key executives? Are their
   names, LinkedIn profiles, and prior career histories publicly verifiable?"

2. **Board and affiliations**: "Does [org] have a named advisory board or notable outside
   affiliates? Are these individuals independently verifiable with real public profiles?"

3. **Accreditation**: "Is [org] accredited by any recognized external standards body
   (ANSI/ISO 17024, IACET, or similar)? Or are their credentials self-issued?"

4. **Employer recognition**: "Do major employers, job postings, or enterprise L&D programs
   recognize or require [org] certifications/credentials? Are they listed on LinkedIn
   profiles at scale?"

5. **Independent community signal**: "What do independent reviews on Reddit, Trustpilot,
   or professional forums say about [org]? Are there real practitioners discussing them?"

## Screening hierarchy

- **Named CEO/founder with verifiable prior career** → proceed to research
- **Named board with outside affiliates you can independently verify** → meaningful positive signal
- **Elaborate governance language, no named individuals** → flag; require video call with
  multiple team members before investing further
- **Anonymous leadership + negative forum signal** → dead stop; surface to Brian immediately

After running: present a verdict (real / thin but real / red flag), note the strongest
positive and negative signals, and recommend next action. Do NOT add to pipeline or
invest further research until vetting is complete if red flags are present.

## Output

Write findings to `partners/<slug>/notes.md` under a `## Credibility` section
(create if absent; skip for established brands where vetting wasn't run):

```markdown
## Credibility

**Verdict:** real | thin but real | red flag
**Date checked:** YYYY-MM-DD

**Strongest positive signals:**
- [e.g., Named CEO Russell Sarder with verifiable prior company (NetCom Learning)]
- [e.g., Advisory board includes Sunil Prashara, former PMI CEO]

**Strongest negative signals:**
- [e.g., No external accreditation — ISO 17024 "alignment" only]
- [e.g., No employer recognition in job postings or L&D programs]

**Recommended next action:** [e.g., Proceed with outreach / Require video call / Dead stop]
```

Presence of this section = vetting was done. Absence = established brand, no check needed.

Append to `manifest.md`: `- YYYY-MM-DD | vetted | partners/<slug>/notes.md | verdict: <verdict>`
