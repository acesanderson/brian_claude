-- Professional Certificate Interest Form submissions
-- Source: LinkedIn lead gen form (mcid = 7029095163159289857)
-- Server: holdem (Trino)
-- Refresh window: 270-day rolling (adjust interval as needed)
--
-- Run via execute_trino_query MCP tool in a Claude Code session.
-- Results are written to JSON then loaded via:
--   uv run --project ~/vibe/licensing-project/catalog python scripts/load_interest_form.py <json_file>

SELECT
    CAST(from_unixtime(created) AS date) AS date_submitted,
    member_id,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["firstname"]') AS varchar), '[\u001A\n\r]', ';') AS firstname,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["lastname"]')  AS varchar), '[\u001A\n\r]', ';') AS lastname,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["email"]')     AS varchar), '[\u001A\n\r]', ';') AS email,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["role"]')      AS varchar), '[\u001A\n\r]', ';') AS role,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["country"]')   AS varchar), '[\u001A\n\r]', ';') AS country,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["company"]')   AS varchar), '[\u001A\n\r]', ';') AS company,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["orgsize"]')   AS varchar), '[\u001A\n\r]', ';') AS orgsize,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["company-type"]')      AS varchar), '[\u001A\n\r]', ';') AS company_type,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["certificate-topic"]') AS varchar), '[\u001A\n\r]', ';') AS certificate_topic,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["other"]')             AS varchar), '[\u001A\n\r]', ';') AS other,
    regexp_replace(CAST(JSON_EXTRACT(form_data, '$["preferred-content"]') AS varchar), '[\u001A\n\r]', ';') AS preferred_content
FROM u_leadgen.lead_record
WHERE 1=1
  AND from_unixtime(created) >= current_date - INTERVAL '270' DAY
  AND mcid = 7029095163159289857
