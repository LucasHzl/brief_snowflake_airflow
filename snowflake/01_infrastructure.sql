-- Infrastructure du projet NYC Yellow Taxi.
-- Exécuter les instructions dans l'ordre dans Snowsight, avec un utilisateur
-- autorisé à utiliser SYSADMIN. Ce script crée les objets sans charger de données.
-- IF NOT EXISTS conserve les objets existants et ne modifie pas leurs paramètres.

USE ROLE SYSADMIN;

-- Calcul : taille XS, suspension après 60 secondes d'inactivité.
-- Le warehouse est créé suspendu et pourra reprendre à la demande.
CREATE WAREHOUSE IF NOT EXISTS NYC_TAXI_WH
    WAREHOUSE_TYPE = 'STANDARD'
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- Organisation des données : noms imposés par CONTRAT_RAW.md.
CREATE DATABASE IF NOT EXISTS NYC_TAXI;

CREATE SCHEMA IF NOT EXISTS NYC_TAXI.RAW;
CREATE SCHEMA IF NOT EXISTS NYC_TAXI.STAGING;
CREATE SCHEMA IF NOT EXISTS NYC_TAXI.INTERMEDIATE;
CREATE SCHEMA IF NOT EXISTS NYC_TAXI.MARTS;

-- Vérification du warehouse : X-Small, auto_suspend = 60,
-- auto_resume = true, owner = SYSADMIN.
SHOW WAREHOUSES LIKE 'NYC_TAXI_WH';

-- Vérifier la présence des quatre schémas du projet.
-- PUBLIC et INFORMATION_SCHEMA sont également créés automatiquement.
SHOW SCHEMAS IN DATABASE NYC_TAXI;
