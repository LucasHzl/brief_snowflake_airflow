-- Exploration locale de janvier 2025 (syntaxe read_parquet).
-- Exécuter depuis la racine du dépôt dans un moteur compatible.
-- Dans Parquet Visualizer, remplacer le chemin relatif par le chemin absolu
-- proposé par l'extension si nécessaire. Exécuter chaque requête séparément.
-- Ces requêtes ne sont pas destinées à Snowflake.

-- 1. Nombre de trajets.
SELECT COUNT(*) AS trip_count
FROM read_parquet('data/input/yellow_tripdata_2025-01.parquet');

-- 2. Échantillon de découverte, non représentatif de tout le fichier.
SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    passenger_count,
    trip_distance,
    fare_amount,
    total_amount
FROM read_parquet('data/input/yellow_tripdata_2025-01.parquet')
LIMIT 10;

-- 3. Valeurs manquantes et valeurs à examiner.
-- COUNT(colonne) ignore les NULL ; COUNT(*) compte toutes les lignes.
SELECT
    COUNT(*) AS total_trips,
    COUNT(*) - COUNT(passenger_count) AS missing_passenger_count,
    SUM(CASE WHEN passenger_count = 0 THEN 1 ELSE 0 END) AS zero_passenger_count,
    COUNT(*) - COUNT(trip_distance) AS missing_distance,
    SUM(CASE WHEN trip_distance <= 0 THEN 1 ELSE 0 END) AS non_positive_distance,
    SUM(CASE WHEN total_amount < 0 THEN 1 ELSE 0 END) AS negative_total_amount
FROM read_parquet('data/input/yellow_tripdata_2025-01.parquet');

-- 4. Période couverte et cohérence des dates.
-- Janvier est l'intervalle [2025-01-01, 2025-02-01[.
-- Les comparaisons ne comptent pas les NULL comme des anomalies temporelles.
SELECT
    MIN(tpep_pickup_datetime) AS earliest_pickup,
    MAX(tpep_pickup_datetime) AS latest_pickup,
    COUNT(*) - COUNT(tpep_pickup_datetime) AS missing_pickup,
    SUM(
        CASE
            WHEN tpep_pickup_datetime < TIMESTAMP '2025-01-01 00:00:00'
              OR tpep_pickup_datetime >= TIMESTAMP '2025-02-01 00:00:00'
            THEN 1 ELSE 0
        END
    ) AS pickups_outside_january,
    SUM(
        CASE
            WHEN tpep_dropoff_datetime <= tpep_pickup_datetime
            THEN 1 ELSE 0
        END
    ) AS non_positive_duration
FROM read_parquet('data/input/yellow_tripdata_2025-01.parquet');
