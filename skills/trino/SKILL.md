# Trino

Query LinkedIn's internal Trino data warehouse. Use when asked to query, explore, or analyze internal LinkedIn data via Trino.

## Manifest

Schema knowledge lives in the `catalog` Postgres database on Caruana (`trino_tables` and `trino_queries` tables). This is a **schema manifest**: a curated, incrementally-built index of the warehouse. It is not exhaustive — only confirmed useful or confirmed broken entries are recorded.

**CLI:** `uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest <command>`

| Command | Purpose |
|---|---|
| `status` | Counts by status — quick orientation |
| `search <keyword>` | Keyword search on schema/table name and description |
| `search <keyword> --status accessible` | Filter to only accessible tables |
| `check hive <schema> <table>` | Full entry for a specific table |
| `upsert-table` | Add or update a table entry |
| `import-json` | One-time migration from `~/.local/state/trino/*.json` |

**Sync script** (discover new tables from Trino → Postgres):
```bash
TRINO_HOST=<host> uv run --directory ~/vibe/licensing-project/trino \
  python scripts/sync.py [--dry-run] [--catalog hive] [--schema <name>] [--describe]
```

## Protocol

### Decision cascade — follow in order, stop at first match

**Step 0 — Blacklist check**
Before anything else:
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest \
  check hive <schema> <table>
```
If result is `broken` or `restricted`, stop. Surface reason and DataHub URL to user. Do not query Trino.

**Step 1 — Prior queries**
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest \
  search "<plain-language intent keyword>" --status accessible
```
If a saved query matches the intent, adapt and re-run it. This is the highest-confidence path.

**Step 2 — Known accessible tables**
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest \
  search "<keyword>" --status accessible
```
If a known table clearly fits, query it directly using the stored column list.

**Step 3 — Manifest exploration (unconfirmed)**
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest \
  search "<keyword>"
```
If a relevant schema is in the manifest (any status), do targeted exploration within it via MCP: `SHOW TABLES LIKE '...'` → `DESCRIBE` → query. Update manifest after.

**Step 4 — Fresh search**
Triggered when no manifest entry matches, or user explicitly requests fresh search. Explore Trino broadly via MCP. Update manifest with findings before reporting results.

### Fresh search exploration pattern

```sql
-- Find schemas by keyword (always use LIKE — never omit it)
SHOW SCHEMAS FROM hive LIKE '%lil%'
SHOW SCHEMAS FROM hive LIKE '%learning%'

-- Find tables within a schema (always use LIKE filter on large schemas)
SHOW TABLES FROM hive.<schema> LIKE '%course%'

-- Describe before querying
DESCRIBE hive.<schema>.<table>

-- Sample to understand content
SELECT * FROM hive.<schema>.<table> LIMIT 5
```

**Hard limits on exploration:**
- Never `SHOW SCHEMAS FROM iceberg` without a LIKE filter — returns 2M+ chars, exceeds token limits
- Never `SHOW TABLES FROM hive.<schema>` on `metrics_temp_*` schemas without a LIKE filter — hundreds of timestamped temp tables

## Querying

**Default server:** `holdem`

**Catalog routing:**
- `hive` — analytics/metrics materialized views, personal schemas (`u_*`), production DB change captures
- `openhouse` — live production tables, often stricter ACLs
- `iceberg` — avoid broad exploration

**Date filtering:** Always filter on partition columns for large fact tables. For `fact_lil_video_session`, filter on `datepartition`.

**Performance:** Never `SELECT *` on large tables. Describe first, select only needed columns.

## Error handling

### Permission denied

1. Extract the DataHub URL from the error message
2. Surface it immediately:
   > "Access denied for `<schema>.<table>`. Request access at: `<datahub_url>`"
3. Add to manifest:
   ```bash
   uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest upsert-table \
     hive <schema> <table> --status restricted --error-type permission_denied \
     --datahub-url "<url>" --notes "Access request pending"
   ```
4. Do not retry

### UDF / view translation error

Error text contains: `not registered`, `Unknown function`, `Failed to translate Hive view`, `go/coral/unsupported`

1. Add to manifest as broken:
   ```bash
   uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest upsert-table \
     hive <schema> <table_or_*> --status broken --error-type udf_translation \
     --error-detail "<function name>"
   ```
2. If in a `metrics_temp_*` schema, use `table_name = *` — the UDF issue affects all views in the family
3. Do not retry — platform issue, not transient

### Table / file not found

```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest upsert-table \
  hive <schema> <table> --status broken --error-type table_not_found
```

## Manifest updates

Update immediately on discovery or failure — never defer.

After a successful query worth saving, add it to the manifest:
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest upsert-table \
  hive <schema> <table> --status accessible \
  --columns '[{"name":"col1","type":"varchar"},{"name":"col2","type":"bigint"}]' \
  --description "<grain, key columns, what it measures>"
```

After confirming a table is accessible, mark it:
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest upsert-table \
  hive <schema> <table> --status accessible --description "..." --notes "..."
```

## Known LiL data landscape

**Accessible:**
- `hive.foundation_tables_fact_lil_video_session_mp.fact_lil_video_session` — raw video sessions, course + user + enterprise grain. No contract_type. Filter on `datepartition`.

**Need access (pending DataHub request):**
- `hive.u_lildata.aps_lil_video` — likely pre-aggregated APS engagement by course
- `hive.u_lildata.lls_sop_lls_learning` — LLS SOP learning; likely has course + licensing metadata

**Broken (Coral UDF issues — do not attempt):**
- `metrics_temp_udp_prod_daily_dim_lil_cosmo_*` — all views use `dateToEpoch`, not registered in Trino
- `learning_mp.prod_lyndav2_course_flattened` — uses `extract_union`, not registered

**Priority gaps in manifest:**
- Course-level `contract_type` / `is_licensed` flag
- AL/week pre-aggregated by course
- Proficiency level per course
- Learning path membership per course
