# Aquifer: Long-Term Token Optimization Layer

**What it is:** `~/Brian_Code/aquifer-project/` is a Python toolkit Brian built for
automated data collection and multi-model research. It is the eventual production layer
for the business_context/ knowledge base — a cheaper, schedulable replacement for the
Claude Code agent research workflows used to initially populate the knowledge base.

**The paradigm shift it enables:**
- **Phase 1 (now):** Use Claude Code agents + Captain MCP tools to establish research
  patterns — expensive but high-capability. Pave the cowpath.
- **Phase 2 (once patterns harden):** Translate validated patterns into aquifer scripts
  that run against local models (Ollama, etc.) on a schedule. Same output, fraction of
  the token cost.
- **Phase 3:** Aquifer becomes the background refresh layer (RSS monitoring, competitor
  earnings, Slack digests). Claude Code handles edge cases, novel research, and anything
  requiring Confluence/internal-source access.

**Aquifer's current capabilities:**
- `collect/rss` — RSS/Atom feed parsing for continuous monitoring
- `collect/youtube` — YouTube channel metadata into PostgreSQL
- `collect/podcasts` — Bulk podcast collection
- `research/brave` — Brave search + URL fetch
- `research/exa` — Exa semantic search
- `research/perplexity`, `research/openai`, `research/google_deep_research` — multi-model research
- `research/10k` — SEC EDGAR 10-K filing retrieval
- `research/snapshot.py` — fan-out orchestrator: takes structured question list, runs
  parallel async LLM calls via `conduit.batch`, aggregates to markdown
- `research/strategy/main.py` — multi-model: same query through Perplexity + Exa + OpenAI

**What aquifer currently lacks that this system provides:**
- Internal source access (Confluence, Slack, Google Docs) — only Claude Code + Captain MCP
- Hierarchical `business_context/` storage with domain summaries and staleness tracking
- The summarization hooks that roll up to the top-level omnibus summary

**When to reference aquifer:** When Brian asks to operationalize or schedule a research
workflow that has been validated through Claude Code agents. The signal is: "we've done
this 3+ times the expensive way and the output format is stable." That's when a pattern
is ready to be distilled into aquifer.
