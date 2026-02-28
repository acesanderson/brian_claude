# Siphon Integration (WIP)

> Status: planned. Siphon is not yet wired into this skill. This document records intent and design.

## What Siphon Is

Siphon is a personal knowledge ingestion pipeline (`~/Brian_Code/siphon`) that parses content
from multiple source types, enriches it via LLM, and stores it in Postgres with embeddings for
vector retrieval.

## Obsidian Source Type

Siphon has a native `OBSIDIAN` source type (`siphon-server/`) that:

- Accepts a `.md` file path inside a vault
- Detects the vault root by walking up directories until `.obsidian/` is found
- Parses `[[wikilink]]` and `[[wikilink|alias]]` patterns
- Recursively fetches linked notes (cycle detection via visited paths)
- Concatenates as structured markdown: `# title\n\ncontent\n\n---\n\n# linked-title\n\n...`
- URI scheme: `obsidian:///{sha256-of-path[:16]}`
- Metadata: `root_note`, `vault_root`, `note_count`

## Planned Capabilities

Once integrated, this skill will support:

### Ingest a single note (with wikilink traversal)

```bash
# planned interface — not yet implemented
uv run ~/.claude/skills/obsidian/scripts/siphon_ingest.py "Note Title"
# or
uv run ~/.claude/skills/obsidian/scripts/siphon_ingest.py --path path/to/note.md
```

### Vault-wide ingest

Batch ingest all notes in the vault (or a subfolder), respecting the Siphon cache so
re-ingesting unchanged notes is a no-op.

### Rich query (planned)

Once notes are in Postgres + vector store, Siphon will support:

- **Embeddings-based retrieval**: find notes semantically related to a query
- **Graph traversal**: follow wikilink relationships to surface connected context
- **Hybrid search**: combine keyword + vector + graph proximity

These queries will be surfaced through a `siphon query` CLI or API call.

## Prerequisites (when implemented)

- Siphon server running (or accessible Postgres instance with siphon schema)
- `SIPHON_API_URL` or direct DB credentials configured
- `OBSIDIAN_VAULT` env var set

## Implementation Notes

- The `rich_to_md` cleaning pass should be run before ingest — messy-rich notes will produce
  garbled embeddings
- Siphon uses standard cache behavior: same path hash returns cached result; pass
  `use_cache=False` to force re-ingest
- Notes that are purely daily logs may not benefit from vectorization; consider a tag-based
  filter (e.g. skip notes tagged `#daily`)
