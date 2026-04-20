---
name: hamel
description: >
  Consult Hamel Husain's AI on delphi.ai/hamel as a live reference when working on LLM evals,
  eval design, LLM judges, rubrics, test sets, or any evaluation-related task.
  Invoke this skill whenever the user is designing, building, or debugging an eval pipeline,
  asking about eval methodology, or wants expert input on what "good" looks like for LLM outputs.
  Also invoke when the user explicitly says "ask Hamel" or "check with Hamel".
---

## What this is

Hamel Husain's Delphi AI is a teaching assistant trained on ~2k curated Q&A pairs from his
"AI Evals For Engineers & PMs" course, lesson transcripts, and his public writing on evals.
It gives high-quality, opinionated answers on eval methodology — treat it as a senior consultant
you can query mid-task.

## Connection setup

Hamel's Delphi runs through a Chrome instance with remote debugging enabled on port 9222.
The Playwright MCP connects to this Chrome session.

**Verify Chrome is running:**
```bash
lsof -i :9222
```

If nothing is listening, the user needs to launch Chrome with:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug
```
Then navigate to https://www.delphi.ai/hamel and log in before proceeding.

## How to ask Hamel a question

Use the Playwright MCP tools in this sequence:

1. **Check current page** — take a snapshot to see where Chrome is:
   ```
   mcp__plugin_playwright_playwright__browser_snapshot
   ```

2. **Navigate if needed** — if not already on delphi.ai/hamel:
   ```
   mcp__plugin_playwright_playwright__browser_navigate  url=https://www.delphi.ai/hamel
   ```

3. **Click the chat input** — find the textbox ref from the snapshot and click it:
   ```
   mcp__plugin_playwright_playwright__browser_click  ref=<textbox-ref>
   ```

4. **Type and submit the question:**
   ```
   mcp__plugin_playwright_playwright__browser_type
     ref=<textbox-ref>
     text="Your question here"
     submit=true
   ```

5. **Wait briefly, then snapshot** to capture the response. The answer appears as paragraph
   elements after the question node. If the snapshot is very large (>50KB), save it to a file
   and grep for the relevant paragraphs rather than loading it all into context.

6. **Read the response** from the snapshot — look for `paragraph` nodes that follow the
   user message element.

## What Hamel knows well

- When and how to use LLM-as-judge
- Designing rubrics and binary pass/fail criteria
- Building a trustworthy ground-truth label set
- The role of domain experts in eval design
- Automating vs. human-in-the-loop evals
- Prompt versioning and eval iteration
- Common failure modes in eval pipelines
- When "ready-to-use" eval metrics are and aren't appropriate

## How to frame questions

Don't ask high-level or trend-seeking questions ("what's the best eval framework these days?").
The bot's knowledge is bounded and may not reflect the current state of AI engineering.

Instead, treat every query as a **scoped consultation**: give Hamel's AI the full context of
what you're building, then ask a precise question about the eval challenge you're facing.

Good pattern:
1. Describe the task the LLM is performing (inputs, outputs, what "good" looks like)
2. Describe the specific eval problem (e.g., "I can't tell if my judge is too lenient", "I don't know what dimension to score", "labels are inconsistent across annotators")
3. Ask a targeted question rooted in that context

The more grounded and specific the prompt, the more useful the answer. Vague questions get
generic answers; scoped questions get actionable ones.

## Workflow tip

Query Hamel *before* committing to an eval design, not after. His strongest value is in
clarifying what the right thing to measure is — which saves re-work downstream.
