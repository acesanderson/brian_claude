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
