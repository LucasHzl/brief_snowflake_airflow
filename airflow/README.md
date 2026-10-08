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
