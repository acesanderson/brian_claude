# Skill Auditor — Design Spec

## Problem

Skills that wrap CLI scripts or external tools have a test surface that the existing skill-creator eval framework doesn't reach. Happy-path evals confirm that Claude follows the golden path when everything works. They say nothing about what happens when a script hangs, a subprocess exits 0 with empty output, an API key is missing, or the agent enters a retry loop on a failing call.

This spec defines a skill-auditor capability that covers that surface: identifying which skills have accrued friction (through git history and static analysis), and providing a framework for testing failure modes — not just success paths.

---

## Two Distinct Problems

The auditor has to hold two problems separate because they need different solutions:

**Problem A — Skill health surveillance**
Which skills in the library are accumulating friction? Which have been edited most, fixed most, and still have structural quality issues? This is a *periodic* question, answered by the `audit.py` script.

**Problem B — Failure mode coverage**
For a given skill, have we tested how Claude responds when the script fails? This is a *per-skill* question, answered by a failure fixture system layered on top of the existing skill-creator eval framework.

---

## Part I: Health Surveillance

### Signals

The `audit.py` script currently combines two signal classes:

**Git churn signals**
- `commit_count` — total commits touching the skill (deduplicated per commit, not per file)
- `friction_commits` — commits whose messages contain troubleshooting/fix keywords
- `last_changed` — freshness indicator

**Static analysis signals**
- SKILL.md line count >500 (progressive disclosure threshold from skill-creator)
- CLI flags documented >10 (cognitive load; prune unused)
- Bare `python script.py` instead of `uv run` (portability assumption)
- Missing prerequisites/env-var section (silent setup failure on new machines)
- Description word count <15 (under-triggers in practice)
- Scripts missing `# /// script` inline metadata (breaks `uv run --with` pattern)
- *Proposed addition:* Scripts with no pre-flight dependency check function (see below)
- *Proposed addition:* Scripts that don't return structured JSON (raw text output is a testability anti-pattern; see Part II)

### Friction Score

Weighted sum of signals. Current weights:
- friction commit: ×4
- raw commit count (capped at 10): ×1
- over 500 lines: +3
- bare python: +3
- scripts missing metadata: ×2 per script
- no prerequisites: +1
- trigger vague: +2
- flag heavy: +2

These weights are provisional. After accumulating more data across the skill library, calibrate against known-problematic skills.

### Pre-flight Check Pattern (new signal)

Scripts at the top of their execution should verify their own prerequisites before doing real work. A pre-flight check looks like:

```python
def preflight():
    missing = []
    for cmd in ["aws", "jq"]:
        if not shutil.which(cmd):
            missing.append(cmd)
    for var in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]:
        if not os.environ.get(var):
            missing.append(f"${var}")
    if missing:
        print(json.dumps({"status": "error", "type": "PreflightError",
                          "message": f"Missing: {', '.join(missing)}",
                          "recovery": "Install missing binaries and set required env vars"}),
              file=sys.stderr)
        sys.exit(1)
```

The auditor should flag scripts that make external calls (subprocess, requests, urllib) but have no pre-flight check. Detectable via AST analysis of imports and top-level function calls.

### Cadence

Run weekly as part of a maintenance habit. The `--since` flag enables filtering to "what changed in the last 30 days" so the report stays focused on recent drift rather than historical debt.

---

## Part II: Failure Mode Testing

### The Core Insight

Testing failure modes for skills has two distinct goals with different test mechanics:

1. **Script robustness** — does the script produce a clean, structured error signal when things go wrong?
2. **Skill robustness** — does Claude, given that error signal, respond correctly?

For skill testing, goal 2 matters more. And critically: you don't need the failure to *actually happen* to test Claude's response. You just need Claude to receive the failure signal. This means fixture injection — manufacturing the output of a failure — is cleaner and more tractable than environment manipulation.

### Failure Mode Taxonomy

All meaningful failure modes for script-based skills fall into five categories:

**1. Environment failures** — script can't start or can't reach a dependency
- Missing binary (not in PATH)
- Missing required env var
- Wrong credentials (token for wrong account, expired)
- VPN not up (network-gated service)
- Wrong Python version / missing package

**2. Auth/permission failures** — script runs, external service rejects it
- HTTP 401/403
- Rate limit / quota exceeded (429)
- Insufficient permissions on a specific resource

**3. Bad input failures** — caller passed something invalid
- Invalid flag combination
- Input file doesn't exist
- Input is syntactically valid but semantically wrong (wrong date format, unknown ID)
- Required field missing

**4. Silent/partial failures** — the hardest category; script exits 0 but output is wrong
- Empty output (query returned 0 results when >0 were expected)
- Truncated JSON (disk full mid-write, pipe buffer exceeded)
- Structurally valid output that's semantically meaningless (all-null fields)
- `status: "partial"` — got something but not everything

