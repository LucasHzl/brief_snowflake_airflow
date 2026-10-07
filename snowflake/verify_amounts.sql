-- Contrôle visuel de la présence de décimales en RAW.
-- L'échantillon ne prouve pas l'égalité de tous les montants avec la source.
USE ROLE TRANSFORMER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE NYC_TAXI_WH;

SELECT
    fare_amount,
    total_amount,
    _source_file
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
WHERE fare_amount <> TRUNC(fare_amount)
   OR total_amount <> TRUNC(total_amount)
LIMIT 10;
