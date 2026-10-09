-- Exécuter les trois blocs séparément dans une même session Snowsight.
-- Bloc 1 : contexte et accès autorisé au périmètre du projet.
USE ROLE TRANSFORMER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE NYC_TAXI_WH;

SELECT CURRENT_ROLE() AS active_role,
       CURRENT_SECONDARY_ROLES() AS secondary_roles;

SELECT COUNT(*) AS valid_trips
FROM NYC_TAXI.MARTS.FCT_TRIPS;

-- Bloc 2 : droits attribués au rôle (conserver le résultat pour le rendu).
SHOW GRANTS TO ROLE TRANSFORMER;

-- Bloc 3 : tentative de lecture hors du périmètre NYC_TAXI, sans mutation.
-- Un refus est attendu avec les droits définis par 02_roles.sql.
-- Un résultat vide ou non vide sans erreur ne constitue pas un refus.
-- Si cette lecture réussit, examiner les droits hérités avant de conclure.
SELECT 1 AS access_probe
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
LIMIT 1;
