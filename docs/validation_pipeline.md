# Validation du pipeline Airflow — 9 octobre 2026

## Exécutions et volumes

Les trois exécutions historiques ont été relancées avec Clear et signalées comme
réussies après intégration des transformations et contrôles. La capture du run de
janvier montre 21 instances de tâche, les groupes STAGING, INTERMEDIATE et MARTS
réussis, et les versions v1 et v2 dans l'historique. Le rejeu a pris en compte la
nouvelle version sans sélection manuelle de version dans la fenêtre Clear.

![Pipeline complet de janvier](captures/airflow_janvier_pipeline_complet.png)

Le comptage Snowflake après les trois exécutions confirme :

| Mois source | Lignes FCT_TRIPS |
|---|---:|
| Janvier 2025 | 3 251 337 |
| Février 2025 | 3 305 246 |
| Mars 2025 | 3 825 795 |
| **Total** | **10 382 378** |

![Comptage par mois](captures/fct_trips_trois_mois.png)

Le total de clés distinctes est également de 10 382 378 et aucune clé n'est NULL.
Le volume total correspond au résultat attendu du brief.

![Unicité et complétude des clés](captures/fct_trips_cles.png)

## Portée de la validation

Ces résultats attestent du fonctionnement du pipeline complet sur les trois mois
et des volumes et clés de la table de faits. Ils ne constituent pas, à eux seuls,
une comparaison avant/après de toutes les tables sur un rejeu de février, ni une
preuve de blocage en situation d'échec volontaire d'un contrôle.

## Protocole de vérification du rejeu

1. Sans autre exécution active, exécuter
   [verify_pipeline_counts.sql](../snowflake/verify_pipeline_counts.sql) dans Snowflake
   et conserver le tableau des 18 volumes.
2. Dans Airflow, ouvrir le run `scheduled__2025-03-01...`, dont la date logique est
   le 1er février 2025. Utiliser Clear sur l'ensemble de ses tâches, y compris celles
   réussies, et attendre la fin de cette seule exécution.
3. Relancer la même requête et comparer chaque volume à celui d'avant le rejeu.

Les comptages sont calculés sur les données, pas lus dans un cache de métadonnées.
Ils incluent les vues STAGING. Les deux comparaisons de volumes et les preuves
visuelles permettent de distinguer une exécution réussie d'un rejeu vérifié.
