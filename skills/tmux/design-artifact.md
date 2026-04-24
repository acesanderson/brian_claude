# tmux Artifact Display — Design Sketch

---

## Approach 1: tmux display-popup + glow

Claude writes artifact to `/tmp/claude-artifact.md`, then opens a floating popup rendering it.

**Send command (Claude runs):**
```bash
cat > /tmp/claude-artifact.md << 'EOF'
<artifact content>
EOF
tmux display-popup -w 80% -h 80% -E "glow /tmp/claude-artifact.md; read -n1"
```

**Brian's UX:** Popup appears immediately. Press any key or `q` to dismiss. No action required to open — it appears automatically.

**Pros:**
- Zero setup — works in any window, no dedicated pane needed
- Dismissal is one keypress, leaves no residue in the layout

**Cons:**
- Blocks the pane until dismissed (display-popup is modal-ish)
- Cannot easily scroll back to a previous artifact — `/tmp/claude-artifact.md` is overwritten each time
- Requires `glow` installed; fallback to `bat` is possible but markdown won't reflow

---

## Approach 2: Dedicated artifacts window

A persistent tmux window (`artifacts`) runs a watcher loop. Claude writes to a file; the watcher re-renders on change.

**One-time setup (Brian runs once):**
```bash
tmux new-window -n artifacts
tmux send-keys -t artifacts "while true; do inotifywait -e close_write /tmp/claude-artifact.md 2>/dev/null && clear && glow /tmp/claude-artifact.md; done" Enter
```
Or a simpler polling version (macOS-compatible, no inotifywait):
```bash
tmux send-keys -t artifacts \
  'while true; do f=/tmp/claude-artifact.md; [ -f "$f" ] && clear && glow "$f"; sleep 1; done' Enter
```

**Send command (Claude runs):**
```bash
cat > /tmp/claude-artifact.md << 'EOF'
<artifact content>
EOF
```

**Brian's UX:** Switch to `artifacts` window to read. Stay in current window and artifact updates silently. Dismiss by switching back.

**Pros:**
- Non-blocking — Claude writes and moves on; Brian reads at leisure
- Artifacts window persists and shows last artifact until overwritten

**Cons:**
- Requires one-time session setup; breaks if tmux session is recreated
- Polling loop wastes cycles; inotifywait not available on macOS by default
- Brian must manually switch windows — no visual interrupt

---

## Approach 3: nvim in a side split

Claude writes the artifact to a tmp file, then opens it in nvim in a new horizontal pane in the current window.

**Send command (Claude runs):**
```bash
artifact=/tmp/claude-artifact.$(date +%s).md
cat > "$artifact" << 'EOF'
<artifact content>
EOF
tmux split-window -h -l 60 "nvim -R '$artifact'"
```

**Brian's UX:** Right pane opens with nvim in read-only mode. Full navigation, search, yank. Close with `:q`. Pane disappears.

**Pros:**
- Full nvim power — search, copy, fold, navigate
- Works with any file type; nvim handles md, py, json, etc. natively
- No extra renderer dependency

**Cons:**
- Splits the current window — disrupts Claude Code's pane layout
- nvim startup has noticeable latency vs. a popup
- Requires Brian to `:q` explicitly; split lingers if forgotten

---

## Approach 4: Named pipe / FIFO

A pre-running renderer process reads from a named pipe. Claude streams content into it.

**One-time setup:**
```bash
mkfifo /tmp/claude-artifact-pipe
tmux new-window -n artifacts "while true; do clear; glow /tmp/claude-artifact-pipe; done"
```

**Send command (Claude runs):**
```bash
cat << 'EOF' > /tmp/claude-artifact-pipe
<artifact content>
EOF
```

**Brian's UX:** Artifact appears instantly in the `artifacts` window as Claude writes. Non-blocking.

**Pros:**
- True streaming — content renders as it arrives
- No polling; pipe wakes the reader on write

**Cons:**
- FIFOs block the writer until a reader consumes — if the artifacts window dies, Claude hangs
- glow reads the whole pipe before rendering; streaming advantage is largely lost
- Most fragile of the four: pipe state, reader state, and writer must all align

---

## Recommendation

**Lead with Approach 1 (display-popup + glow).**

Rationale:
- Zero persistent state — no setup window, no background loop, nothing to break
- Modal popup is the closest tmux equivalent to Desktop's artifact panel: it appears, you read, you dismiss
- The blocking behavior is a feature for significant artifacts — it signals "something worth reading appeared"
- Fallback to `bat` if glow is absent is a one-liner change

For a `persistent/stackable` variant, pair Approach 1 with a per-artifact timestamp filename so previous artifacts aren't lost:
```bash
ts=$(date +%Y%m%dT%H%M%S)
artifact="/tmp/claude-artifact-${ts}.md"
```
Then offer a separate `/artifact-history` command that lists and lets Brian pick one to re-open.

---

## Recommended snippet

```bash
#!/usr/bin/env bash
# Usage: artifact-show <title> <content-file-or-stdin>
# Claude calls this after writing content to /tmp/claude-artifact.md

ARTIFACT_FILE="/tmp/claude-artifact.md"

# Write artifact (Claude already did this, but here for reference)
# cat > "$ARTIFACT_FILE"

# Render: prefer glow, fall back to bat, fall back to less
if command -v glow &>/dev/null; then
    RENDER_CMD="glow $ARTIFACT_FILE"
elif command -v bat &>/dev/null; then
    RENDER_CMD="bat --paging=always $ARTIFACT_FILE"
else
    RENDER_CMD="less $ARTIFACT_FILE"
fi

tmux display-popup \
    -w 80% \
    -h 80% \
    -E "$RENDER_CMD; echo '--- press any key to close ---'; read -rn1"
```

**Claude's invocation pattern:**
```bash
cat > /tmp/claude-artifact.md << 'ARTIFACT'
<generated content>
ARTIFACT
bash ~/.claude/skills/tmux-artifacts/show-artifact.sh
```
