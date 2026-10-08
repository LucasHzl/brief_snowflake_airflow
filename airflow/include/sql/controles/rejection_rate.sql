-- The monthly batch must exist and its rejection rate must stay below the threshold.
-- The threshold is a project monitoring choice, not a TLC rule.
SELECT
    COUNT(*) > 0 AS has_rows,
    COALESCE(
        100.0 * SUM(CASE WHEN rejection_reason IS NOT NULL THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0) <= {{ params.max_rejection_rate_pct }},
        FALSE
    ) AS rejection_rate_ok
FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
WHERE source_file_month = '{{ ds }}'::date;
