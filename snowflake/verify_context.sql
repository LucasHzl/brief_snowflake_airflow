-- Prérequis : 01_infrastructure.sql et 02_roles.sql.
-- Exécuter avec un utilisateur pouvant activer TRANSFORMER.
-- Vérifie le contexte et l'accès aux objets, pas encore les créations de tables.
USE ROLE TRANSFORMER;
USE SECONDARY ROLES NONE;

USE WAREHOUSE NYC_TAXI_WH;
USE DATABASE NYC_TAXI;
USE SCHEMA RAW;

-- Résultat attendu : TRANSFORMER / NYC_TAXI_WH / NYC_TAXI / RAW.
SELECT
    CURRENT_ROLE() AS role_actif,
    CURRENT_WAREHOUSE() AS warehouse_actif,
    CURRENT_DATABASE() AS base_active,
    CURRENT_SCHEMA() AS schema_actif;
