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

-- Après génération locale des clés, exécuter séparément cette instruction
-- en remplaçant le contenu par la clé PUBLIQUE, sans en-têtes ni sauts de ligne.
-- ALTER USER AIRFLOW_SVC SET RSA_PUBLIC_KEY = 'CLE_PUBLIQUE';
-- La clé privée ne doit jamais être insérée dans ce script.

SHOW GRANTS TO USER AIRFLOW_SVC;
DESCRIBE USER AIRFLOW_SVC;
