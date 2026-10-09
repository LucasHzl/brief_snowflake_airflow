-- Diagnostic en lecture seule : Midtown Center, 17 h, semaine, No charge.
USE ROLE TRANSFORMER;
USE WAREHOUSE NYC_TAXI_WH;

SELECT COUNT(*) AS trip_count,
       MIN(total_amount) AS min_amount,
       MEDIAN(total_amount) AS median_amount,
       MAX(total_amount) AS max_amount,
       ROUND(AVG(total_amount), 2) AS avg_amount
FROM NYC_TAXI.MARTS.FCT_TRIPS
WHERE source_file_month >= '2025-01-01'::date
  AND source_file_month < '2025-04-01'::date
  AND pickup_zone_key = 161 AND pickup_hour = 17
  AND is_weekend = FALSE AND payment_type_key = 3;

SELECT trip_sk, pickup_at, dropoff_at, vendor_key, trip_distance_miles,
       fare_amount, tip_amount, tolls_amount, surcharges_amount,
       total_amount, source_file
FROM NYC_TAXI.MARTS.FCT_TRIPS
WHERE source_file_month >= '2025-01-01'::date
  AND source_file_month < '2025-04-01'::date
  AND pickup_zone_key = 161 AND pickup_hour = 17
  AND is_weekend = FALSE AND payment_type_key = 3
ORDER BY total_amount DESC, trip_sk
LIMIT 20;
