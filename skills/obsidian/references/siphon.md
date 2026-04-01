# Siphon Integration

> Status: operational. The pipeline, CLI, and Obsidian source type are all working.

## What Siphon Is

Siphon is a personal knowledge ingestion pipeline (`~/Brian_Code/siphon`) that parses content
from multiple source types, enriches it via LLM, and stores it in Postgres with embeddings for
vector retrieval.

## Pipeline Architecture

Four-stage pipeline with early-exit action types:

| Stage | Component | Input | Output |
|:---|:---|:---|:---|
| **1. Parse** | `SourceParser` | Raw string/URL | `SourceInfo` (canonical URI) |
| **2. Extract** | `ContentExtractor` | `SourceInfo` | `ContentData` (raw text + metadata) |
| **3. Enrich** | `ContentEnricher` | `ContentData` | `EnrichedData` (LLM summary/description) |
| **4. Persist** | `Repository` | `ProcessedContent` | PostgreSQL record |

Action types (via `--return-type`): `parse`, `extract`, `enrich`, `gulp` (full pipeline).

## Obsidian Source Type

The `OBSIDIAN` source type in `siphon-server/src/siphon_server/sources/obsidian/`:

- Accepts a `.md` file path inside a vault
- Detects vault root by walking up directories until `.obsidian/` is found
- Parses `[[wikilink]]` and `[[wikilink|alias]]` patterns
- Recursively fetches linked notes (cycle detection via visited set)
- Concatenates as structured markdown: `# title\n\ncontent\n\n---\n\n# linked-title\n\n...`
- URI scheme: `obsidian:///{sha256-of-path[:16]}`
- Metadata: `root_note`, `vault_root`, `note_count`

## CLI Reference

### Ingestion

```bash
# Ingest a single note (full pipeline, persists to DB)
siphon gulp path/to/note.md

# Bulk vault sync — client-side change detection, only processes new/modified notes
siphon sync --vault ~/morphy --concurrency 10
```

### Retrieval

```bash
# Full-text + vector search
siphon query "machine learning" --type obsidian

# Walk wikilink graph from a starting note
siphon traverse "Project Phoenix" --depth 2 --backlinks

# Access query history and retrieve by index
siphon results --history
siphon results --get 2 --return-type c
```

## Supported Source Types

| Type | Extraction Method |
|:---|:---|
| **YouTube** | `yt-dlp` metadata + `youtube-transcript-api` |
| **Article** | `readabilipy` + `markdownify` |
| **Doc** | `MarkItDown` (PDF, DOCX, TXT, CSV) |
| **Audio** | Whisper transcription + Pyannote diarization |
| **GitHub** | GitHub API tree traversal |
| **Obsidian** | Wikilink extraction + frontmatter parsing |
| **Email** | Gmail API (OAuth) |
| **Image** | Vision-LLM description |
| **Newsletter** | IMAP against Stalwart on nimzo (in progress) |

## Prerequisites

- Siphon server installed: `pip install siphon-api siphon-client siphon-server`
- PostgreSQL with `pgvector` extension running
- Environment variables:

| Variable | Description |
|:---|:---|
| `POSTGRES_USERNAME` | PostgreSQL user |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `HUGGINGFACEHUB_API_TOKEN` | For audio diarization |
| `YOUTUBE_API_KEY2` | Optional, advanced YouTube metadata |

## Configuration

`~/.config/siphon/config.toml`:

```toml
default_model = "gpt-4o"
log_level = 2
cache = true
vault = "~/morphy"
```

## Notes

- Siphon uses content-hash caching — re-ingesting an unchanged note is a no-op
- The `siphon sync` command uses client-side diffing so unchanged notes are skipped without a server round-trip
- Newsletter source is in progress (IMAP against Stalwart on nimzo VPS)
