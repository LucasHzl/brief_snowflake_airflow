-- Contrôle du référentiel complet, après chargement puis après relance.
USE ROLE TRANSFORMER;
USE SECONDARY ROLES NONE;
USE WAREHOUSE NYC_TAXI_WH;

-- Résultat attendu : 265 lignes, 265 identifiants uniques, 0 métadonnée invalide.
SELECT
    COUNT(*) AS zone_count,
    COUNT(DISTINCT locationid) AS unique_ids,
    COUNT_IF(_source_file IS NULL
             OR _source_file <> 'taxi_zone_lookup.csv'
             OR _loaded_at IS NULL) AS invalid_metadata,
    MIN(_loaded_at) AS first_loaded_at,
    MAX(_loaded_at) AS last_loaded_at
FROM NYC_TAXI.RAW.TAXI_ZONE_LOOKUP;
