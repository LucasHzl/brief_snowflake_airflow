-- Contrôle manuel ACCOUNTADMIN, distinct du pipeline.
-- Même borne de mesure que l'export de crédits du 9 octobre 2026.
USE ROLE ACCOUNTADMIN;
USE SECONDARY ROLES NONE;
USE WAREHOUSE NYC_TAXI_WH;
ALTER SESSION SET TIMEZONE = 'UTC';

SELECT
    COUNT(*) AS reported_intervals,
    ROUND(SUM(credits_used), 6) AS query_acceleration_credits,
    MIN(start_time) AS first_interval_utc,
    MAX(end_time) AS last_interval_end_utc,
    CURRENT_TIMESTAMP() AS measured_at_utc
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_ACCELERATION_HISTORY
WHERE warehouse_name = 'NYC_TAXI_WH'
  AND start_time >= '2026-10-06 00:00:00'::TIMESTAMP_LTZ
  AND start_time < '2026-10-09 09:42:02.951'::TIMESTAMP_LTZ;

-- Si aucun intervalle n'est retourné, SUM reste NULL : absence de consommation
-- publiée pour le périmètre, sous réserve du délai de publication (jusqu'à 3 h).
USE ROLE TRANSFORMER;
