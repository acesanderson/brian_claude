---
name: obsidian
description: "Comprehensive Obsidian vault skill. Use for any vault operation: creating or appending to notes, logging to daily notes, searching the vault, opening notes in the app, writing Obsidian Flavored Markdown (wikilinks, embeds, callouts, properties), using the obsidian CLI for live app operations (backlinks, property:set, tasks, plugin dev, eval), or any question about Siphon-based vault ingestion and vector retrieval. Trigger phrases: save to vault, add to my daily note, create an Obsidian note, log this to Obsidian, search my vault, open this note, wikilink, callout, obsidian property, backlinks, siphon ingest."
---

# Obsidian Vault

## The Vault Is Just a Directory

The Obsidian vault is at `$MORPHY` (`/Users/bianders/morphy`). It is a folder of plain `.md` files.

**For saving, reading, or copying notes — just use file tools directly.** No scripts, no `uv run`, no CLI needed.

```
Save a note   → Write the .md file to /Users/bianders/morphy/Note Title.md
Read a note   → Read /Users/bianders/morphy/Note Title.md
Search notes  → Grep across /Users/bianders/morphy/
Copy content  → Read source, Write destination
```

That's it. Reach for `vault.py` or the obsidian CLI only when you need features those tools actually provide (daily note append with date logic, live app operations, backlinks, etc.).

**After creating or saving any note, always open it in the Obsidian app:**

```bash
uv run ~/.claude/skills/obsidian/scripts/vault.py --vault /Users/bianders/morphy open "Note Title"
```

This is the only reliable method. `open -a Obsidian <path>` and the `obsidian://` URI scheme both fail silently on files outside the vault or when the app is already open.

---

## `vault.py` — When Plain File Ops Aren't Enough

For operations that benefit from structured logic (daily notes with auto-date, tag frontmatter injection, fuzzy note search):

```bash
SCRIPT=~/.claude/skills/obsidian/scripts/vault.py

# Create a note with frontmatter tags
uv run $SCRIPT --vault /Users/bianders/morphy create "Note Title" --tags tag1 tag2 --body "content"

# Append to a note (creates if absent)
uv run $SCRIPT --vault /Users/bianders/morphy append "Note Title" "Content to add"

# Append to today's daily note (auto-dates)
uv run $SCRIPT --vault /Users/bianders/morphy daily "Content to log"

# Search across all notes
uv run $SCRIPT --vault /Users/bianders/morphy search "query" --excerpt

# Open a note in the Obsidian app (macOS)
uv run $SCRIPT --vault /Users/bianders/morphy open "Note Title"
```

Note: `OBSIDIAN_VAULT` env var may not be set — pass `--vault /Users/bianders/morphy` explicitly.

---

## Vault Cleaning — REMOVED

> **Removed 2026-02-28.** A `rich_to_md.py` script was built and briefly included here. It used pure regex/structural passes (no LLM) to detect and convert rich-formatted text artifacts — centered headers, `•` unicode bullets, trailing whitespace — into standard Markdown. It supported single-file and vault-wide modes with an `--inplace` flag.
>
> It was removed because the vault-wide conversion silently corrupted ~1,000 notes. The heuristics (detecting "messy" files by unicode bullets or leading-space counts) were too broad — they matched notes that were intentionally formatted that way. The vault was restored from git without data loss, but the feature is too risky to keep around. If this is ever revisited, it needs per-file dry-run output with explicit approval before any in-place write, and tighter heuristics scoped to known-bad import patterns rather than general formatting signals.

---

## Live App Ops (obsidian CLI)

Requires Obsidian desktop app open and `obsidian` on PATH.

```bash
obsidian read file="My Note"
obsidian append file="My Note" content="New line"
obsidian search query="term" limit=10
obsidian daily:append content="- [ ] Task"
obsidian property:set name="status" value="done" file="My Note"
obsidian backlinks file="My Note"
obsidian tags sort=count counts
obsidian tasks daily todo
```

For the full CLI reference, see `references/cli-commands.md`.

---

## Mermaid Diagrams

If the user requests a Mermaid diagram (Gantt, flowchart, sequence, etc.):

1. Write the `.md` file to the vault (`/Users/bianders/morphy/<Note Title>.md`) with the diagram in a fenced `mermaid` code block
2. Open it with `vault.py open` (see above)
3. Tell the user: **switch to Reading View (`Cmd+E`) to see the rendered diagram**

Obsidian renders Mermaid natively in Reading View. The diagram will not render in Edit or Live Preview mode.

If the source file is outside the vault (e.g. in `~/licensing/context/`), copy it to the vault first, then open:

