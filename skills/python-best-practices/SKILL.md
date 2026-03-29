---
name: python-best-practices
description: Use when writing, reviewing, or modifying Python code, or when creating a new Python project, scaffolding a package, or setting up project files (pyproject.toml, .envrc, .python-version, py.typed).
---

# Python Best Practices

Apply when writing Python or scaffolding a Python project.

---

## Imports

Separate lines only. Three groups separated by blank lines: stdlib, third-party, local.

```python
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from my_package.models import User
```

### Lazy type imports

Always use `from __future__ import annotations` at the top of every file. Put type-only imports under `TYPE_CHECKING`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from my_package.config import Config
```

`Awaitable`, `Callable`, `Generator`, `Iterable`, `Iterator`, `Sequence` — always from `collections.abc`, never `typing`.

### Type hints

Modern builtins only. Never `List`, `Dict`, `Tuple`, `Optional` from `typing`:

```python
# correct
def process(items: list[str]) -> dict[str, int]: ...
def find(val: str | None = None) -> str | None: ...

# wrong
from typing import List, Dict, Optional
def process(items: List[str]) -> Dict[str, int]: ...
```

---

## Logging

**Library/module files:**
```python
import logging
logger = logging.getLogger(__name__)
```

**Entry points** (`if __name__ == "__main__"` or direct execution):
```python
import logging
import os

log_level = int(os.getenv("PYTHON_LOG_LEVEL", "2"))
levels = {1: logging.WARNING, 2: logging.INFO, 3: logging.DEBUG}
logging.basicConfig(level=levels.get(log_level, logging.INFO), format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)
```

Only configure `basicConfig` once, at the entry point. Never in imported modules.

---

## Naming

| Thing | Convention |
|---|---|
| functions, variables, methods | `snake_case` |
| classes | `PascalCase` |
| constants | `UPPER_SNAKE_CASE` |
| private | `_single_underscore` prefix |

Avoid single-letter names except in short loops/comprehensions.

---

## Code Structure

- Functions under 50 lines, single responsibility
- Return early to reduce nesting
- f-strings always (no `.format()` or `%`)
- Line length: 88 (ruff default)

```python
# preferred: early return
def validate(data: dict) -> bool:
    if not data:
        return False
    if "required" not in data:
        return False
    return True
```

---

## Type Hints

Required on all function signatures, including explicit `-> None`:

```python
def calculate(prices: list[float], tax: float = 0.08) -> float:
    return sum(prices) * (1 + tax)

def log_event(msg: str) -> None:
    logger.info(msg)
```

---

## Data Structures

- `dict` for simple structures with 3 or fewer keys
- `dataclass` for structured data with 4+ fields or complex behavior

```python
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
    role: str
```

---

## Docstrings

One-line docstring for all public functions and classes. Omit for private helpers and obvious getters.

```python
def fetch(url: str, timeout: int = 30) -> dict:
    """Fetch JSON from url with the given timeout."""
    ...
```

---

## Error Handling

Always specify exception types. Never bare `except:`.

```python
try:
    value = data["key"]
except KeyError as e:
    logger.error(f"Missing key: {e}")
    raise
```

---

## Anti-Patterns

- Bare `except:` — always name the exception
- Mutable default args: `def f(items=[])` — use `None` and set inside
- Wildcard imports: `from module import *`
- String concat in loops — use `join()` or f-strings
- `from typing import List, Dict, Tuple, Optional, Callable` — use builtins or `collections.abc`

---

## Dependencies

Prefer stdlib. Hand-roll simple utilities rather than adding a dep. Question every third-party import: "Could I write this in 10 lines?"

---

## Async

Keep it basic: coroutines and `asyncio.gather()`.

```python
async def main() -> None:
    results = await asyncio.gather(*[fetch(url) for url in urls])
```

---

## Testing

pytest, minimal scaffolding, no mocking. Test the primary API — what you'd show in README examples.

```python
def test_parse_config_loads_defaults():
    """Verify parse_config returns expected defaults."""
    config = parse_config("test_config.json")
    assert config.host == "localhost"
    assert config.port == 8080
```

- Name: `test_function_does_x_when_y`
- One test can verify multiple related assertions
- Inline test data, no conftest, minimal fixtures
- `-pdb -x` in pytest config: drops into debugger on first failure

---

## Project Structure

### Layout

Always `src/` layout, Hatchling build system:

```
my-project/
├── .claude/settings.local.json
├── .envrc
├── .python-version          # contains: 3.12
├── .venv/
├── pyproject.toml
├── uv.lock
├── src/
│   └── my_package/
│       ├── __init__.py      # empty or __all__ = []
│       └── py.typed         # empty PEP 561 marker
└── tests/
    └── test_basic.py
```

### pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
description = "Short description"
readme = "README.md"
requires-python = ">=3.12"
dependencies = []

[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]
sources = ["src"]
include = ["src/my_package/py.typed"]

[project.scripts]
my-tool = "my_package.cli:main"

[tool.pytest.ini_options]
addopts = "-v -s --tb=short --no-header --showlocals --pdb -x"
log_cli = true
log_cli_level = "INFO"

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["F", "E", "UP", "SIM", "ARG", "B", "RUF", "S102", "S103", "S108", "PERF", "FBT003"]
ignore = ["SIM118", "ARG001", "ARG002", "E501"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ARG", "FBT"]
"scripts/**/*.py" = ["ARG", "SIM"]

[tool.ruff.lint.isort]
known-first-party = ["my_package"]
force-sort-within-sections = true
split-on-trailing-comma = true
```

### Python version

Pin in two places: `.python-version` (contains `3.12`) and `requires-python = ">=3.12"` in pyproject.toml. Use 3.12 as floor; 3.13 for newer projects with no dep conflicts.

### Virtual environment

```bash
uv venv
uv sync   # or: uv pip install -e .
```

Never commit `.venv/`.

### .envrc

```bash
export PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [[ -z "$PROJECT_ROOT" ]]; then echo "direnv: error: no git root" >&2; exit 1; fi

export DEV="$PROJECT_ROOT/dev"
export DOCS="$PROJECT_ROOT/docs"
export TESTS="$PROJECT_ROOT/tests"

MAIN_PKG_DIR=$(find "$PROJECT_ROOT/src" -mindepth 1 -maxdepth 1 -type d | head -n 1)
[[ -d "$MAIN_PKG_DIR" ]] && export PACK="$MAIN_PKG_DIR"

deactivate 2>/dev/null || true
source .venv/bin/activate
```

### Local/sibling deps

```toml
[tool.uv.sources]
dbclients = { path = "../dbclients-project", editable = true }
```

### .claude/settings.local.json

```json
{ "permissions": { "allow": ["Bash(*)"] } }
```

Add to `.gitignore` — per-developer, not shared.

### .gitignore essentials

```
.venv/
__pycache__/
*.egg-info/
dist/
.env
.claude/settings.local.json
```

### Monorepo

Root `pyproject.toml` contains only pytest config. Each sub-package has its own full `pyproject.toml` and `.venv`.

---

## Output

Apply these standards silently. Do not announce compliance.