**5. Service degradation**
- Network timeout (request hangs indefinitely)
- HTTP 503 / service unavailable
- Unexpected response schema (API changed, field renamed)
- Retry-loop trap (agent repeats same failing call without adapting)

Category 4 is the most insidious because there's no error signal to react to — Claude has to notice the result is suspicious rather than waiting for an error. Category 5's retry-loop case is empirically the most expensive failure in production (documented 30,000-token burns on a single hanging loop).

### Fixture Format

A failure fixture is a canned `(stdout, stderr, exit_code, status)` tuple that simulates what a script would return under a failure condition. Fixtures live in `references/failure_modes.md` within the skill directory, dual-purposed: they document expected failure handling for Claude (part of the golden path) and serve as test inputs.

Structured fixture definition (for use in `evals/failure_modes.json`):

```json
{
  "skill": "sec-filings",
  "fixtures": [
    {
      "id": "auth_expired",
      "category": "auth",
      "description": "EDGAR API token expired",
      "stdout": "",
      "stderr": "{\"status\": \"error\", \"type\": \"AuthenticationError\", \"message\": \"API token expired. Regenerate at https://efts.sec.gov/LATEST/search-index\", \"recovery\": \"Run sec-setup to refresh credentials\"}",
      "exit_code": 1,
      "expected_claude_behavior": "Tells user their EDGAR token is expired and directs them to regenerate it. Does not retry the request."
    },
    {
      "id": "empty_results",
      "category": "silent_failure",
      "description": "Query returns 0 results for valid ticker",
      "stdout": "{\"status\": \"success\", \"data\": [], \"metrics\": {\"result_count\": 0}}",
      "stderr": "",
      "exit_code": 0,
      "expected_claude_behavior": "Notices result_count is 0, asks whether the ticker is correct or suggests broadening the search. Does not report 'success' and stop."
    },
    {
      "id": "rate_limit",
      "category": "auth",
      "description": "EDGAR rate limit hit",
      "stdout": "",
      "stderr": "{\"status\": \"error\", \"type\": \"RateLimitError\", \"message\": \"Rate limit exceeded: 10 req/min. Retry after 60s.\", \"recovery\": \"Wait 60 seconds and retry.\"}",
      "exit_code": 1,
      "expected_claude_behavior": "Informs user of the rate limit, suggests waiting 60 seconds, does not immediately retry."
    }
  ]
}
```

### Script Output Contract

Scripts should return structured JSON on stdout. This is both a quality standard and a testability requirement — unstructured text output cannot be reliably fixture-tested.

Required schema:

```json
{
  "status": "success | error | partial",
  "data": {},
  "metrics": {
    "result_count": 0,
    "duration_ms": 0
  },
  "error": {
    "type": "AuthenticationError | RateLimitError | InputValidationError | NetworkError | PreflightError | SilentFailure | ToolInternalError",
    "message": "Human-readable explanation",
    "recovery": "Actionable next step for Claude"
  }
}
```

Key decisions in this schema:

- `status: "partial"` is a first-class state, not an error. Some results are legitimately incomplete and Claude should surface that rather than treating them as success or failure.
- `error.type` is a bounded enum, not a free string. Claude can be given explicit per-type handling instructions in the SKILL.md.
- `error.recovery` is written for Claude, not for the user. It's an actionable instruction: "Run sec-setup to refresh credentials", not "Token expired."
- `metrics.result_count` enables cardinality validation for the silent-failure case — Claude can check whether 0 results is expected or suspicious.
- Full stack traces go to a log file, not to stdout. Structured JSON on stdout, verbose diagnostics to stderr or a log. Research shows LLM recovery rates drop from ~80% on structured JSON errors to ~20% on raw stack traces.

### Three Validation Layers

Per-fixture assertions should be structured around three layers, evaluated in order:

**Layer 1 — Structural** (mechanical, always check)
Did Claude parse the output? Did it acknowledge `status: "error"` rather than proceeding as if it succeeded? Did it quote `error.type` in its reasoning?

**Layer 2 — Cardinality** (for silent-failure fixtures)
Did Claude notice `result_count: 0` or `status: "partial"` and react to it? Did it ask a clarifying question or propose an alternative query?

**Layer 3 — Semantic** (LLM-as-judge, for recovery quality)
Did Claude's response follow the `recovery` instruction? Did it avoid repeating the failing call with identical arguments? Did it tell the user the right thing?

### Retry-Loop Assertion

Every eval fixture for categories 2-5 should include an assertion against the retry-loop failure:

> Claude must not repeat the exact same failing call. If the fixture is an error, Claude must either change arguments, use a different approach, or escalate to the user.

