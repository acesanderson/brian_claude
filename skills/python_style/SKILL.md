---
name: python-style-guide
type: skill
description: Defines coding standards and best practices for Python development, including import conventions, logging setup, naming conventions, code structure, type hints, string formatting, data structures, dependency management, async code patterns, docstring usage, anti-patterns to avoid, error handling, comments, line length, and testing philosophy.
---

# Python Style Guide Skill

## When to Use This Skill
Apply this skill when writing, reviewing, or modifying Python code.

## Core Principles
- Prioritize readability and explicitness over cleverness
- Follow PEP 8 with specific project modifications below
- Minimize dependencies and complexity
- Hand-roll simple solutions rather than adding dependencies

## Import Standards

### Separate Lines
```python
# Correct
import os
import sys
from pathlib import Path

# Incorrect
import os, sys
```

### No Type Imports
Use built-in type hints directly (Python 3.9+):
```python
# Correct
def process_items(items: list[str]) -> dict[str, int]:
    pass

# Incorrect
from typing import List, Dict
def process_items(items: List[str]) -> Dict[str, int]:
    pass
```

### Import Order
1. Standard library
2. Third-party packages
3. Local application imports

Separate each group with a blank line.

## Logging Standards

### Library/Module Files
For importable modules and libraries:
```python
import logging
logger = logging.getLogger(__name__)
```

### Entry Point Files
For scripts with `if __name__ == "__main__":` or direct execution:
```python
import logging
import os

# Set up logging
log_level = int(os.getenv("PYTHON_LOG_LEVEL", "2"))  # Default to INFO
levels = {1: logging.WARNING, 2: logging.INFO, 3: logging.DEBUG}
logging.basicConfig(
    level=levels.get(log_level, logging.INFO),
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)
```

### Usage Pattern
- **Library files**: Just create logger instance, no configuration
- **Entry points**: Configure basicConfig once at top level
- **Rule**: Only configure logging in the entry point, never in imported modules

This ensures logging is configured once and controlled via `PYTHON_LOG_LEVEL` environment variable (1=WARNING, 2=INFO, 3=DEBUG).

## Naming Conventions
- `snake_case` for functions, variables, methods
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants
- Prefix private attributes with single underscore: `_private_var`
- Avoid single-letter variables except in comprehensions or short loops

## Code Structure

### Function Design
- Keep functions under 50 lines
- Single responsibility principle
- Return early to reduce nesting

```python
# Preferred
def validate_input(data: dict) -> bool:
    if not data:
        return False
    if "required_field" not in data:
        return False
    return True

# Avoid deep nesting
```

### Type Hints
Required for all function signatures, including explicit `None` returns:
```python
def calculate_total(prices: list[float], tax_rate: float = 0.08) -> float:
    return sum(prices) * (1 + tax_rate)

def log_message(msg: str) -> None:
    logger.info(msg)
```

## String Formatting
Always use f-strings:
```python
# Correct
name = "Alice"
greeting = f"Hello, {name}!"

# Avoid
greeting = "Hello, {}!".format(name)
greeting = "Hello, %s!" % name
```

## Data Structures
- Use dataclasses for structured data with 4+ fields or complex behavior
- Use dict for simple structures with 3 or fewer keys
- Prefer explicit structure over generic dicts when data shape is consistent

```python
from dataclasses import dataclass

# Use dataclass for structured data
@dataclass
class User:
    id: int
    name: str
    email: str
    role: str

# Use dict for simple structures
config = {"host": "localhost", "port": 8080, "debug": True}
```

## Dependencies
- Prefer hand-rolled solutions for simple tasks
- Only add dependencies if they solve complex problems in a one-liner
- Favor standard library over third-party packages when reasonable
- Question every import: "Could I write this in 10 lines?"

## Async Code
Keep async patterns simple and basic:
```python
import asyncio

async def fetch_data(url: str) -> dict:
    # Simple async operation
    pass

async def main() -> None:
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks)
```

Focus on basic coroutines and `asyncio.gather()` for concurrent operations.

## Docstrings
Use for public functions/classes. Keep concise:
```python
def fetch_data(url: str, timeout: int = 30) -> dict:
    """Fetch JSON data from URL with specified timeout."""
    pass
```

Omit docstrings for obvious private helpers or simple property getters.

## Anti-Patterns to Avoid
- Bare `except:` clauses (always specify exception types)
- Mutable default arguments (`def func(items=[]):`)
- String concatenation in loops (use `join()` or f-strings)
- Wildcard imports (`from module import *`)

## Error Handling
Be specific with exceptions:
```python
# Correct
try:
    value = data["key"]
except KeyError as e:
    logger.error(f"Missing key: {e}")
    raise

# Avoid
try:
    value = data["key"]
except:
    pass
```

## Comments
- Explain *why*, not *what*
- Avoid redundant comments that restate code
- Use comments sparingly—prefer self-documenting code

## Line Length
- Hard limit: 100 characters
- Preferred: 88 characters (Black formatter default)

## Testing Philosophy

### Approach
Pragmatic regression coverage for core workflows. Tests answer: "Does this project still work as advertised?"

### Framework
Use pytest with minimal scaffolding:
```python
def test_process_data_returns_valid_result():
    """Test that process_data handles basic input correctly."""
    input_data = {"key": "value"}
    result = process_data(input_data)
    assert result["status"] == "success"
    assert "processed" in result
```

### Key Principles
- **Regression-focused**: Test main paths only, not edge cases
- **Integration-biased**: Test real end-to-end behavior
- **Usage-driven**: Test what you'd show in README examples
- **Simple setup**: Inline test data, no conftest, minimal fixtures
- **Multiple assertions OK**: One test can verify related behaviors

### What to Test
Test the primary API—the most common use case for each script or function. If it's not worth documenting in usage examples, don't test it.

### Test Structure
- Naming: `test_function_does_x_when_y`
- Include docstrings explaining what's being tested
- Use simple `assert` statements
- No mocking (test real implementations)
- Organize by usage patterns, not by module structure

### Example
```python
def test_parse_config_loads_default_settings():
    """Verify parse_config returns expected defaults for basic input."""
    config_path = "test_config.json"
    config = parse_config(config_path)
    
    assert config.host == "localhost"
    assert config.port == 8080
    assert config.debug is False
```

## Output Format
When creating Python files, automatically apply these standards without announcing compliance with the style guide.
