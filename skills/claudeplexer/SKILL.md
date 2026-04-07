---
name: claudeplexer
description: Reference for the claudeplexer CLI tool. ONLY invoke this skill when the user explicitly asks to use claudeplexer, mentions it by name, or asks for help with it. Do not trigger automatically for general Claude Code or tmux questions.
---

# claudeplexer

Launches multiple Claude Code interactive sessions in parallel tmux windows. Each window opens with a pre-loaded prompt and stays fully interactive.

**Project:** `/Users/bianders/vibe/claudeplexer-project`
**Invoke via:** `uv run --project /Users/bianders/vibe/claudeplexer-project claudeplexer`

---

## Two modes

### Mode 1 — Prompt strings

Pass prompts directly as positional arguments. Each becomes one tmux window.

```sh
claudeplexer "Prompt for item one" "Prompt for item two" "Prompt for item three"
```

### Mode 2 — Jinja2 template + vars

Provide a single template and a JSON array of variable dicts. One window is launched per dict.

```sh
claudeplexer \
  --template "Review item <number>{{ number }}</number> in the doc. Think step by step." \
  --vars '[{"number": "1"}, {"number": "2"}, {"number": "3"}]'
```

The template can be an inline string or a file path. Variables must exactly match the template's Jinja2 placeholders — missing or extra keys are an error.

**Vars from file** (JSON array or JSONL, one object per line):

```sh
claudeplexer --template template.j2 --vars-file vars.jsonl
```

---

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--session NAME` | current session | Create a new named tmux session instead of using the active one |
| `--max N` | 10 | Cap on concurrent windows |

If run outside a tmux session without `--session`, claudeplexer exits with an error.

---

## Constraints

- Modes cannot be mixed: prompt strings + `--vars` is an error
- `--vars` and `--vars-file` cannot be used together
- Max 10 windows per invocation
