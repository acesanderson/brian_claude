---
name: conduit
description: Use when a task involves a non-Anthropic model — Perplexity for research, Gemini, local Ollama, image generation, or any multi-model workflow. Conduit is the LLM runtime to reach for whenever the right tool is not a Claude model.
---

# conduit

Conduit is the local LLM runtime. When a task calls for a non-Anthropic model — a search-grounded query via Perplexity, a cheap local subtask via Ollama, image generation, or multi-model chaining — conduit is how you invoke it.

**Rule:** Any time Claude Code delegates to a non-Claude model, it does so through conduit.

---

## `ask` / `conduit query` — query any LLM

```bash
ask "your query"
ask --model <model> "your query"
cat file.txt | ask --model <model> "summarize this"
ask --raw --model <model> "query"   # plain stdout, safe to pipe
```

| Flag | Effect |
|------|--------|
| `--model <model>` | Override default model |
| `--local` | Route to local Ollama |
| `--raw` | Plain text output — no Rich rendering, pipeable |
| `--temperature <float>` | Set temperature |
| `--chat` | Include conversation history |
| `--append <text>` | Append extra text to query |

---

## `models` — discover and inspect models

```bash
models                        # list all models
models -m <model>             # model details (fuzzy match on miss)
models -t <type>              # filter by type
models -p <provider>          # filter by provider
models -a                     # show all aliases
models -e                     # show embedding models only
```

Use `models` to find the exact model identifier before passing `--model`.

---

## `tokenize` — count tokens before a call

```bash
tokenize "your text here"
tokenize -m <model> "your text here"   # model-specific tokenizer (default: gpt)
```

Prints: `Number of tokens: N`. Use this before sending large inputs to expensive models.

---

## `tokens` — usage stats / odometer

```bash
tokens
```

Prints total requests, tokens (input/output), breakdown by provider and model, today vs. all-time. Use to monitor spend during long sessions.

---

## `imagegen` — generate images

```bash
imagegen generate "your prompt"
imagegen generate --model <model> "your prompt"
imagegen history              # numbered list of past generations
imagegen last                 # show last generated image
imagegen get <N>              # show image N from history
```

| Model alias | Resolves to |
|-------------|-------------|
| `banana` / `google-imagen` | `gemini-2.5-flash-image` (default) |
| `imagegen` | `dall-e-3` |
| `gemini-3-pro-image-preview` | Higher quality Gemini |
| `imagen-4.0-generate-001` | Google Imagen 4 (Vertex credentials required) |

---

## `chat` — interactive chat session

```bash
chat                          # enhanced input mode (default)
chat -i basic                 # basic input mode
```

---

## `conduit` — conversation management

```bash
conduit history               # view message history for current session
conduit last                  # show last response
conduit get <N>               # show message N
conduit wipe                  # clear session history (with confirmation)
conduit config                # show current configuration
```

---

## `conduit_cache` — inspect/manage the LLM cache

```bash
conduit_cache                         # list all cached projects with stats
conduit_cache -p <project>            # list recent entries for a project
conduit_cache -p <project> -l        # show payload of last cache entry
conduit_cache -p <project> -w        # wipe all entries for project (with confirmation)
```

---

## POSIX pipe patterns

`--raw` makes `ask` output plain text to stdout. This is the key to chaining conduit into pipelines.

```bash
# Research → image generation
ask --raw --model perplexity "describe a coral reef at 30m depth" \
  | imagegen generate --model banana

# Summarize a large file before including in context
cat large_doc.md | ask --raw --model <local-model> "summarize in 5 bullets"

# Multi-step: research → draft
ask --raw --model perplexity "latest on X" > research.txt
cat research.txt | ask --model claude "write a summary paragraph"
```

---

## When to use which model

- **Perplexity** — web-grounded research, current events, citations
- **Ollama (`--local`)** — sensitive data, offline, cheap subtasks, cost reduction
- **Gemini / Imagen** — image generation, multimodal, long context
