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

**After reboot** — from within your existing tmux session:
```sh
claudeplexer resurrect --clear
```

This opens each saved session as a new window in the **current tmux session**. Do NOT pass `--session` unless you want to create a separate tmux session for the restored windows.
Note: `claude --resume` restores conversation history but not session-scoped
permissions. The working directory is restored via `cd` before launching.

---

### `alias` — Tag the current session with a name

Stores an alias for the current session in the `claude_history` database.

```sh
claudeplexer alias roger
```

Detects the session the same way `save` does (most recently modified JSONL for the current working directory). Requires VPN to reach the Postgres DB.

---

## Session alias workflow

### Saving an alias

When the user says something like **"alias this session as 'X'"** or **"save this session as 'X' with claudeplexer"**, run:

```sh
uv run --project /Users/bianders/vibe/claudeplexer-project claudeplexer alias X
```

### Loading an alias into memory

When the user says something like **"load the alias 'X' session"** or **"resume the 'X' session"**, run these two commands in sequence:

```sh
# 1. Resolve alias to session_id
uv run --directory ~/vibe/claude-history-project python ~/.claude/skills/claude-history/run.py alias get X

# 2. Fetch all turns for that session_id (use session_id from step 1)
uv run --directory ~/vibe/claude-history-project python ~/.claude/skills/claude-history/run.py turns <session_id> --limit 200
```

Parse the JSON output of step 2 and summarize the session context into the current conversation. Focus on: what was being worked on, key decisions made, current state, and any open threads.

---

## Constraints

- `launch`: modes cannot be mixed (prompt strings + `--vars` is an error)
- `launch`: max 10 windows per invocation
- `save`: multiple sessions in the same directory — picks the most recently modified JSONL, which is the active session as long as no two Claude instances share a cwd simultaneously