This is the most impactful single assertion across all failure categories. It catches the documented 30,000-token failure mode.

### Failure Mode Discovery

The auditor can auto-suggest fixture candidates by analyzing a skill's scripts:

- Any `os.environ.get("X")` or `os.getenv("X")` → suggest `missing_env_var` fixture for X
- Any `subprocess.run` or `os.system` call → suggest `missing_binary` fixture
- Any `requests.get` or `urllib` call → suggest `network_timeout` and `auth_failure` fixtures
- Any file read (`open(path)`) → suggest `file_not_found` fixture
- Any result that's a list → suggest `empty_results` fixture

This is static analysis on script AST. It produces a starter `failure_modes.json` with empty `expected_claude_behavior` fields that the developer fills in. This gets you 80% coverage with no manual enumeration.

---

## Part III: SKILL.md Failure Handling Section

Every skill that uses scripts should have a `## Failure handling` section in SKILL.md that:

1. Lists the relevant error types and what Claude should do for each
2. Explicitly states the retry constraint ("never repeat the same failing call verbatim")
3. Points to `references/failure_modes.md` for the full fixture definitions

Template:

```markdown
## Failure handling

Scripts return structured JSON. If `status` is `"error"` or `"partial"`, handle as follows:

| error.type | Action |
|------------|--------|
| PreflightError | Tell user what's missing. Do not proceed. |
| AuthenticationError | Tell user to refresh credentials via [specific command]. Do not retry. |
| RateLimitError | Wait the specified duration, then retry once. |
| NetworkError | Retry once after 10s. If still failing, tell user the service may be down. |
| InputValidationError | Fix the input per `error.recovery` and retry once. |
| SilentFailure | Tell user results were empty or partial. Ask whether to broaden the query. |
| ToolInternalError | Report the error message to the user verbatim. Do not retry. |

**Retry constraint:** Never repeat a failing call with identical arguments. If a retry fails, escalate to the user.

**Silent failure check:** If `status` is `"success"` but `metrics.result_count` is 0 and that's unexpected, ask the user whether the query parameters are correct before treating the result as valid.
```

---

## Part IV: Integration Points

### With skill-creator

The failure fixture system is an extension of the existing eval framework, not a replacement. `failure_modes.json` is a sibling to `evals/evals.json`. Failure-mode evals run the same fixture injection mechanics as golden-path evals but with pre-baked outputs instead of live script execution.

The skill-creator's eval loop should grow a `--mode failure` flag that runs only fixture-based tests against the failure taxonomy.

### With the auditor

The auditor's static analysis gains two new checks:

1. Does the skill have a `failure_modes.json`? (If not: flag as uncovered)
2. Does the skill have a `## Failure handling` section in SKILL.md? (If not: flag as undocumented)
3. Do the skill's scripts return structured JSON? (Heuristic: does stdout contain `{"status":`)
4. Do the scripts have a pre-flight check? (Heuristic: function named `preflight` or `check_deps`)

These turn into auditor signals with weights comparable to "missing prerequisites section."

### With failure_modes.md

`references/failure_modes.md` is human-readable documentation of the fixture definitions — what each failure means, what conditions trigger it, what good Claude behavior looks like. It serves as the skill author's reference when writing the `## Failure handling` section and as context for Claude when the skill is invoked.

---

## What This Doesn't Cover

**Environment-level failures in CI.** This spec is about Claude's response to failure signals, not about integration testing the scripts themselves in various environments. Container-based script testing (verifying a script actually works on a fresh machine) is a separate concern orthogonal to skill testing.

**Multi-step failure cascades.** A failure in step 3 of a 5-step workflow that causes step 4 to receive bad data is not covered by per-fixture testing. That requires trajectory-level eval, which is more complex and deferred.

**Non-deterministic partial failures.** Some scripts fail randomly (flaky network, intermittent rate limits). Fixture testing treats all failures as deterministic. Flakiness testing is a separate class of problem.

---

## Open Questions

1. **Should `failure_modes.json` live inside the skill dir or in a separate workspace dir?** Putting it inside the skill dir (alongside `evals/evals.json`) is cleaner for discovery but adds non-skill content to the skill package.

2. **Should the auditor auto-generate starter fixtures?** This requires importing the skill's scripts for AST analysis, which adds complexity. The alternative is a separate `skill-auditor generate-fixtures SKILL_NAME` command.

3. **Weight calibration.** The friction score weights are guesses. After running the auditor on the full skill library monthly for 3 months, revisit weights against which skills actually needed intervention.

4. **LLM-as-judge for semantic assertions.** Layer 3 validation requires an LLM call per fixture. For a weekly audit of 30 skills × 5 fixtures each, that's ~150 LLM calls. Acceptable, but needs a budget flag to suppress if running the auditor in a lightweight mode.
