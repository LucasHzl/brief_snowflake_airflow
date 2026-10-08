# Airflow — NYC Yellow Taxi

Projet local généré avec Astro CLI, basé sur l'image Astro Runtime
`astrocrpublic.azurecr.io/runtime:3.3-8`.

## Configuration

Docker doit être démarré. Le fichier local `.env` reprend le format de
[.env.example](.env.example) avec le compte Snowflake réel et le contenu de la
clé privée du compte AIRFLOW_SVC. Il définit la connexion `snowflake_nyc_taxi`.
Ce fichier est exclu de Git et du contexte de construction Docker ; il ne doit
jamais être publié. Les fichiers SQL fournis se trouvent dans `include/sql/`.

## Démarrer et arrêter

Depuis ce dossier :

```bash
astro dev start
```

Cette commande construit l'image avec les dépendances de requirements.txt et
lance les services locaux. Ouvrir l'adresse affichée par Astro dans le terminal.
Après modification du fichier `.env`, redémarrer avec `astro dev restart`.
Pour arrêter l'environnement en fin de session :

```bash
astro dev stop
```

## Vérifier la connexion Snowflake

Le DAG `check_snowflake_connection` contient une tâche SQL, `check_connection`.
Il n'est pas planifié automatiquement (`schedule=None`) et ne rejoue pas de
périodes historiques (`catchup=False`). Son lancement manuel via Trigger sert
uniquement à vérifier la connexion, sans charger ni modifier de données.

Activer le DAG, lancer une exécution puis ouvrir les logs de la tâche.
Vérifier les valeurs retournées : AIRFLOW_SVC, TRANSFORMER, NYC_TAXI_WH, NYC_TAXI.
Le statut success indique la réussite de la requête ; la lecture du résultat
confirme le contexte effectif. Les identifiants de connexion sont lus par Airflow,
ils ne figurent pas dans le DAG. Le contenu de la clé privée ne doit pas apparaître
dans les logs ni dans les captures de démonstration.

Le test local d'import des DAGs peut être exécuté dans l'environnement Astro :

```bash
astro dev pytest
```

Référence : [SQLExecuteQueryOperator](https://airflow.apache.org/docs/apache-airflow-providers-common-sql/stable/operators.html).

## Validation du 8 octobre 2026

Le DAG de connexion a été exécuté dans Airflow et a renvoyé
`AIRFLOW_SVC`, `TRANSFORMER`, `NYC_TAXI_WH`, `NYC_TAXI`.
Le premier lancement signalait une incompatibilité de pyarrow 25.0.1 avec le
connecteur Snowflake 4.8.0 sous Python 3.14.7. Le provider Snowflake 6.18.0
exige pyarrow >= 22 dans cet environnement et le connecteur impose pyarrow < 24.
La contrainte `pyarrow>=22.0.0,<24` est donc déclarée dans requirements.txt.
Après reconstruction et redémarrage avec `astro dev restart`, une nouvelle
exécution a réussi sans cet avertissement.

L'authentification par clé fonctionne depuis le conteneur. Ce test ne charge
aucun mois et ne valide pas encore l'orchestration mensuelle des données.

## Chargement mensuel RAW

Le DAG `nyc_taxi_monthly` est créé en pause. Son activation par l'interrupteur
permet au scheduler de créer les trois exécutions historiques, sans utiliser Trigger.
La période du projet est limitée aux dates logiques du 1er janvier au 1er mars 2025.
Un calendrier mensuel explicite (`CronDataIntervalTimetable`) associe chaque
exécution à un mois entier ; `catchup=True` rattrape les périodes historiques
et `max_active_runs=1` limite le traitement à un mois à la fois.

| Date logique | Intervalle des données, borne finale exclue | Fichier |
|---|---|---|
| 2025-01-01 | 2025-01-01 → 2025-02-01 | yellow_tripdata_2025-01.parquet |
| 2025-02-01 | 2025-02-01 → 2025-03-01 | yellow_tripdata_2025-02.parquet |
| 2025-03-01 | 2025-03-01 → 2025-04-01 | yellow_tripdata_2025-03.parquet |

Le mois du fichier provient de logical_date, jamais de la date du jour.
Un lancement manuel hors de ces trois mois est rejeté par le code.

Trois tâches s'enchaînent :

1. `wait_for_file` vérifie la disponibilité par HTTP HEAD. Une réponse 404 provoque
   une nouvelle vérification après 60 secondes, pendant au plus une heure.
   Le mode reschedule libère le worker entre les vérifications.
2. `download_and_stage` télécharge par morceaux dans un dossier temporaire,
   vérifie les marqueurs Parquet et exécute PUT à la racine du stage. Le transfert
   et le téléchargement partagent une tâche pour utiliser le même fichier local.
   Le dossier temporaire est supprimé à la sortie du bloc.
3. `copy_into_raw` exécute `include/sql/raw/load_yellow_trips.sql`, avec les options
   du chargement déjà validé, notamment FORCE = FALSE et les métadonnées sources.

Les erreurs de téléchargement ou de chargement peuvent être retentées deux fois,
avec 30 secondes entre les tentatives. Le capteur échoue sans relance automatique
s'il atteint son délai ou rencontre une erreur HTTP autre qu'un fichier absent.
Les limites du suivi de fichiers Snowflake restent celles de la
[procédure RAW](../docs/chargement_raw.md).

Après activation, vérifier trois exécutions réussies et les logs COPY de chacune.
Le total attendu après mars est 11 198 026 trajets RAW. Les tests d'import et de
calendrier vérifient localement les trois périodes et le nom de fichier SQL rendu ;
ils ne prouvent pas la réussite des chargements réels.


### Résultat du chargement des trois mois — 8 octobre 2026

Les trois exécutions planifiées ont terminé avec le statut success. Le contrôle
SQL des volumes dans Snowflake confirme les résultats suivants :

| Fichier source | Lignes RAW |
|---|---:|
| yellow_tripdata_2025-01.parquet | 3 475 226 |
| yellow_tripdata_2025-02.parquet | 3 577 543 |
| yellow_tripdata_2025-03.parquet | 4 145 257 |
| **Total** | **11 198 026** |

Janvier et février étaient déjà chargés avant ces exécutions ; leurs volumes
restent inchangés. Le rejeu n'a donc pas ajouté une deuxième copie de ces fichiers.

Dans cette version d'Airflow, les identifiants des exécutions planifiées et la
colonne « Exécuté après » affichent respectivement le 1er février, le 1er mars
et le 1er avril. Ces dates correspondent à la fin des intervalles. Les dates
logiques enregistrées sont bien le 1er janvier, le 1er février et le 1er mars :
le run affiché au 1er avril charge le fichier de mars.

Requêtes de vérification :

```sql
SELECT _source_file, COUNT(*) AS trip_count
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
GROUP BY _source_file
ORDER BY _source_file;

SELECT COUNT(*) AS total_trips
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA;
```
