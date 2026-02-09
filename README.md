This repository provides a suite of extensions for the Claude Code agent environment, consisting of Model Context Protocol (MCP) servers, lifecycle hooks, and task orchestration scripts. The system is designed to extend the agent's capabilities in web data retrieval, runtime security enforcement, and parallelized task execution.

### Architecture and Component Interaction

The codebase is organized into four primary functional domains:

1.  **Web Search and Content Retrieval (MCP):** The `conduit-websearch` server implements the Model Context Protocol to expose tools for searching the web via the Brave Search API and fetching remote resources. The retrieval pipeline uses a multi-stage conversion process: HTML is processed through `readabilipy` for content extraction and `markdownify` for Markdown conversion, while binary formats (PDF, DOCX, XLSX, PPTX) are processed via `markitdown`.
2.  **Runtime Intervention (Hookify & Security Guidance):** These components utilize Claude Code's hook system to intercept agent actions. `Hookify` implements a dynamic rule engine that parses YAML frontmatter from local Markdown files to evaluate conditions against tool inputs using regex and string comparison. `Security Guidance` provides a specialized implementation for detecting common vulnerabilities such as command injection in GitHub Actions or unsafe execution of `eval()` and `child_process.exec()`.
3.  **Parallel Orchestration (Batch Dispatch):** The `batch-dispatch` skill manages the concurrent execution of multiple Claude Code instances. It uses an asynchronous semaphore-controlled worker model to spawn isolated subprocesses, utilizing the agent's native sandboxing features by enforcing per-task working directories.
4.  **Extensibility Framework (Skill Creator):** A set of utilities for scaffolding, validating, and packaging modular "skills." This includes schema enforcement for skill metadata and zip-based packaging into `.skill` distribution files.

### Key Implementation Details

**Concurrency and Resource Management:**
The `batch_runner.py` script utilizes `asyncio.Semaphore` to limit concurrent worker processes (defaulting to 5). Each worker operates in a unique temporary directory to prevent filesystem collisions. Tasks are subject to a configurable timeout (default 600s) implemented via `asyncio.wait_for`, with explicit subprocess termination on timeout to prevent zombie processes.

**Data Flow and Content Processing:**
In the `fetch_url` tool, a MIME-type dispatcher determines the processing path. For HTML, the decision to use Readability is made to maximize information density for the LLM by stripping boilerplate navigation and ads. Content exceeding 8,000 characters is automatically paginated and includes a generated Table of Contents based on Markdown headers to allow the agent to navigate large documents efficiently.

**Error Handling and Stability:**
Plugin hooks (e.g., `pretooluse.py`) are designed with a fail-open philosophy. The scripts use exhaustive `try-except` blocks and typically exit with code 0 to ensure that a failure in the hook logic does not block the primary agent loop, except when a security rule explicitly triggers a block (exit code 2). State management for security warnings is persisted in `~/.claude/` using session-keyed JSON files to prevent redundant notifications within the same context.

**Technical Constraints and Decisions:**
*   **Markdown Conversion:** `markitdown` is used for binary files instead of simpler text extractors because it preserves structural elements (tables, lists) which are critical for LLM reasoning.
*   **Regex Caching:** The `RuleEngine` utilizes `functools.lru_cache` for compiled regex patterns to minimize overhead during high-frequency tool calls (e.g., `MultiEdit` operations).
*   **Sandboxing:** The `batch_runner` explicitly checks for the `/sandbox` auto-allow configuration. This decision was made because running parallel headless agents without filesystem restriction poses a high risk of accidental recursive file modifications.

### Operational Context and Limitations

*   **Brave API Dependency:** The search functionality requires a `BRAVE_API_KEY` environment variable.
*   **Dependency Management:** The `batch_runner` uses the inline script metadata format (PEP 723) for dependency specification, requiring a compatible runner like `uv` or manual installation of `jinja2`.
*   **Hook Pathing:** Plugins depend on the `CLAUDE_PLUGIN_ROOT` environment variable being correctly set by the host environment to resolve internal modules.
*   **MIME Sniffing:** If a server provides an incorrect or missing MIME type, the `fetch_url` tool falls back to inspecting the first 100 characters for an `<html` tag before defaulting to raw text.
