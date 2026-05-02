---
name: tmux
description: Use when manipulating the user's tmux session — opening monitor panes, detecting active windows, sending keys to other windows, or surfacing output without interrupting the user's focus. Also reference for TBD features: Claude Code session topology status bar, terminal artifact display, and Headwater scheduled batch job orchestration.
---

# tmux

Recipes for Claude Code operating inside Brian's tmux environment. Single session index `0`, 2-4 windows, each window typically a Claude Code instance launched via claudeplexer.

**Rule:** Always detect the active window before targeting. Never hardcode a window index.

---

## Detect active window

```bash
win=$(tmux display-message -p '#{window_index}')
```

Use this as the target for any pane operation.

---

## tmux-monitor — open a tail/watch pane below the active window

Validated pattern. Use when Brian asks to "open a monitor", "tail a log", or "watch" something.

```bash
win=$(tmux display-message -p '#{window_index}')
tmux split-window -t "0:${win}" -v "<command>"
```

Examples:
```bash
# Tail a log
tmux split-window -t "0:${win}" -v "tail -f /tmp/app.log"

# Watch a command
tmux split-window -t "0:${win}" -v "watch -n2 'ps aux | grep python'"
```

**Gotcha:** `-v` splits vertically (pane below). `-h` splits horizontally (pane to the right). For monitors, below is almost always correct.

---

## Inspect pane state before sending keys

Always check what's running in a pane before sending keystrokes. A bare shell is safe; a TUI will misinterpret input.

```bash
cmd=$(tmux display-message -p -t "0:<win>.<pane>" '#{pane_current_command}')
```

**TUI signals — do NOT send arbitrary text:**
- `nvim`, `vim` — editor commands
- `htop`, `ncdu`, `lazygit` — TUI navigation
- `less`, `man` — pager commands

**Safe to send:** `bash`, `zsh`, `sh`, `ssh` (at a shell prompt on the remote end)

If a TUI is detected, bail and tell Brian rather than guessing.

---

## Send keys to another window without switching

Use when Claude needs to trigger something in a different window (restart a process, run a command) without interrupting Brian's focus.

**Always inspect pane state first** (see above), then send:

```bash
tmux send-keys -t "0:<win>.<pane>" "<command>" Enter
```

To send Ctrl-C (interrupt):
```bash
tmux send-keys -t "0:<win>.<pane>" C-c
```

To answer an interactive prompt (`[Y/n]`, host key confirmation, etc.) — read the pane first to confirm what it's asking, then send:
```bash
tmux send-keys -t "0:<win>.<pane>" "y" Enter
```

**Caveat:** Password prompts use noecho — the prompt text may not be visible in the capture. Don't send passwords blindly.

**Safety:** List windows first to confirm the target is what you expect:
```bash
tmux list-windows -t 0 -F "#{window_index} #{window_name} #{pane_current_command}"
```

---

## Read a pane's visible content

Use to read what's on screen in any pane without interrupting it — pipe output, error state, log tail.

```bash
tmux capture-pane -pt "0:<win>.<pane>"
```

Pane index defaults to `0` (active pane in that window):
```bash
tmux capture-pane -pt "0:${win}.0"
```

**Token discipline:** Trim to last N lines to avoid bloating context with noisy output (apt installs, systemd logs, etc.):
```bash
tmux capture-pane -pt "0:<win>.<pane>" | tail -30
```

Only re-capture after sending a command — don't poll speculatively.

---

## Remote shell execution (SSH panes)

When a pane is SSH'd into a remote host, send-keys works the same — keystrokes go to the remote shell's stdin. The pattern:

1. Confirm pane command is `ssh` (not a TUI on the remote end)
2. Send the command
3. Wait briefly, then capture to read output

```bash
tmux send-keys -t "0:<win>.<pane>" "<command>" Enter
sleep 1
tmux capture-pane -pt "0:<win>.<pane>" | tail -30
```

Increase sleep for slow commands (package installs, network ops). For long-running commands, re-capture until the shell prompt reappears.

---

## List all windows with process info

```bash
tmux list-windows -t 0 -F "#{window_index} #{window_name} #{pane_current_command} #{pane_current_path}"
```

Useful for finding which windows have `claude` running vs plain shell.

---

## TBD: Claude Code session topology status bar

**Status:** Design complete, not yet implemented.
**Design doc:** `design-statusbar.md` in this skill directory.

Summary: A `status-right` segment that polls all windows, detects which are running `claude` vs shell, infers active/waiting/stalled state from JSONL mtime, and color-codes each window by state. Script at `~/.config/tmux/cc-status.sh`.

Key implementation note: `encode_path` must match claudeplexer's actual path encoding — verify against a real `~/.claude/projects/` directory name before wiring up.

---

## TBD: Terminal artifact display

**Status:** Design complete, not yet implemented.
**Design doc:** `design-artifact.md` in this skill directory.

Summary: When Claude produces a significant artifact (design doc, long report, code block), display it in a floating tmux popup rendered with `glow` (fallback: `bat`, then `less`). Popup is modal — appears, Brian reads, any key dismisses. Zero persistent state required.

Recommended invocation:
```bash
cat > /tmp/claude-artifact.md << 'ARTIFACT'
<content>
ARTIFACT

RENDER_CMD="less /tmp/claude-artifact.md"
command -v bat  &>/dev/null && RENDER_CMD="bat --paging=always /tmp/claude-artifact.md"
command -v glow &>/dev/null && RENDER_CMD="glow /tmp/claude-artifact.md"
tmux display-popup -w 80% -h 80% -E "$RENDER_CMD; echo '--- press any key ---'; read -rn1"
```

---

## TBD: Headwater scheduled batch job orchestration

**Status:** Design complete, not yet implemented.
**Design doc:** `design-broadcast.md` in this skill directory.

Summary: Instead of broadcasting prompts to tmux agent windows at runtime, submit a batch job to HeadwaterServer's `/jobs` endpoint and let the server execute inference autonomously at a scheduled time (e.g., 3 AM). MacBook can be closed after submit. Client fetches results the next morning via `--fetch JOB_ID`.

Key components: `POST /jobs` on the router (port 8081), SQLite job store with TTL cleanup, asyncio scheduler in FastAPI lifespan, new `--submit` / `--fetch` flags on `classify_orgs.py`.

Key implementation note: the router's scheduler calls `/conduit/batch` on a backend server as an HTTP client — it does not call the conduit batch service function directly. `aiosqlite` must be added to `headwater-server/pyproject.toml`.
