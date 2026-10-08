-- Prérequis : 01_infrastructure.sql et 02_roles.sql.
USE ROLE SECURITYADMIN;

CREATE USER IF NOT EXISTS AIRFLOW_SVC
    TYPE = SERVICE
    DEFAULT_ROLE = TRANSFORMER
    DEFAULT_WAREHOUSE = NYC_TAXI_WH
    DEFAULT_NAMESPACE = 'NYC_TAXI.RAW'
    COMMENT = 'Service user for the NYC Taxi ingestion and Airflow pipeline';

-- Le rôle par défaut ne constitue pas une attribution de droits.
GRANT ROLE TRANSFORMER TO USER AIRFLOW_SVC;

-- Enregistrer ensuite la clé publique selon docs/connexion_snowflake.md.
-- La clé privée ne doit jamais être insérée dans ce script.

SHOW GRANTS TO USER AIRFLOW_SVC;
DESCRIBE USER AIRFLOW_SVC;
