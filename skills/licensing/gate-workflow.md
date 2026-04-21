# Gate Decision Workflow

## Logging a gate decision

Fires when a course passing or failing a gate is mentioned in conversation —
e.g., "CS rejected the Fortinet FortiGate course, SCORM format" or "Anaconda Docker
Engineering passed topic review".

1. Extract all available fields: `partner_slug`, `course_title`, gate number, decision,
   `reason_code`, `reason_detail`, `decided_by`, `submitted_date`, `decided_date`.
   Ask for any missing required fields (partner, course, gate, decision) before writing.
   Infer `reason_code` from the taxonomy in `projects/pipeline-ops/notes.md` if not
   explicitly stated — confirm with Brian if ambiguous.
2. Read `gate_log.json`. Compute next sequential ID (`gl-NNN`). Compute `velocity_days`
   if both dates are available. Append the new entry. Write `gate_log.json`.
3. Append a one-line note to `partners/<slug>/notes.md` under a `## Gate Log` section
   (create the section if absent):
   `- YYYY-MM-DD | Gate N | decision | reason_code | course_title`
4. Append to `manifest.md`:
   `- YYYY-MM-DD | gate-decision | gate_log.json | <id>: <partner> / "<course>" / Gate N / <decision>`

Use `log_gate.py` only for programmatic/batch logging. In-session logging always goes
through this hook directly (read → mutate → write `gate_log.json`).

## Gate report / funnel summary

Triggers: "gate report", "funnel summary", "conversion rates", "rejection breakdown".

1. Read `gate_log.json`.
2. Compute and display inline — no script needed:
   - Per gate: total decisions, pass/reject/pending/withdrawn counts and rates, avg velocity,
     rejection reason breakdown (count + %)
   - Partner summary table: submitted, pass, reject, pending, pass rate
3. Apply any filters mentioned (`--partner`, `--gate`, `--since`).

If the log is empty, say so and remind Brian the hook fires automatically when gate
decisions are mentioned in session.

## Sync gate log to Google Sheet

Trigger: "sync gate log".

See `~/.claude/skills/licensing/tooling-reference.md` for the full sync procedure.
