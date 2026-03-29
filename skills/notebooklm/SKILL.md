---
name: notebooklm
description: Complete API for Google NotebookLM - full programmatic access including features not in the web UI. Create notebooks, add sources, generate all artifact types, download in multiple formats. Activates on explicit /notebooklm or intent like "create a podcast about X"
---

# NotebookLM

Programmatic access to Google NotebookLM via the `notebooklm` CLI (unofficial API).

## Prerequisites

```bash
pip install "notebooklm-py[browser]"
notebooklm login        # browser OAuth, one-time
notebooklm list --json  # verify auth works before anything else
```

## The Podcast Cowpath

This is the exact sequence that works end-to-end. Follow it precisely.

### 1. Create notebook, capture ID

```bash
NB=$(notebooklm create "Podcast: <topic>" --json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['notebook']['id'])")
```

**Never use `notebooklm use`** — it writes to a shared context file that parallel operations overwrite. Always pass `-n "$NB"` explicitly.

### 2. Find sources with brave-web-search (not add-research)

`source add-research` is unreliable in practice — it fails silently. Use the `brave-web-search` skill instead:

```bash
uv run --directory ~/.claude/skills/brave-web-search python conduit.py search "<topic query>"
```

This returns real URLs you can inspect and selectively add.

### 3. Add sources in parallel

```bash
notebooklm source add "https://url1.com" --notebook "$NB" --json 2>&1 &
notebooklm source add "https://url2.com" --notebook "$NB" --json 2>&1 &
notebooklm source add "https://url3.com" --notebook "$NB" --json 2>&1 &
wait
```

Capture the `source_id` from each JSON response for the next step.

### 4. Wait for indexing in parallel

```bash
notebooklm source wait <src_id1> -n "$NB" --timeout 120 2>&1 &
notebooklm source wait <src_id2> -n "$NB" --timeout 120 2>&1 &
notebooklm source wait <src_id3> -n "$NB" --timeout 120 2>&1 &
wait && echo "All sources ready"
```

Sources must be fully indexed before generation will work.

### 5. Generate

```bash
TASK=$(notebooklm generate audio "<description>" --format deep-dive \
  --notebook "$NB" --json \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['task_id'])")
```

Audio formats: `deep-dive` | `brief` | `critique` | `debate`
Audio lengths: `short` | `default` | `long`

### 6. Wait for completion — in the main thread, not a subagent

Subagents get Bash permission denied for this command. Do it directly:

```bash
notebooklm artifact wait "$TASK" -n "$NB" --timeout 1200 2>&1
```

Exit codes: `0` = done, `1` = error, `1` = timeout. If timeout, extend and re-run.

### 7. Download as .mp4, convert to .mp3 with ffmpeg

NotebookLM always delivers an MP4 container regardless of the extension you request.
Naming it `.mp3` produces a file that ffmpeg and most players will reject with "Header missing" errors.

```bash
mkdir -p ~/recordings
notebooklm download audio ~/recordings/<name>.mp4 -a "$TASK" -n "$NB"
ffmpeg -i ~/recordings/<name>.mp4 ~/recordings/<name>.mp3 -y
rm ~/recordings/<name>.mp4
```

Default save location: `~/recordings/`. Ask user if they want something different.

## Obsidian Vault Integration

Brian's vault is at `~/morphy`. Save reports, study guides, and chat transcripts there:

```bash
# Generate a study guide and save directly to vault
notebooklm generate report --format study-guide --notebook "$NB" --wait
notebooklm download report ~/morphy/<slug>.md -n "$NB"

# Save a Q&A session as a note, then retrieve and write to vault
notebooklm ask "<question>" -n "$NB" --save-as-note --note-title "<title>"
# or save entire conversation history:
notebooklm history --save --note-title "<title>" -n "$NB"
```

## All Generation Types

All generate commands accept: `-n` (notebook), `-s` (source filter, repeatable), `--language <code>`, `--retry N`, `--json`, `--wait/--no-wait`

| Type | Command | Key Options | True Output Format |
|------|---------|-------------|--------------------|
| Podcast | `generate audio` | `--format [deep-dive\|brief\|critique\|debate]`, `--length [short\|default\|long]` | MP4 container — convert with ffmpeg |
| Video | `generate video` | `--format [explainer\|brief]`, `--style [auto\|classic\|whiteboard\|kawaii\|anime\|watercolor\|retro-print\|heritage\|paper-craft]` | `.mp4` |
| Report | `generate report` | `--format [briefing-doc\|study-guide\|blog-post\|custom]`, `--append "<extra>"` | `.md` |
| Quiz | `generate quiz` | `--difficulty [easy\|medium\|hard]`, `--quantity [fewer\|standard\|more]` | `.json` / `.md` / `.html` |
| Flashcards | `generate flashcards` | same as quiz | `.json` / `.md` / `.html` |
| Slide deck | `generate slide-deck` | `--format [detailed\|presenter]`, `--length [default\|short]` | `.pdf` or `.pptx` |
| Infographic | `generate infographic` | `--orientation [landscape\|portrait\|square]`, `--detail [concise\|standard\|detailed]` | `.png` |
| Mind map | `generate mind-map` | (sync — instant, no `--wait` needed) | `.json` |
| Data table | `generate data-table "<desc>"` | description is required positional arg | `.csv` |
| Revise slide | `generate revise-slide "<desc>" --artifact <id> --slide <N>` | `--slide` 0-indexed, `--artifact` required | re-downloads parent deck |

## Download Options

