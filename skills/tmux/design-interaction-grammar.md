---
status: WIP
started: 2026-04-30
---

# tmux Interaction Grammar — Design WIP

Design session for a fluent human/LLM agent collaboration vocabulary built on tmux primitives. Goal: make Claude's work legible in real-time (shared situational awareness), not just report results after the fact.

---

## Design Goals

- **Passive observation by default** — monitoring panes give ambient awareness; intervention is always manual (Ctrl-C in the target session)
- **Capability vocabulary first** — enumerate what Claude can do when asked; predefined layout templates come later
- **MVP implementations** — design comprehensively, implement minimally

---

## Use Cases (from history survey, Apr 24–30)

Three domains benefit from tmux primitives. Others (LinkedIn BD email, silt research) are conversational — the agent output is the interface.

| Domain | Why tmux helps |
|--------|---------------|
| DevOps / homelab | Remote shell execution, log tailing, service status |
| Software engineering | Build output, test runners, dev servers |
| Long-running autonomous agents | Ambient visibility into what subagents are doing |
| Writing / drafts | Artifact display + nvim handoff |

---

## Primitive Vocabulary

### User-facing (verbally invoked)

| Primitive | Description |
|-----------|-------------|
| `observe` | Snapshot a pane's current content |
| `watch-log` | Tail a file in a new pane below |
| `send-command` | Send keystrokes to a target pane |
| `answer-prompt` | Respond to an interactive prompt in a pane |
| `remote-exec` | Execute a command on an SSH pane |
| `agent-log` | Open consolidated JSONL feed for current session + subagents |
| `conduit-monitor` | Tail conduit's LLM request/response log in a new pane |
| `display-artifact` | Render markdown in a persistent split pane with glow |
| `edit-artifact` | Open current artifact in nvim in a new window |

### Agent-internal (composed silently, not verbally triggered)

| Primitive | Description |
|-----------|-------------|
| `inspect` | Check `pane_current_command` before acting |
| `spawn-pane-below` | `-v` split below active window |
| `spawn-pane-right` | `-h` split right |
| `spawn-window` | New tmux window |
| `label-pane` | Name a pane for later lookup |
| `find-pane` | Check if a named pane exists before spawning a duplicate |
| `close-pane` | Kill a pane (only on explicit user request for now) |

---

## Agent-Log Format Spec

Source: `~/.claude/projects/<encoded-path>/*.jsonl` — watch directory for new files as subagents spawn.

**Rules:**
- Single line per entry (no multi-line output)
- Strip all newlines from output; use first line only, rest discarded
- Fixed width: total line ≤ 120 chars
- Always show command lines even if no output follows

**Format:**
```
[orch ]  $ ansible-playbook site.yml -l lasker
[orch ]  → ok: [lasker] => (item=python3-pip) … [truncated]
[agt:1]  $ uv run conduit.py search "teachable competitors"
[agt:1]  → {"results": [{"title": "Kajabi vs Teach… [truncated]
[agt:2]  ✗ Connection refused: nimzo:8080
```

**Sigils:** `$` command, `→` output, `✗` non-zero exit / stderr

**Color coding:**
- Agent label prefix: distinct color per agent (orchestrator = green, subagents cycle through cyan/yellow/magenta)
- Command lines: white/bright
- Output lines: dimmed
- Errors (`✗`): red regardless of agent

**Idempotency:** label the pane `agent-log` on spawn; check for existing pane before opening a second one.

---

## Lifecycle Decisions

- Monitoring panes are **left open** when task completes — user dismisses manually
- Panes are **labeled on spawn** so agent can find them again
- `find-pane` always runs before `spawn-pane` to prevent duplicates

---

## TODO (pick up here next session)

1. **Verbal triggers** — natural language phrases that map to each user-facing primitive. E.g. "tail a log in the pane below" → `watch-log`. Need a comprehensive trigger list per primitive.
2. **Layout templates** — predefined pane arrangements for common scenarios (devops session, agent orchestration session, writing session). Not MVP but worth designing.
3. **Skill update** — fold all of the above into SKILL.md as new sections, replacing/extending existing recipes.
4. **Implementation priority** — `agent-log` and `display-artifact` are the highest-value MVPs. Start there.

---

## Cross-domain references that informed this design

- **Supervisory control** (aviation/aerospace): human sets intent, agent executes, human can always interrupt
- **OODA loop**: Observe → Orient → Decide → Act; human injects at any stage
- **Actor model**: panes as actors, send-keys as message passing, claudeplexer as actor spawning
- **Distributed systems logging**: color-coded prefixes (docker-compose), structured line format (Datadog/Loki), single-line discipline
