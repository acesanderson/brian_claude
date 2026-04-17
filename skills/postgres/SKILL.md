---
name: postgres
description: Use when querying PostgreSQL databases on Caruana via psql. Provides approved read-only commands, accessible databases, and connection patterns. Use when the user asks to query, explore, or inspect any of Brian's Postgres databases.
---

# PostgreSQL Access (Read-Only)

## CRITICAL: Read-Only User

The `psql` command on this machine connects as `claude_ro` — a read-only user with SELECT-only permissions.

**DO NOT attempt any write operations.** The following will be rejected by the database and should never be attempted:
- `INSERT`, `UPDATE`, `DELETE`, `TRUNCATE`
- `CREATE`, `DROP`, `ALTER`
- `GRANT`, `REVOKE`
- Any DDL or DML other than `SELECT`

This is enforced at the database level, not just by convention.

## Connection

The system `psql` wrapper handles host (`172.16.0.4`), port (`5432`), and user (`claude_ro`) automatically. Always specify the database:

```bash
psql -d {database}
```

Run a one-off query without entering the REPL:

```bash
psql -d {database} -c "SELECT ..."
```

**Caruana must be reachable** — either on the local network (`10.0.0.82`) or via WireGuard VPN (`172.16.0.4`). If connection fails, ask the user to check VPN.

## Accessible Databases

| Database         | Description |
|------------------|-------------|
| `annotations`    | Annotation data |
| `claude_history` | Claude conversation history |
| `conduit`        | Conduit LLM runtime data |
| `emails`         | Email data |
| `haddock`        | Haddock data |
| `kramer`         | Kramer data |
| `siphon`         | Main siphon data |

List all accessible databases (requires CONNECT on `postgres`):

```bash
psql -l
```

## Approved Commands

### Explore schema

```bash
# List all tables in a database
psql -d {database} -c "\dt"

# Describe a table (columns, types, constraints)
psql -d {database} -c "\d {table_name}"

# List schemas
psql -d {database} -c "\dn"

# List all tables across all schemas
psql -d {database} -c "\dt *.*"
```

### Query data

```bash
# Basic select
psql -d {database} -c "SELECT * FROM {table} LIMIT 10;"

# Row count
psql -d {database} -c "SELECT COUNT(*) FROM {table};"

# Filtered query
psql -d {database} -c "SELECT * FROM {table} WHERE {condition} LIMIT 50;"
```

### Formatting tips

```bash
# Expanded output (one column per line) — useful for wide rows
psql -d {database} -c "\x on" -c "SELECT * FROM {table} LIMIT 5;"

# CSV output
psql -d {database} --csv -c "SELECT * FROM {table} LIMIT 100;"
```

## Common Mistakes

- **Omitting `-d`**: psql will try to connect to a database named `claude_ro`, which does not exist
- **Attempting writes**: they will fail with `ERROR: permission denied` — do not retry with elevated privileges
- **Assuming connectivity**: always handle connection errors gracefully and tell the user if Caruana is unreachable

---

## Production / Scripted Usage

For any code that runs in scripts or agents, use the `dbclients` library instead of `psql`. It auto-handles host discovery (Caruana locally → WireGuard VPN → LAN fallback) and connects as `bianders`.

```python
from dbclients.clients.postgres import get_postgres_client
```

Requires `POSTGRES_PASSWORD` env var. Username defaults to `bianders`.

If the host is unreachable, a `RuntimeError` is raised — tell the user to check VPN.

**Rule of thumb:**
- `psql` + `claude_ro` → schema introspection and ad-hoc exploration
- `dbclients` + `bianders` → all scripted / agent code

### Client Types and When to Use Each

| Client type | Returns | Use when |
|-------------|---------|----------|
| `"context_db"` | context manager (new connection per call) | Sequential scripts; one operation at a time |
| `"sync"` | raw `psycopg2` connection | Single-threaded code where you manage the lifecycle manually |
| `"threaded"` | `psycopg2.pool.ThreadedConnectionPool` | Any concurrent code using `ThreadPoolExecutor` or threads |
| `"async"` | `asyncpg.Pool` (must be awaited) | `asyncio`-based concurrent code |

### `"context_db"` — Sequential scripts (recommended default)

Opens and closes a fresh connection each time. Safe, no leak risk, no pool overhead for low-volume work.

```python
context_db = get_postgres_client("context_db", dbname="siphon")
with context_db() as conn:
    cur = conn.cursor()
    cur.execute("SELECT * FROM my_table LIMIT 10")
    rows = cur.fetchall()
```

**Do not** share the yielded `conn` across threads — it is not thread-safe.

### `"threaded"` — Concurrent threaded code

Safe for `ThreadPoolExecutor` and any multi-threaded usage. Always call `putconn` even on error (use try/finally), and `closeall` when the pool is no longer needed.

```python
pool = get_postgres_client("threaded", dbname="siphon")

def worker(n):
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT %s", (n,))
        return cur.fetchone()[0]
    finally:
        pool.putconn(conn)

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    results = list(ex.map(worker, range(20)))

pool.closeall()
```

Default pool size: `minconn=1`, `maxconn=10`. Pass `maxconn` to override.

### `"async"` — asyncio concurrent code

Returns a coroutine that must be awaited. The pool manages concurrent `acquire`/`release` automatically.

```python
pool = await get_postgres_client("async", dbname="siphon")

async def worker(n):
    async with pool.acquire() as conn:
        return await conn.fetchval("SELECT $1", n)

results = await asyncio.gather(*[worker(i) for i in range(20)])
await pool.close()
```

### `"sync"` — manual single-connection use

Returns a bare `psycopg2` connection. You own the lifecycle. **Never share across threads.**

```python
conn = get_postgres_client("sync", dbname="siphon")
try:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM my_table")
    print(cur.fetchone())
finally:
    conn.close()
```

### Concurrency anti-patterns to avoid

- **Sharing a `sync` or `context_db` connection across threads** → race conditions guaranteed; psycopg2 connections are not thread-safe
- **Not calling `putconn` after `getconn`** → pool exhaustion; always use try/finally
- **Creating a new `threaded` pool per request** → defeats pooling; create once at startup and reuse
- **Not awaiting `get_postgres_client("async")`** → returns a coroutine object, not a pool
