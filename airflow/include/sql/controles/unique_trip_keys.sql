-- An empty batch, a NULL key or a duplicate key blocks publication to MARTS.
SELECT
    COUNT(*) > 0 AS has_rows,
    COUNT(*) = COUNT(trip_sk) AS no_null_keys,
    COUNT(*) = COUNT(DISTINCT trip_sk) AS unique_keys
FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__ENRICHED
WHERE source_file_month = '{{ ds }}'::date;