```bash
notebooklm download <type> [OUTPUT_PATH] [OPTIONS]
```

**Selectors** (pick one): `--latest` (default) | `--earliest` | `--all <dir/>` | `--name "<fuzzy title>"` | `-a <artifact_id>`

**Flags**: `--dry-run` | `--force` | `--no-clobber` | `--json`

**Type-specific**:
- `slide-deck`: add `--format [pdf|pptx]`
- `quiz` / `flashcards`: add `--format [json|markdown|html]`

## Source Management

```bash
notebooklm source add "<url|file|text>" --notebook "$NB" --json   # type auto-detected
notebooklm source add-drive <file_id> --notebook "$NB"             # Google Drive
notebooklm source list --json -n "$NB"
notebooklm source get <src_id> -n "$NB"
notebooklm source fulltext <src_id> -n "$NB"                       # full indexed text
notebooklm source guide <src_id> -n "$NB"                          # AI summary + keywords
notebooklm source refresh <src_id> -n "$NB"                        # re-fetch URL/Drive
notebooklm source stale <src_id> -n "$NB"                          # check if outdated
notebooklm source rename <src_id> "<title>" -n "$NB"
notebooklm source delete <src_id> -n "$NB"
```

## Chat

```bash
notebooklm ask "<question>" -n "$NB"
notebooklm ask "<question>" -n "$NB" --json                         # includes source citations
notebooklm ask "<question>" -n "$NB" --save-as-note --note-title "<title>"
notebooklm ask "<question>" -n "$NB" -c <conversation_id>           # continue a conversation
notebooklm ask "<question>" -n "$NB" -s <src_id> -s <src_id2>       # limit to specific sources
notebooklm configure -n "$NB" --mode [default|learning-guide|concise|detailed]
notebooklm configure -n "$NB" --persona "<custom prompt, up to 10k chars>"
notebooklm configure -n "$NB" --response-length [default|longer|shorter]
notebooklm history -n "$NB"
notebooklm history -n "$NB" --save --note-title "<title>"
```

## Artifact Management

```bash
notebooklm artifact list -n "$NB" --json
notebooklm artifact list -n "$NB" --type [all|audio|video|slide-deck|quiz|flashcard|infographic|data-table|mind-map|report]
notebooklm artifact poll <artifact_id> -n "$NB"              # single non-blocking status check
notebooklm artifact wait <artifact_id> -n "$NB" --timeout 1200
notebooklm artifact suggestions -n "$NB"                     # AI-suggested report topics (undocumented gem)
notebooklm artifact export <artifact_id> -n "$NB" --title "<title>" --type [docs|sheets]
notebooklm artifact rename <artifact_id> "<title>" -n "$NB"
notebooklm artifact delete <artifact_id> -n "$NB"
```

## Notebook & Notes

```bash
notebooklm list --json
notebooklm create "<title>" --json
notebooklm rename <nb_id> "<new title>"
notebooklm summary -n "$NB"                     # AI-generated notebook insights + topics
notebooklm delete <nb_id>
notebooklm note list -n "$NB"
notebooklm note create "<content>" -t "<title>" -n "$NB"
notebooklm note get <note_id> -n "$NB"
notebooklm note save <note_id> "<content>" -n "$NB"
notebooklm note rename <note_id> "<title>" -n "$NB"
notebooklm note delete <note_id> -n "$NB"
```

## Sharing

```bash
notebooklm share status -n "$NB"
notebooklm share public --enable -n "$NB"
notebooklm share view-level [full-notebook|chat-only] -n "$NB"
notebooklm share add <email> --permission [editor|viewer] -n "$NB"
notebooklm share update <email> --permission [editor|viewer] -n "$NB"
notebooklm share remove <email> -n "$NB"
```

## Language (global — affects all notebooks)

```bash
notebooklm language list
notebooklm language get
notebooklm language set <code>             # e.g. ja, zh_Hans, es, fr, de, pt_BR
notebooklm generate audio --language ja    # per-command override
```

## Auth & Environment

```bash
notebooklm login
notebooklm auth check
notebooklm auth check --test               # full validation with network test
```

| Env var | Purpose |
|---------|---------|
| `NOTEBOOKLM_HOME` | Override `~/.notebooklm` (useful for parallel agents or multiple accounts) |
| `NOTEBOOKLM_AUTH_JSON` | Inline auth JSON for CI/CD (no file needed) |

## Reliability

**Always works:** notebook CRUD, source add/list/delete, chat, mind-map, report, data-table

**Frequently rate-limited (may fail):** audio, video, quiz, flashcards, infographic, slide-deck

If generation fails: wait 5–10 min and retry. Fall back to the NotebookLM web UI if repeated retries fail.

| Operation | Typical time | Timeout to use |
|-----------|-------------|----------------|
| Source indexing | 30s – 10 min | 600s |
| Mind map | instant | — |
| Report / data-table | 5 – 15 min | 900s |
| Quiz / flashcards | 5 – 15 min | 900s |
| Audio (podcast) | 10 – 20 min | 1200s |
| Video | 15 – 45 min | 2700s |

## Autonomy Rules

**Run without asking:** `list`, `status`, `auth check`, `source list/get/fulltext/guide/stale/wait`, `artifact list/poll/wait/suggestions`, `ask` (without `--save-as-note`), `note list/get`, `share status`, `language get/list`, `source add`, `create`

**Ask first:** `delete` (any), `generate *`, `download *`, `share public --enable`, `configure --persona`, `language set`, `ask --save-as-note`, `history --save`, `note create/save`