```bash
cp ~/licensing/context/some-diagram.md ~/morphy/some-diagram.md
uv run ~/.claude/skills/obsidian/scripts/vault.py --vault /Users/bianders/morphy open "some-diagram"
```

---

## Writing Obsidian Flavored Markdown

When creating or editing vault notes, use OFM syntax — not standard Markdown.
Key differences: `[[wikilinks]]` instead of `[text](path)`, `![[embeds]]`, callouts, and frontmatter properties.

See `references/markdown-syntax.md` for the full syntax reference.

---

## Siphon Integration

Siphon (`~/Brian_Code/siphon`) is operational. It ingests vault notes and stores them in Postgres with LLM enrichment for search and graph traversal.

Key vault-related commands:

```bash
# Ingest a single note (active ingestion)
siphon gulp path/to/note.md

# Bulk sync an entire vault (change-detected, incremental)
siphon sync --vault ~/morphy --concurrency 10

# Search ingested content
siphon query "topic"

# Walk wikilink graph from a note
siphon traverse "Note Title" --depth 2 --backlinks
```

See `references/siphon.md` for full CLI reference and architecture details.

---

## References

| File | Load when... |
|---|---|
| `references/markdown-syntax.md` | writing/editing notes, wikilinks, embeds, callouts, properties |
| `references/cli-commands.md` | using obsidian CLI (backlinks, property:set, plugin dev, eval) |
| `references/siphon.md` | questions about vault ingestion, vector retrieval, graph traversal |

---

## TBD: Blackglass (Vault HTTP Server + CLI)

**Blackglass** (`$BC/blackglass-project`) is a fully-built FastAPI server + Click CLI that exposes the Obsidian vault over HTTP for agentic access. When deployed it replaces the current mishmash of direct file ops, `vault.py`, and obsidian CLI calls with a single clean interface.

**Capabilities once live:**
- Note CRUD (`GET/POST/PUT/PATCH/DELETE /vault/notes/{path}`)
- Vault info: `/vault/files`, `/vault/tags`, `/vault/backlinks/{path}`, `/vault/periodic`
- Full-text search: `/vault/search?q=`
- Semantic search (pgvector + nomic-embed-text-v1.5): `/vault/semantic-search?q=`
- Incremental sync (git pull + re-index): `POST /vault/sync`
- CLI: `blackglass notes/vault/search` with `--json` flag for agent-friendly output

**Target host:** Botvinnik (172.16.0.3), port 8083

**HITL steps required to stand it up:**

1. **Push blackglass to GitHub** (was blocked by GitHub outage — do this first):
   ```bash
   cd $BC/blackglass-project && git push -u origin main
   ```

2. **Clone vault on botvinnik** (vault must exist at a known path, e.g. `~/services/vault`):
   ```bash
   ssh -p 2222 fishhouses@172.16.0.3 'git clone <vault-github-url> ~/services/vault'
   ```

3. **Clone blackglass on botvinnik:**
   ```bash
   ssh -p 2222 fishhouses@172.16.0.3 'git clone <blackglass-github-url> ~/services/blackglass'
   ```

4. **Pre-install dbclients on botvinnik** (path dep won't resolve remotely):
   ```bash
   ssh -p 2222 fishhouses@172.16.0.3 \
     'uv pip install --system git+https://github.com/acesanderson/database-clients.git'
   ```

5. **Create the `blackglass` database on Caruana:**
   ```bash
   ssh -p 2227 bianders@172.16.0.4 'createdb blackglass'
   ```

6. **Set env vars on botvinnik** (add to `~/.exports` or systemd unit):
   - `BLACKGLASS_VAULT_PATH=~/services/vault`
   - `BLACKGLASS_API_KEY=<chosen-key>`
   - `POSTGRES_PASSWORD=<caruana-postgres-password>`

7. **Create systemd service on botvinnik** and enable it:
   ```ini
   [Unit]
   Description=Blackglass vault server
   After=network.target

   [Service]
   User=fishhouses
   WorkingDirectory=/home/fishhouses/services/blackglass/src/blackglass/blackglass-server
   ExecStart=uv run uvicorn blackglass_server.main:app --host 0.0.0.0 --port 8083
   Restart=on-failure
   EnvironmentFile=/home/fishhouses/.env.blackglass

   [Install]
   WantedBy=multi-user.target
   ```

8. **Run initial sync** to index all vault notes:
   ```bash
   curl -X POST -H "X-API-Key: <key>" http://172.16.0.3:8083/vault/sync
   ```

9. **Install CLI on Petrosian** (MacBook):
   ```bash
   uv pip install -e $BC/blackglass-project/src/blackglass/blackglass-client
   ```

Once deployed, prefer `blackglass` CLI over direct file ops for any vault interaction that benefits from search or structured access.
