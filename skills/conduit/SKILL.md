---
name: conduit
description: Use when a task involves a non-Anthropic model — Perplexity for research, Gemini, local/open-weight models via Headwater, image generation, or any multi-model workflow. Conduit is the LLM runtime to reach for whenever the right tool is not a Claude model.
---

# conduit

Conduit is the LLM runtime. When a task calls for a non-Anthropic model — a search-grounded query via Perplexity, an open-weight model via Headwater, image generation, or multi-model chaining — conduit is how you invoke it.

**Rule:** Any time Claude Code delegates to a non-Claude model, it does so through conduit.

---

## Local model inference — AlphaBlue / Headwater ONLY

**Do NOT invoke Ollama on the local MacBook.** It saturates memory and disrupts other work.

All open-weight / Ollama-backed models (`gpt-oss:latest`, `llama`, `qwen`, `quant`, etc.) must run on the **AlphaBlue** host via **HeadwaterServer / HeadwaterClient**.

- **MacBook**: Headwater remote client only. Never use `--local` or invoke `ollama` directly.
- **AlphaBlue**: Ollama runs locally; direct use is fine.
- The `gpt-oss` alias is the preferred local model. Conduit routes it through Headwater automatically when the remote backend is configured.

If you need a cheap/fast local model and are not on AlphaBlue, use a cloud API (e.g., `haiku`, `gpt-mini`) instead.

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
| `--citations` / `-C` | Print source citations (Perplexity models only) |

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

## `conduit batch` — parallel queries

Run multiple prompts against a model simultaneously. All requests fire in parallel; results are returned in input order.

```bash
# Inline prompts — primary use case for agentic multi-angle research
conduit batch -m sonar-pro \
  "What are the philosophical implications of X?" \
  "What does the economic data say about X?" \
  "What are the technical constraints on X?" \
  "What do critics of X argue?" \
  "What are historical precedents for X?"

# From a file (one prompt per line)
conduit batch -m gpt-4o -f prompts.txt

# From stdin
cat prompts.txt | conduit batch -m sonar-pro

# File + inline merged
conduit batch -f base_prompts.txt "one more angle" -m claude
```

| Flag | Effect |
|------|--------|
| `-m, --model` | Model for all prompts |
| `-t, --temperature` | Temperature (0.0–1.0) |
| `-f, --file PATH` | Read prompts from file (one per line) |
| `-n, --max-concurrent INT` | Cap parallel requests |
| `-a, --append TEXT` | Suffix appended to every prompt |
| `-r, --raw` | Plain text output, separated by `---` |
| `--json` | Output as JSON array `[{index, prompt, response}]` |

**Output modes:**

```bash
# Default: numbered headers + markdown bodies (pretty)
conduit batch -m sonar-pro "Q1" "Q2"

# Raw: pipe-friendly, responses separated by ---
conduit batch -m sonar-pro --raw "Q1" "Q2"

# JSON: jq-friendly structured output
conduit batch -m sonar-pro --json "Q1" "Q2" | jq '.[].response'
```

**Agentic pattern — multi-angle research:**

When an agentic task calls for exploring a problem from multiple dimensions, write the prompts and call batch rather than making sequential `ask` calls:

```bash
# Write prompts to a temp file, then batch
conduit batch --json -m sonar-pro \
  "$(cat /tmp/prompt1.txt)" \
  "$(cat /tmp/prompt2.txt)" \
  "$(cat /tmp/prompt3.txt)" | jq -r '.[].response' | paste -sd '\n---\n'
```

---

## POSIX pipe patterns

`--raw` makes `ask` output plain text to stdout. This is the key to chaining conduit into pipelines.

```bash
# Research → image generation
ask --raw --model sonar-pro "describe a coral reef at 30m depth" \
  | imagegen generate --model banana

# Summarize a large file before including in context
cat large_doc.md | ask --raw --model <local-model> "summarize in 5 bullets"

# Multi-step: research → draft
ask --raw --model sonar-pro "latest on X" > research.txt
cat research.txt | ask --model claude "write a summary paragraph"
```

---

## Large self-contained queries (headless cowpath)

**Problem:** Pipe patterns (`cat ... | ask`) rely on `stdin.isatty()` for stdin detection. In Claude Code's headless Bash tool context, this detection is unreliable and the command may hang.

**Also broken:** `cat <<'EOF' | ask "$(cat)"` — `$(cat)` is evaluated before the pipe is established, so it reads from the terminal and blocks.

**Reliable pattern for large prompts:**

```bash
# Step 1: write the query to a temp file (use the Write tool)
# Step 2: pass as a CLI argument via file substitution
ask --raw --model <model> "$(cat /tmp/query.txt)"
```

`$(cat /tmp/file)` reads from a file, not stdin — no `isatty()` ambiguity, works headlessly. The full prompt becomes a CLI argument.

**When to use which pattern:**

| Use case | Pattern |
|----------|---------|
| Content + short instruction | `cat file.txt \| ask "summarize this"` |
| Large self-contained prompt | Write to file → `ask "$(cat /tmp/query.txt)"` |
| Chain outputs | `ask --raw "..." \| next-command` |

---

## When to use which model

- **Perplexity** (`--model sonar` or `--model sonar-pro`) — web-grounded research, current events, citations (`--citations` to print sources). Use `sonar` for fast/cheap, `sonar-pro` for deeper research.
- **gpt-oss / open-weight models** — preferred for bulk/batch inference (cost, privacy). Routes through Headwater on AlphaBlue. **Never run via local Ollama on MacBook.**
- **Gemini / Imagen** — image generation, multimodal, long context
- **haiku / gpt-mini** — cheap cloud fallback when AlphaBlue is unavailable and cost matters

---

## Model aliases

Pass any alias via `--model <alias>`. Aliases are defined in `$BC/conduit-project/src/conduit/core/model/models/aliases.json`.

| Alias | Resolves to |
|-------|-------------|
| `banana` / `google-imagen` | `gemini-2.5-flash-image` |
| `claude` / `sonnet` | `claude-sonnet-4-6` |
| `deepseek` | `deepseek-chat` |
| `flash` | `gemini-3-flash-preview` |
| `gemini` | `gemini-2.5-flash` |
| `gemini3` | `gemini-3.1-pro-preview` |
| `gpt` / `gpt-mini` / `nano` | `gpt-5-mini` |
| `gpt3` | `gpt-3.5-turbo-0125` |
| `gpt5` | `gpt-5.1-2025-11-13` |
| `gpt-oss` | `gpt-oss:latest` |
| `groq` | `mixtral-8x7b-32768` |
| `haiku` | `claude-haiku-4-5-20251001` |
| `imagegen` | `dall-e-3` |
| `llama` | `llama3.1:latest` |
| `mistral` / `mistral-large` | `mistral-large-latest` |
| `mistral-medium` | `mistral-medium-2508` |
| `mistral-small` | `mistral-small-latest` |
| `ollama` | `mistral:latest` |
| `opus` | `claude-opus-4-6` |
| `qwen` | `qwen3:14b` |
| `tts` | `gemini-2.5-flash-preview-tts` |
| `quant` | `hf.co/unsloth/gpt-oss-20b-GGUF:Q8_0` |
