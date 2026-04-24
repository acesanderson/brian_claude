---
name: tmux
description: Use when manipulating the user's tmux session — opening monitor panes, detecting active windows, sending keys to other windows, or surfacing output without interrupting the user's focus. Also reference for TBD features: Claude Code session topology status bar and terminal artifact display.
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

## Send keys to another window without switching

Use when Claude needs to trigger something in a different window (restart a process, run a command) without interrupting Brian's focus.

```bash
tmux send-keys -t "0:<win>" "<command>" Enter
```

To send Ctrl-C (interrupt):
```bash
tmux send-keys -t "0:<win>" C-c
```

**Safety:** List windows first to confirm the target is what you expect before sending keys to it:
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
