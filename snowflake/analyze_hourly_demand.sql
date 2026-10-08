-- Classement sur toute la période actuellement présente dans le mart.
-- Lors de la validation manuelle documentée, FCT_TRIPS ne contenait que janvier.
USE ROLE TRANSFORMER;
USE WAREHOUSE NYC_TAXI_WH;

SELECT pickup_zone_name, pickup_borough, pickup_hour, is_weekend,
       nb_trips, nb_days, avg_trips_per_day, avg_revenue_per_trip
FROM NYC_TAXI.MARTS.MART_ZONE_HOURLY_DEMAND
ORDER BY nb_trips DESC, pickup_zone_key, pickup_hour, is_weekend
LIMIT 10;
