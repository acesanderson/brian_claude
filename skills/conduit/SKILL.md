---
name: conduit
description: Use when a task involves a non-Anthropic model — Perplexity for research, Gemini, local/open-weight models via Headwater, image generation, or any multi-model workflow. Conduit is the LLM runtime to reach for whenever the right tool is not a Claude model.
---

# conduit

Conduit is the LLM runtime. When a task calls for a non-Anthropic model — a search-grounded query via Perplexity, an open-weight model via Headwater, image generation, or multi-model chaining — conduit is how you invoke it.

**Rule:** Any time Claude Code delegates to a non-Claude model, it does so through conduit.

---

## Local model inference — HeadwaterClient ONLY

**Do NOT invoke Ollama on the local MacBook.** It saturates memory and disrupts other work.

All open-weight / Ollama-backed models (`gpt-oss:latest`, `llama`, `qwen`, `quant`, etc.) must go through **HeadwaterClient exclusively**. Never use `--local`, never call `ollama` directly from the MacBook.

### Headwater instances

| Instance | Host | GPU | VRAM | `host_alias` | Default? |
|----------|------|-----|------|--------------|----------|
| **Headwater** (AlphaBlue) | AlphaBlue | RTX 5090 | 32 GB + 128 GB RAM | `"headwater"` | **Yes** |
| **Bywater** (Caruana) | Caruana | RTX 4090 | 15 GB | `"bywater"` | No |

Both handle `gpt-oss:latest` and embeddings work. Use Headwater (AlphaBlue) by default. Switch to Bywater if AlphaBlue is under load or offline.

### Python — instantiating the client

```python
from headwater_client.client.headwater_client_async import HeadwaterAsyncClient

# Default — Headwater on AlphaBlue
async with HeadwaterAsyncClient() as client:
    ...

# Bywater on Caruana (explicit opt-in)
async with HeadwaterAsyncClient(host_alias="bywater") as client:
    ...
```

The client resolves the correct IP automatically via network context detection (VPN → LAN → WAN fallback). No hardcoded IPs needed.

### Observability methods

All HeadwaterClient instances (sync and async) expose:

```python
client.ping()               # bool — liveness check
client.get_status()         # StatusResponse — uptime, server name, version
client.get_logs_last(n=50)  # LogsLastResponse — last N records from ring buffer
client.get_routes()         # dict (router: parsed routes.yaml) or list (subserver: FastAPI routes)
```

Use these to triage failures: check router logs first (routing/backend errors), then subserver logs (service/model errors). See `CLAUDE.md` in the headwater repo for the full deploy + triage workflow.

### Batch inference via headwater_client

The `/conduit/batch` endpoint is the right path for multi-prompt structured inference. Use `BatchRequest` from `headwater_api.classes`:

```python
from headwater_api.classes import BatchRequest
from conduit.domain.request.generation_params import GenerationParams
from conduit.domain.config.conduit_options import ConduitOptions

params = GenerationParams(model="gpt-oss:latest", output_type="structured_response", response_model=MyModel, temperature=0.0)
options = ConduitOptions(project_name="my-project", include_history=False)
batch_req = BatchRequest(prompt_strings_list=prompts, params=params, options=options)

async with HeadwaterAsyncClient(host_alias="bywater") as client:  # or default
    resp = await client.conduit.query_batch(batch_req)
# resp.results is list[Conversation]; extract via conv.last.parsed
```

**Note:** If `output_type="structured_response"` fails on the server with an instructor-related error (version mismatch), fall back to `output_type="text"`, append a JSON schema instruction to the prompt, and parse the raw text response client-side.

If you need a cheap/fast model and Headwater is unavailable, use a cloud API (`haiku`, `gpt-mini`) instead.

---

## `conduit query` — query any LLM

**Claude Code always uses `conduit query` directly, never the `ask` alias.** `ask` is for interactive human use and always persists to the message store. `conduit query` does not persist by default.

```bash
conduit query "your query"
conduit query --model <model> "your query"
conduit query --raw --model <model> "query"   # plain stdout, safe to pipe
```

| Flag | Effect |
|------|--------|
| `--model <model>` | Override default model |
| `--local` | Route to local Ollama |
| `--raw` | Plain text output — no Rich rendering, pipeable |
| `--temperature <float>` | Set temperature |
| `--chat` | Include conversation history |
| `--append <text>` | Append extra text to query |
| `--citations` / `-C` | Print source citations (Perplexity sonar models; Google Gemini via grounding) |
| `--deep-research` / `-D` | Run Gemini Deep Research — comprehensive async report, 5–20 min turnaround. Implies `--citations`. |
| `--persist` | Persist this query to the message store (off by default for `conduit query`) |

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

