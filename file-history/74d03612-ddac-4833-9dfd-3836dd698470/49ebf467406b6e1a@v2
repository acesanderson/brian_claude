# Conduit WebSearch MCP Server

This MCP server exposes your Conduit web search and fetch tools to Claude Code.

## Tools Provided

### `web_search`
- Searches the web using Brave Search API
- Returns top 5 results with titles, URLs, and snippets
- **Requires:** `BRAVE_API_KEY` environment variable

### `fetch_url`
- Fetches URLs and converts them to clean Markdown
- Supports: HTML, PDF, Office docs (docx/pptx/xlsx)
- Automatically paginates long content (8000 chars per page)

## Setup Complete! ✓

The server is registered in `~/.claude/settings.json` and ready to use.

## Next Step

**Restart Claude Code** to activate the MCP server.

After restarting, you'll have access to:
- `web_search("query")` - Search the web
- `fetch_url("url", page=1)` - Fetch and convert URLs

## Testing

You can test the server manually:
```bash
cd ~/.claude/mcp-servers/conduit-websearch
uv run python server.py
```

## Environment Variables

Make sure `BRAVE_API_KEY` is set in your shell environment.
