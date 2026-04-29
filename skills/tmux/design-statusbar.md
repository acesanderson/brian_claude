# tmux Claude Code Topology Status Bar

## State Detection Approach

**Active vs Waiting** (approximate, no inotify needed):
- Find JSONL for each window's CWD via `ps -p <pid> -o args=` → extract `--cwd` or infer from pane CWD
- Check `stat -f %m ~/.claude/projects/<encoded>/*.jsonl` — mtime within last 5s → **active**
- `pane_current_command == claude` but JSONL mtime > 5s → **waiting**
- `pane_current_command` is `zsh`/`bash` → **exited**

**PID→CWD mapping:**
```sh
pgrep -a claude | awk '{print $1}' | while read pid; do
  lsof -p "$pid" -d cwd -Fn 2>/dev/null | grep '^n' | sed 's/^n//'
done
```

---

## Polling Script (`~/.config/tmux/cc-status.sh`)

```sh
#!/usr/bin/env bash
# Outputs a tmux-formatted status segment for Claude Code windows

SESSION=0
NOW=$(date +%s)
ACTIVE_THRESH=5   # seconds since JSONL mtime = "active"
WAITING_THRESH=30 # mtime older than this = "waiting"

# Nerd Font icons (fallback to ASCII if unavailable)
ICON_ACTIVE=""   # nf-md-lightning_bolt  (or use ">")
ICON_WAIT=""     # nf-md-timer_sand      (or use "~")
ICON_DONE=""     # nf-md-check_circle    (or use "-")
ICON_SHELL="$"

encode_path() {
  # Match claudeplexer's encoding: replace / with - (simplified)
  echo "$1" | sed 's|^/||' | tr '/' '-'
}

latest_jsonl_mtime() {
  local cwd="$1"
  local encoded
  encoded=$(encode_path "$cwd")
  local dir="$HOME/.claude/projects/${encoded}"
  [[ -d "$dir" ]] || { echo 0; return; }
  find "$dir" -name '*.jsonl' -exec stat -f %m {} \; 2>/dev/null | sort -n | tail -1
}

out=""
while IFS=$'\t' read -r idx name cmd pane_cwd; do
  if [[ "$cmd" == "claude" ]]; then
    mtime=$(latest_jsonl_mtime "$pane_cwd")
    age=$(( NOW - mtime ))
    shortname=$(basename "$pane_cwd")
    if (( age <= ACTIVE_THRESH )); then
      state="#[fg=colour2]${ICON_ACTIVE}"   # green
      label="#[fg=colour2,bold]${shortname}"
    elif (( age <= WAITING_THRESH )); then
      state="#[fg=colour3]${ICON_WAIT}"     # yellow
      label="#[fg=colour3]${shortname}"
    else
      state="#[fg=colour1]${ICON_WAIT}"     # red/stalled
      label="#[fg=colour1]${shortname}"
    fi
    out+="#[fg=colour8][#[default]${state} ${label}#[fg=colour8]]#[default] "
  elif [[ "$cmd" =~ ^(zsh|bash|fish)$ ]]; then
    shortname=$(basename "$pane_cwd")
    out+="#[fg=colour8][#[fg=colour245]${ICON_SHELL} ${shortname}#[fg=colour8]]#[default] "
  fi
done < <(tmux list-windows -t "$SESSION" \
  -F "#{window_index}\t#{window_name}\t#{pane_current_command}\t#{pane_current_path}" 2>/dev/null)

echo -n "${out% }"
```

---

## tmux.conf Snippet

```tmux
# Claude Code session topology in status-right
set -g status-right-length 200
set -g status-right '#(~/.config/tmux/cc-status.sh) #[fg=colour8]| #[default]%H:%M'
set -g status-interval 3   # poll every 3s; low overhead for shell script

# Optional: highlight active window tab
setw -g window-status-current-style 'fg=colour2,bold'
setw -g window-status-format         '#I:#W'
setw -g window-status-current-format '#I:#W*'
```

---

## ASCII Mockup

```
┌─────────────────────────────────────────────────────────────────────┐
│ 0:main  1:yolo-box  2:morgan  3:sift          [ vibe] [ yolo-box] [~ morgan] [$ sift] | 14:32 │
└─────────────────────────────────────────────────────────────────────┘

Legend:
  [  vibe]      green lightning  = active (JSONL < 5s old)
  [~ morgan]    yellow hourglass = waiting (JSONL 5-30s old)
  [  yolo-box]  red hourglass    = stalled (JSONL > 30s, claude still running)
  [$ sift]      grey $           = plain shell, no claude
```

---

## Gotchas

1. **encode_path must match claudeplexer exactly.** If claudeplexer uses URL-encoding or a different scheme, `latest_jsonl_mtime` finds nothing and everything looks stalled. Verify against an actual `~/.claude/projects/` directory name first.

2. **`pane_current_path` vs actual CWD.** If the user `cd`'d inside the pane after launch, `pane_current_path` drifts. JSONL lookup will miss. Anchor on the project dir registered at session start if claudeplexer writes that to resurrect.json.

3. **`stat -f %m` is macOS-only.** Linux needs `stat -c %Y`. Add a guard:
   ```sh
   if stat --version 2>/dev/null | grep -q GNU; then STAT_FMT='-c %Y'; else STAT_FMT='-f %m'; fi
   ```

4. **status-right length.** With 4+ windows the string grows. `status-right-length 200` handles 6 windows comfortably; beyond that consider a left+right split or abbreviate shortnames to 8 chars.

5. **`lsof` on each poll is expensive.** Skip it — use `pane_current_path` from tmux directly (already in the format string). Only fall back to `lsof` if you need the exact project dir and pane_current_path is unreliable.

6. **Multiple panes per window.** `list-windows` gives one pane's command. If a window has splits, `pane_current_command` is whichever pane is active. For claude detection, filter with `tmux list-panes -t "$SESSION:$idx" -F '#{pane_current_command}'` and check any pane.
