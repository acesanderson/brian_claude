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
| `search-queries <keyword>` | Search saved queries by question text or SQL |
| `check hive <schema> <table>` | Full entry for a specific table |
| `upsert-table` | Add or update a table entry |
| `delete-table hive <schema> <table>` | Remove an entry from the manifest |

**Sync script** (discover new tables from Trino → Postgres):
```bash
# Shallow crawl — seed ALL schema/table names as unconfirmed (no DESCRIBE, no access test)
uv run --directory ~/vibe/licensing-project/trino \
  python scripts/sync.py --crawl [--schema-like '%lil%'] [--dry-run]

# Deep sync — DESCRIBE and confirm access for known schemas
uv run --directory ~/vibe/licensing-project/trino \
  python scripts/sync.py [--schema <name>] [--describe] [--dry-run]
```

Run `--crawl` first to eliminate the discovery moat. Then `--describe` on schemas of interest to pull column lists and confirm access. These are separate passes by design — crawl is cheap (names only), describe is expensive (auth + round-trips).

## Protocol

### Decision cascade — follow in order, stop at first match

**Step 1 — Prior queries**
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest \
  search-queries "<plain-language intent keyword>"
```
If a saved query matches the intent, adapt and re-run it. This is the highest-confidence path.

**Step 2 — Known accessible tables**
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest \
  search "<keyword>" --status accessible
```
If a known table clearly fits, query it directly using the stored column list. (Blacklisted tables are excluded by the status filter — no separate check needed.)

**Step 3 — Manifest exploration (unconfirmed)**
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest \
  search "<keyword>"
```
If a relevant schema is in the manifest, check its status. If `broken` or `restricted`, stop and surface the reason to the user. Otherwise do targeted exploration via MCP: `SHOW TABLES LIKE '...'` → `DESCRIBE` → query. Update manifest after.

**Step 4 — Fresh search (live Trino via MCP)**
Triggered when no manifest entry matches, or user explicitly requests a fresh search.
Before issuing any MCP call against a specific schema or table, check the manifest:
```bash
uv run --directory ~/vibe/licensing-project/trino python -m trino_manifest \
  check hive <schema> <table_or_*>
```
If `broken` or `restricted`, stop. Otherwise explore broadly. Update manifest with findings before reporting results.

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
- `hive.foundation_tables_fact_lil_video_session_mp.fact_lil_video_session_private` — identical schema (32 cols), likely same table with ACL-based PII stripping.

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
