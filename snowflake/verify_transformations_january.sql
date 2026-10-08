-- Contrôles en lecture seule des transformations de janvier 2025.
USE ROLE TRANSFORMER;
USE WAREHOUSE NYC_TAXI_WH;

SELECT source_file_month, COUNT(*) AS trip_count
FROM NYC_TAXI.STAGING.STG_TLC__YELLOW_TRIPS
GROUP BY source_file_month ORDER BY source_file_month;

SELECT rejection_reason, COUNT(*) AS rejected_trips
FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
WHERE source_file_month = '2025-01-01'::date
  AND rejection_reason IS NOT NULL
GROUP BY rejection_reason ORDER BY rejected_trips DESC;

WITH flagged_counts AS (
    SELECT COUNT(*) AS total_trips,
           COUNT_IF(rejection_reason IS NOT NULL) AS rejected_trips,
           COUNT_IF(rejection_reason IS NULL) AS valid_before_dedup
    FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
    WHERE source_file_month = '2025-01-01'::date
), enriched_counts AS (
    SELECT COUNT(*) AS valid_after_dedup
    FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__ENRICHED
    WHERE source_file_month = '2025-01-01'::date
)
SELECT f.total_trips, f.rejected_trips, f.valid_before_dedup,
       f.valid_before_dedup - e.valid_after_dedup AS duplicates_removed,
       e.valid_after_dedup
FROM flagged_counts f CROSS JOIN enriched_counts e;

SELECT COUNT(*) AS total_trips,
       COUNT(DISTINCT trip_sk) AS unique_trip_keys,
       COUNT_IF(trip_sk IS NULL) AS missing_trip_keys
FROM NYC_TAXI.MARTS.FCT_TRIPS
WHERE source_file_month = '2025-01-01'::date;
