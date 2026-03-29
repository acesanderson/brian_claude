# Trino — Programmatic Python Access

How to query LinkedIn's Trino (holdem) from Python scripts and CLIs, confirmed working
in `~/vibe/licensing-project/trino/scripts/sync.py`.

## Auth model

OAuth2 / Microsoft Entra ID (LNKDPROD SSO). On first run a browser tab opens for
one-step HITL login. The token is cached by the trino Python client via keyring so
subsequent runs are fully headless.

## Dependencies

```toml
# pyproject.toml
dependencies = [
    "trino",
    "keyring",
    "keyrings.alt",
]
```

## The critical env var

Must be set **before** any `import trino` or `import keyring`:

```python
import os
os.environ.setdefault("PYTHON_KEYRING_BACKEND", "keyrings.alt.file.PlaintextKeyring")
```

Without this, the trino client tries to use the macOS system keychain, which is
inaccessible from terminal contexts and causes silent auth failures.

## Connection

```python
import os
import trino
from trino.auth import OAuth2Authentication

# Must precede all trino/keyring imports
os.environ.setdefault("PYTHON_KEYRING_BACKEND", "keyrings.alt.file.PlaintextKeyring")


def get_trino_connection(catalog: str = "hive"):
    host = os.environ.get("TRINO_HOST", "trino-holdem.prod.linkedin.com")
    user = os.environ.get("TRINO_USER", os.environ.get("USER", ""))
    return trino.dbapi.connect(
        host=host,
        port=443,
        user=user,
        catalog=catalog,
        http_scheme="https",
        auth=OAuth2Authentication(),
    )
```

## Querying

```python
conn = get_trino_connection()
cursor = conn.cursor()
cursor.execute("SELECT course_id, title FROM hive.some_schema.some_table LIMIT 10")
rows = cursor.fetchall()
conn.close()
```

Results are plain tuples. Column names are available via `cursor.description`:

```python
cols = [d[0] for d in cursor.description]
records = [dict(zip(cols, row)) for row in rows]
```

## Env vars

| Var | Default | Notes |
|---|---|---|
| `TRINO_HOST` | `trino-holdem.prod.linkedin.com` | Override for non-holdem servers |
| `TRINO_USER` | `$USER` | Your LinkedIn LDAP username |
| `PYTHON_KEYRING_BACKEND` | *(must set manually)* | Set to `keyrings.alt.file.PlaintextKeyring` |

## First-run HITL flow

1. Script calls `conn.cursor()` or issues first query
2. Browser tab opens automatically to LNKDPROD SSO login
3. User completes login; browser tab can be closed
4. Token is written to keyring cache (`~/.local/share/python_keyring/` or similar)
5. All subsequent runs are headless until token expires

**The handshake may require 2-3 runs to stabilize.** The OAuth2 token exchange and
keyring write don't always complete cleanly on the first attempt — the script may
time out or throw an auth error even after the browser login appears to succeed.
If the first run fails after login, just re-run. By the second or third invocation
the cached token is in place and it works headlessly. Tell the user to expect this
on initial setup.

## Minimal self-contained script template

```python
#!/usr/bin/env python
# /// script
# dependencies = ["trino", "keyring", "keyrings.alt"]
# ///
from __future__ import annotations

import os
os.environ.setdefault("PYTHON_KEYRING_BACKEND", "keyrings.alt.file.PlaintextKeyring")

import trino
from trino.auth import OAuth2Authentication


def main() -> None:
    conn = trino.dbapi.connect(
        host=os.environ.get("TRINO_HOST", "trino-holdem.prod.linkedin.com"),
        port=443,
        user=os.environ.get("TRINO_USER", os.environ.get("USER", "")),
        catalog="hive",
        http_scheme="https",
        auth=OAuth2Authentication(),
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print(cur.fetchall())
    conn.close()


if __name__ == "__main__":
    main()
```

Run with: `uv run script.py` (deps in `# /// script` block are installed ephemerally).

## Source

`~/vibe/licensing-project/trino/scripts/sync.py` — `_build_connection()` is the
canonical implementation. If auth behavior changes, check there first.
