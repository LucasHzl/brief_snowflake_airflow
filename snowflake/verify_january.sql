-- Exécuter après le premier chargement, puis après sa relance à l'identique.
USE ROLE TRANSFORMER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE NYC_TAXI_WH;

-- Résultat attendu : un fichier, 3 475 226 lignes et des dates renseignées.
-- Après relance, le nombre de lignes et les bornes de chargement restent inchangés.
SELECT
    _source_file,
    COUNT(*) AS trip_count,
    MIN(_loaded_at) AS first_loaded_at,
    MAX(_loaded_at) AS last_loaded_at
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
GROUP BY _source_file;
