---
name: claudeplexer
description: Reference for the claudeplexer CLI tool. ONLY invoke this skill when the user explicitly asks to use claudeplexer, mentions it by name, or asks for help with it. Do not trigger automatically for general Claude Code or tmux questions.
---

# claudeplexer

Launches and manages Claude Code sessions in tmux windows.

**Project:** `/Users/bianders/vibe/claudeplexer-project`
**Invoke via:** `uv run --project /Users/bianders/vibe/claudeplexer-project claudeplexer`

---

## Commands

### `launch` — Start new Claude Code instances

**Mode 1 — Prompt strings**

```sh
claudeplexer launch "Prompt for item one" "Prompt for item two"
```

**Mode 2 — Jinja2 template + vars**

```sh
claudeplexer launch \
  --template "Review item <number>{{ number }}</number>." \
  --vars '[{"number": "1"}, {"number": "2"}]'
```

The template can be an inline string or a file path. Variables must exactly match the Jinja2 placeholders.

**Vars from file** (JSON array or JSONL):

```sh
claudeplexer launch --template template.j2 --vars-file vars.jsonl
```

| Flag | Default | Description |
|------|---------|-------------|
| `--session NAME` | current session | Create a new named tmux session |
| `--max N` | 10 | Cap on concurrent windows |

---

### `save` — Save current session to resurrect manifest

Run this from within a Claude Code session to record its ID for later restoration.

```sh
claudeplexer save
claudeplexer save --name "my-project"
```

Detects the session by finding the most recently modified JSONL in
`~/.claude/projects/<encoded-cwd>/`. Writes to `~/.claude/resurrect.json`,
deduplicating by working directory.

| Flag | Default | Description |
|------|---------|-------------|
| `--name NAME` | directory basename | Human-readable window name |
| `--manifest PATH` | `~/.claude/resurrect.json` | Manifest file |

---

### `resurrect` — Restore saved sessions

Reads the manifest and opens each session in a tmux window. Each window runs:
```
cd <cwd> && claude --resume <session-id>
```

```sh
claudeplexer resurrect
claudeplexer resurrect --session restored --clear
```

| Flag | Default | Description |
|------|---------|-------------|
| `--session NAME` | current tmux session | Create a new named tmux session |
| `--manifest PATH` | `~/.claude/resurrect.json` | Manifest file |
| `--clear` | off | Delete manifest entries after restoring |

---

## Session resurrection workflow

**Before reboot** — in each Claude Code session, ask Claude to run:
```sh
claudeplexer save
# or with a custom name:
claudeplexer save --name "headwater"
```

**After reboot** — from any tmux session:
```sh
claudeplexer resurrect --session restored --clear
```

This opens each saved session in a new tmux window with `claude --resume`.
Note: `claude --resume` restores conversation history but not session-scoped
permissions. The working directory is restored via `cd` before launching.

---

## Constraints

- `launch`: modes cannot be mixed (prompt strings + `--vars` is an error)
- `launch`: max 10 windows per invocation
- `save`: multiple sessions in the same directory — picks the most recently modified JSONL, which is the active session as long as no two Claude instances share a cwd simultaneously