When an agentic task calls for exploring a problem from multiple dimensions, write the prompts and call batch rather than making sequential `conduit query` calls:

```bash
# Write prompts to a temp file, then batch
conduit batch --json -m sonar-pro \
  "$(cat /tmp/prompt1.txt)" \
  "$(cat /tmp/prompt2.txt)" \
  "$(cat /tmp/prompt3.txt)" | jq -r '.[].response' | paste -sd '\n---\n'
```

---

## Classification at scale

For classifying large datasets, use `conduit batch` with a local model via Headwater. It's cheap, private, and runs all items in parallel.

**Simple case — label comes back as plain text:**

```bash
# Build one prompt per item (one per line) and batch classify
conduit batch -m gpt-oss --json -f prompts.txt \
  | jq -r '.[].response'
```

Craft each line in `prompts.txt` as a self-contained prompt:

```
Classify the following review as POSITIVE, NEGATIVE, or NEUTRAL. Reply with the label only.\n\nReview: "Great product, fast shipping."
Classify the following review as POSITIVE, NEGATIVE, or NEUTRAL. Reply with the label only.\n\nReview: "Arrived broken and support was useless."
```

Use `--json` to get structured output you can join back to your dataset by index.

**Structured output — when you need more than a label:**

The CLI doesn't support `response_model`, so write a Python script using the `BatchRequest` API (see "Batch inference via headwater_client" above). Pass a Pydantic model as `response_model` and set `output_type="structured_response"`. If instructor errors occur server-side, fall back to `output_type="text"` and parse JSON from the raw response.

**Model choice:**

- `gpt-oss` — default; fast, free, good for straightforward classification
- `qwen` / `llama` — alternatives if `gpt-oss` quality is insufficient
- Cloud models (`haiku`, `gpt-mini`) — only if Headwater is unavailable; incurs cost and latency

---

## POSIX pipe patterns

`--raw` outputs plain text to stdout. This is the key to chaining conduit into pipelines.

```bash
# Research → image generation
conduit query --raw --model sonar-pro "describe a coral reef at 30m depth" \
  | imagegen generate --model banana

# Summarize a large file before including in context
cat large_doc.md | conduit query --raw --model <local-model> "summarize in 5 bullets"

# Multi-step: research → draft
conduit query --raw --model sonar-pro "latest on X" > research.txt
cat research.txt | conduit query --model claude "write a summary paragraph"
```

---

## Large self-contained queries (headless cowpath)

**Problem:** Pipe patterns (`cat ... | conduit query`) rely on `stdin.isatty()` for stdin detection. In Claude Code's headless Bash tool context, this detection is unreliable and the command may hang.

**Also broken:** `cat <<'EOF' | conduit query "$(cat)"` — `$(cat)` is evaluated before the pipe is established, so it reads from the terminal and blocks.

**Reliable pattern for large prompts:**

```bash
# Step 1: write the query to a temp file (use the Write tool)
# Step 2: pass as a CLI argument via file substitution
conduit query --raw --model <model> "$(cat /tmp/query.txt)"
```

`$(cat /tmp/file)` reads from a file, not stdin — no `isatty()` ambiguity, works headlessly. The full prompt becomes a CLI argument.

**When to use which pattern:**

| Use case | Pattern |
|----------|---------|
| Content + short instruction | `cat file.txt \| conduit query "summarize this"` |
| Large self-contained prompt | Write to file → `conduit query "$(cat /tmp/query.txt)"` |
| Chain outputs | `conduit query --raw "..." \| next-command` |

---

## When to use which model

- **Perplexity** (`--model sonar` or `--model sonar-pro`) — web-grounded research, current events, citations (`--citations` to print sources). Use `sonar` for fast/cheap, `sonar-pro` for deeper research.
- **Gemini grounded** (`--model gemini3 --citations`) — alternative to Perplexity for web-grounded queries. Uses Google Search natively; good for queries where Google's index beats Perplexity.
- **Gemini Deep Research** (`--model gemini3 --deep-research`) — autonomous multi-step research agent; produces comprehensive cited reports. Use for substantive research questions, not quick lookups. **Turnaround: 5–20 minutes.**
- **gpt-oss / open-weight models** — preferred for bulk/batch inference (cost, privacy). Use HeadwaterClient exclusively — default to AlphaBlue (Headwater), opt into Caruana (Bywater) with `host_alias="bywater"`. **Never run via local Ollama on MacBook.**
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
