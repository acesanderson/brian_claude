---
name: python-project-structure
type: skill
description: Defines Brian's standard Python project scaffolding and structure conventions, derived from conduit-project, siphon, headwater, and dbclients-project. Use when creating a new Python project, scaffolding a new package, or setting up project files (pyproject.toml, .envrc, .python-version, py.typed, tests/). Trigger phrases include "create a new Python project", "scaffold a project", "set up a new package", "initialize a Python project", "create the project structure".
---

# Python Project Structure

## When to Use
Apply when creating a new Python project or sub-package from scratch. This defines the exact scaffolding conventions derived from Brian's existing projects.

---

## Build System

Always **Hatchling**. Never setuptools.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Package Layout

Always `src/` layout. Declare the package path explicitly in the wheel target.

```
my-project/
├── .envrc
├── .python-version
├── .venv/              # created with: uv venv
├── pyproject.toml
├── uv.lock
├── src/
│   └── my_package/
│       ├── __init__.py
│       └── py.typed    # empty marker file
└── tests/
    └── test_basic.py
```

---

## pyproject.toml (single-package template)

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
dependencies = [
    "rich",
]

[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]
sources = ["src"]
include = ["src/my_package/py.typed"]

[project.scripts]
my-package = "my_package.cli:main"

[tool.uv.sources]
# Local editable deps from sibling projects:
# dbclients = { path = "../dbclients-project", editable = true }

[tool.pytest.ini_options]
addopts = "-v -s --tb=short --no-header --showlocals --pdb -x"
log_cli = true
log_cli_level = "INFO"

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "F", "E",
    "UP",
    "SIM",
    "ARG",
    "B",
    "RUF",
    "S102", "S103", "S108",
    "PERF",
    "FBT003",
]
ignore = [
    "SIM118",
    "ARG001", "ARG002",
    "E501",
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ARG", "FBT"]
"scripts/**/*.py" = ["ARG", "SIM"]

[tool.ruff.lint.isort]
known-first-party = ["my_package"]
force-sort-within-sections = true
split-on-trailing-comma = true
```

---

## Python Version

Pin in two places:

**`.python-version`** (at project root):
```
3.12
```

**`pyproject.toml`**:
```toml
requires-python = ">=3.12"
```

Use 3.12 as the floor. Use 3.13 for newer projects where no deps conflict.

---

## Virtual Environment

Created with `uv venv` at project root. Never committed (add `.venv/` to `.gitignore`).

```bash
uv venv          # creates .venv/
uv pip install -e .   # or: uv sync
```

---

## .envrc (single-package)

```bash
# .envrc

export PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [[ -z "$PROJECT_ROOT" ]]; then
  echo "direnv: error: could not find git root." >&2
  exit 1
fi

export DEV="$PROJECT_ROOT/dev"
export DOCS="$PROJECT_ROOT/docs"
export TESTS="$PROJECT_ROOT/tests"

MAIN_PKG_DIR=$(find "$PROJECT_ROOT/src" -mindepth 1 -maxdepth 1 -type d | head -n 1)
if [[ -d "$MAIN_PKG_DIR" ]]; then
    export PACK="$MAIN_PKG_DIR"
fi

deactivate 2>/dev/null || true
source .venv/bin/activate
```

---

## .envrc (monorepo root)

```bash
# .envrc

export PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [[ -z "$PROJECT_ROOT" ]]; then
  echo "direnv: error: could not find git root." >&2
  exit 1
fi

export DEV="$PROJECT_ROOT/dev"
export DOCS="$PROJECT_ROOT/docs"
export TESTS="$PROJECT_ROOT/tests"
export API="$PROJECT_ROOT/pkg-api/src/pkg_api"
export SERVER="$PROJECT_ROOT/pkg-server/src/pkg_server"
export CLIENT="$PROJECT_ROOT/pkg-client/src/pkg_client"

cdapi()    { cd "$PROJECT_ROOT/pkg-api"; }
cdserver() { cd "$PROJECT_ROOT/pkg-server"; }
cdclient() { cd "$PROJECT_ROOT/pkg-client"; }

export -f cdapi
export -f cdserver
export -f cdclient
```

Each sub-package also has its own minimal `.envrc`:
```bash
deactivate 2>/dev/null || true
source .venv/bin/activate
```

---

## Monorepo Structure

Root `pyproject.toml` contains **only** pytest config — no build config, no deps.

```
my-monorepo/
├── .envrc
├── .venv/
├── pyproject.toml       # pytest config only
├── pkg-api/
│   ├── .envrc
│   ├── pyproject.toml   # full build config
│   ├── src/pkg_api/
│   ├── tests/
│   └── uv.lock
├── pkg-server/
│   └── ...
└── pkg-client/
    └── ...
```

Root `pyproject.toml` for a monorepo:
```toml
[tool.pytest.ini_options]
markers = [
    "integration: Full pipeline integration tests",
    "slow: Tests that take >1 second",
]
addopts = ["-v", "--tb=short", "--strict-markers", "-ra"]
testpaths = ["tests"]
```

Sub-packages reference siblings via `uv.sources`:
```toml
[tool.uv.sources]
pkg_api = { path = "../pkg-api", editable = true }
```

---

## py.typed

Every package includes an empty `py.typed` marker at `src/<package>/py.typed`. This signals PEP 561 type support to type checkers.

```bash
touch src/my_package/py.typed
```

Always include it explicitly in the wheel:
```toml
[tool.hatch.build.targets.wheel]
include = ["src/my_package/py.typed"]
```

---

## __init__.py

Minimal. Either empty or just `__all__ = []`. No re-exports. Consumers use explicit import paths.

```python
__all__ = []
```

---

## CLI Entry Points

Defined in `[project.scripts]`. Each entry point points to a `main()` function:

```toml
[project.scripts]
my-tool = "my_package.cli:main"
```

---

## Tests

Single `tests/` directory at project root. Minimal `test_basic.py` at minimum.

```python
def test_import():
    import my_package
    assert my_package is not None
```

Pytest config (in `pyproject.toml`):
```toml
[tool.pytest.ini_options]
addopts = "-v -s --tb=short --no-header --showlocals --pdb -x"
log_cli = true
log_cli_level = "INFO"
```

The `-pdb -x` combination drops into debugger on the first failure. `--showlocals` prints all local variables in tracebacks.

---

## Local / Sibling Dependencies

Use `uv.sources` with editable paths for local packages in sibling directories:

```toml
[tool.uv.sources]
dbclients = { path = "../dbclients-project", editable = true }
conduit    = { path = "../conduit-project",  editable = true }
```

---

## .gitignore Essentials

```
.venv/
__pycache__/
*.egg-info/
dist/
.env
```
