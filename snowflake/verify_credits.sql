-- Contrôle administratif manuel, jamais exécuté par le DAG ou AIRFLOW_SVC.
-- Exécuter les instructions de contexte, puis chaque requête séparément.
USE ROLE ACCOUNTADMIN;
USE SECONDARY ROLES NONE;
USE WAREHOUSE NYC_TAXI_WH;
ALTER SESSION SET TIMEZONE = 'UTC';

-- Consommation publiée depuis le début du projet, par jour UTC.
-- Les dernières heures peuvent être absentes (3 h, jusqu'à 6 h pour cloud services).
-- Les crédits bruts ne sont pas les crédits facturés après ajustements.
SELECT
    TO_DATE(start_time) AS usage_date_utc,
    warehouse_name,
    ROUND(SUM(credits_used_compute), 6) AS compute_credits,
    ROUND(SUM(credits_used_cloud_services), 6) AS cloud_services_credits,
    ROUND(SUM(credits_used), 6) AS total_credits_before_adjustment,
    MAX(end_time) AS last_reported_hour_end_utc,
    CURRENT_TIMESTAMP() AS measured_at_utc
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE warehouse_name = 'NYC_TAXI_WH'
  AND start_time >= '2026-10-06 00:00:00'::TIMESTAMP_LTZ
  AND start_time < CURRENT_TIMESTAMP()
GROUP BY TO_DATE(start_time), warehouse_name
ORDER BY usage_date_utc;

-- Vérifier la taille XS et AUTO_SUSPEND = 60 sans les modifier.
SHOW WAREHOUSES LIKE 'NYC_TAXI_WH';

-- Après les mesures, revenir au rôle utilisé pour le projet.
USE ROLE TRANSFORMER;
