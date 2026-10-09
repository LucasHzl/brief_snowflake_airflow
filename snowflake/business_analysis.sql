-- Analyse des trajets valides de janvier à mars 2025.
-- Les montants enregistrés ne sont ni des bénéfices ni des encaissements vérifiés.
USE ROLE TRANSFORMER;
USE WAREHOUSE NYC_TAXI_WH;

-- 1. Top 10 zone de départ x heure x type de jour, classé par volume cumulé.
WITH trips AS (
    SELECT *
    FROM NYC_TAXI.MARTS.FCT_TRIPS
    WHERE source_file_month >= '2025-01-01'::date
      AND source_file_month < '2025-04-01'::date
), slots AS (
    SELECT
        pickup_zone_key,
        pickup_hour,
        is_weekend,
        COUNT(*) AS nb_trips,
        COUNT(DISTINCT pickup_date) AS nb_days,
        ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT pickup_date), 0), 1) AS avg_trips_per_observed_day,
        ROUND(AVG(total_amount), 2) AS avg_amount_per_trip_usd
    FROM trips
    GROUP BY pickup_zone_key, pickup_hour, is_weekend
), top_slots AS (
    SELECT *
    FROM slots
    ORDER BY nb_trips DESC, pickup_zone_key, pickup_hour, is_weekend
    LIMIT 10
)
SELECT
    s.pickup_zone_key,
    COALESCE(z.zone_name, 'Zone sans correspondance') AS pickup_zone_name,
    z.borough,
    s.pickup_hour,
    IFF(s.is_weekend, 'Week-end', 'Semaine') AS day_type,
    s.nb_trips,
    s.nb_days,
    s.avg_trips_per_observed_day,
    s.avg_amount_per_trip_usd
FROM top_slots s
LEFT JOIN NYC_TAXI.MARTS.DIM_ZONE z ON z.zone_key = s.pickup_zone_key
ORDER BY s.nb_trips DESC, s.pickup_zone_key, s.pickup_hour, s.is_weekend;

-- 2. Détail par mode de paiement des mêmes dix créneaux.
-- Le nombre de lignes peut dépasser dix : un créneau comporte plusieurs paiements.
WITH trips AS (
    SELECT *
    FROM NYC_TAXI.MARTS.FCT_TRIPS
    WHERE source_file_month >= '2025-01-01'::date
      AND source_file_month < '2025-04-01'::date
), slots AS (
    SELECT
        pickup_zone_key,
        pickup_hour,
        is_weekend,
        COUNT(*) AS nb_trips,
        COUNT(DISTINCT pickup_date) AS nb_days,
        ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT pickup_date), 0), 1) AS avg_trips_per_observed_day,
        ROUND(AVG(total_amount), 2) AS avg_amount_per_trip_usd
    FROM trips
    GROUP BY pickup_zone_key, pickup_hour, is_weekend
), top_slots AS (
    SELECT *
    FROM slots
    ORDER BY nb_trips DESC, pickup_zone_key, pickup_hour, is_weekend
    LIMIT 10
)
SELECT
    s.pickup_zone_key,
    COALESCE(z.zone_name, 'Zone sans correspondance') AS pickup_zone_name,
    s.pickup_hour,
    IFF(s.is_weekend, 'Week-end', 'Semaine') AS day_type,
    f.payment_type_key,
    COALESCE(p.payment_type_label, 'Paiement sans correspondance') AS payment_type,
    COUNT(*) AS nb_trips,
    ROUND(AVG(f.total_amount), 2) AS avg_amount_per_trip_usd
FROM trips f
JOIN top_slots s ON s.pickup_zone_key = f.pickup_zone_key
    AND s.pickup_hour = f.pickup_hour AND s.is_weekend = f.is_weekend
LEFT JOIN NYC_TAXI.MARTS.DIM_ZONE z ON z.zone_key = s.pickup_zone_key
LEFT JOIN NYC_TAXI.MARTS.DIM_PAYMENT_TYPE p ON p.payment_type_key = f.payment_type_key
GROUP BY s.pickup_zone_key, z.zone_name, s.pickup_hour, s.is_weekend,
         f.payment_type_key, p.payment_type_label, s.nb_trips
ORDER BY s.nb_trips DESC, s.pickup_zone_key, s.pickup_hour, s.is_weekend,
         nb_trips DESC, f.payment_type_key;
