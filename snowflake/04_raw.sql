-- Prérequis : infrastructure, rôle TRANSFORMER et droits du contrat RAW.
-- Les objets doivent appartenir au rôle utilisé par les outils.
USE ROLE TRANSFORMER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE NYC_TAXI_WH;
USE DATABASE NYC_TAXI;
USE SCHEMA RAW;

CREATE FILE FORMAT IF NOT EXISTS NYC_TAXI.RAW.PARQUET_FORMAT
    TYPE = PARQUET
    USE_LOGICAL_TYPE = TRUE;

CREATE FILE FORMAT IF NOT EXISTS NYC_TAXI.RAW.CSV_FORMAT
    TYPE = CSV
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"';

-- Stage interne commun aux Parquet et au CSV ; préciser le format au chargement.
-- Les fichiers seront déposés à sa racine pour conserver le nom source attendu.
CREATE STAGE IF NOT EXISTS NYC_TAXI.RAW.TLC_STAGE;

-- FLOAT conserve les décimales des valeurs sources et accepte les variations
-- de types numériques entre les mois. Le typage métier est réalisé en STAGING.
-- Les colonnes sources restent nullables. Aucun filtrage n'est effectué en RAW.
CREATE TABLE IF NOT EXISTS NYC_TAXI.RAW.YELLOW_TRIPDATA (
    vendorid                 FLOAT,
    tpep_pickup_datetime     TIMESTAMP_NTZ,
    tpep_dropoff_datetime    TIMESTAMP_NTZ,
    passenger_count          FLOAT,
    trip_distance            FLOAT,
    ratecodeid               FLOAT,
    store_and_fwd_flag       VARCHAR,
    pulocationid             FLOAT,
    dolocationid             FLOAT,
    payment_type             FLOAT,
    fare_amount              FLOAT,
    extra                    FLOAT,
    mta_tax                  FLOAT,
    tip_amount               FLOAT,
    tolls_amount             FLOAT,
    improvement_surcharge    FLOAT,
    total_amount             FLOAT,
    congestion_surcharge     FLOAT,
    airport_fee              FLOAT,
    cbd_congestion_fee       FLOAT,
    _source_file             VARCHAR,
    _loaded_at               TIMESTAMP_NTZ
);

CREATE TABLE IF NOT EXISTS NYC_TAXI.RAW.TAXI_ZONE_LOOKUP (
    locationid      INTEGER,
    borough         VARCHAR,
    zone            VARCHAR,
    service_zone    VARCHAR,
    _source_file    VARCHAR,
    _loaded_at      TIMESTAMP_NTZ
);

-- Vérifier les types et les nombres de colonnes : 22 pour les trajets, 6 pour les zones.
DESCRIBE TABLE NYC_TAXI.RAW.YELLOW_TRIPDATA;
DESCRIBE TABLE NYC_TAXI.RAW.TAXI_ZONE_LOOKUP;

-- Vérifier la présence des objets et leur propriétaire : TRANSFORMER.
SHOW TABLES IN SCHEMA NYC_TAXI.RAW;
SHOW FILE FORMATS IN SCHEMA NYC_TAXI.RAW;
SHOW STAGES IN SCHEMA NYC_TAXI.RAW;
