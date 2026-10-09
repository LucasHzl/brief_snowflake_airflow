-- Independent classification from RAW, using the supplied rule priority.
-- Fixed scope and thresholds match the validated DAG: 2025 Q1, 180 min, 100 miles.
WITH classified AS (
 SELECT _source_file AS source_file,
 CASE
  WHEN tpep_pickup_datetime IS NULL OR tpep_dropoff_datetime IS NULL THEN 'timestamp_null'
  WHEN tpep_dropoff_datetime <= tpep_pickup_datetime THEN 'duration_non_positive'
  WHEN DATEDIFF('second', tpep_pickup_datetime, tpep_dropoff_datetime) > 10800 THEN 'duration_too_long'
  WHEN DATE_TRUNC('month', tpep_pickup_datetime) <> TO_DATE(REGEXP_SUBSTR(_source_file, '[0-9]{4}-[0-9]{2}'), 'YYYY-MM') THEN 'pickup_outside_file_month'
  WHEN trip_distance <= 0 OR trip_distance > 100 THEN 'distance_out_of_range'
  WHEN fare_amount < 0 OR total_amount <= 0 THEN 'amount_non_positive'
  WHEN pulocationid IS NULL OR dolocationid IS NULL THEN 'zone_null'
  ELSE 'valid'
 END AS status
 FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
 WHERE _source_file IN ('yellow_tripdata_2025-01.parquet', 'yellow_tripdata_2025-02.parquet', 'yellow_tripdata_2025-03.parquet')
), raw_counts AS (
 SELECT source_file, status, COUNT(*) AS raw_count FROM classified GROUP BY 1, 2
), mart_counts AS (
 SELECT source_file, status, nb_rows FROM NYC_TAXI.MARTS.MART_DATA_QUALITY
 WHERE source_file_month >= '2025-01-01'::date AND source_file_month < '2025-04-01'::date
)
SELECT COALESCE(r.source_file, m.source_file) AS source_file,
 COALESCE(r.status, m.status) AS status,
 r.raw_count, m.nb_rows AS mart_count,
 COALESCE(r.raw_count, 0) - COALESCE(m.nb_rows, 0) AS difference,
 r.raw_count IS NOT NULL AND m.nb_rows IS NOT NULL AND r.raw_count = m.nb_rows AS matches
FROM raw_counts r FULL OUTER JOIN mart_counts m
 ON r.source_file = m.source_file AND r.status = m.status
ORDER BY 1, 2;
