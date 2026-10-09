# Pipeline médaillon NYC Yellow Taxi — Snowflake et Airflow

Pipeline de données pour analyser la demande et les revenus des taxis jaunes de
New York, sur janvier, février et mars 2025. Les fichiers publics de la TLC sont
chargés dans Snowflake par Python et orchestrés par Airflow 3.

La question métier est : où et quand la demande est-elle la plus forte, et combien
rapporte un trajet selon la zone, l'heure et le mode de paiement ? Les données
couvrent les taxis jaunes publiés par la TLC, pas uniquement une flotte privée.

## Architecture

![Architecture du pipeline](docs/architecture.png)

| Élément | Rôle |
|---|---|
| Python / Requests | Télécharger les fichiers Parquet mensuels et le référentiel CSV des zones |
| Stage Snowflake | Recevoir les fichiers avant leur copie dans les tables |
| RAW | Conserver les valeurs sources, le nom du fichier et la date de chargement |
| STAGING | Renommer et typer les colonnes dans des vues |
| INTERMEDIATE | Identifier les trajets rejetés et enrichir les trajets valides |
| MARTS | Organiser faits, dimensions et agrégats pour l'analyse |
| Airflow | Planifier les périodes et ordonner les tâches exécutées dans Snowflake |

Le DAG automatise le chargement RAW et enchaîne les transformations des autres
couches avec trois contrôles bloquants. Les fichiers SQL fournis sont conservés
sans modification. Les résultats validés sont précisés ci-dessous.

## Prérequis

- Git, Docker démarré, Astro CLI, OpenSSL et uv.
- Python 3.12 pour les scripts d'ingestion locaux ; Airflow utilise le Python de son image Docker.
- Un compte Snowflake avec accès aux rôles d'administration SYSADMIN et SECURITYADMIN.
- Un terminal zsh sur macOS pour les commandes de saisie documentées.

## Installation et lancement

```bash
git clone git@github.com:LucasHzl/brief_snowflake_airflow.git
cd brief_snowflake_airflow
bash verifier_poste.sh
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r ingestion/requirements.txt
```

1. Suivre la [configuration Snowflake](docs/connexion_snowflake.md) : exécuter les
   scripts 01 à 03 et verify_context dans l'ordre indiqué, enregistrer la clé
   publique et tester la connexion du compte de service.
2. Exécuter `snowflake/04_raw.sql` dans Snowsight avec TRANSFORMER. Ce script crée
   les formats, le stage et les deux tables du [contrat RAW](CONTRAT_RAW.md).
3. Charger le référentiel des zones et un mois depuis le terminal :

```bash
read -r 'SNOWFLAKE_ACCOUNT?Identifiant de compte Snowflake : '
python ingestion/load_zones.py --account "$SNOWFLAKE_ACCOUNT"
python ingestion/load_month.py --account "$SNOWFLAKE_ACCOUNT" --month 2025-01
```

4. Suivre la [configuration Airflow](airflow/README.md) pour créer localement
   `airflow/.env` à partir du fichier d'exemple. Le compte Snowflake et la clé privée
   sont propres à l'installation ; ils ne sont pas publiés dans le dépôt.
5. Démarrer le projet déjà initialisé :

```bash
cd airflow
astro dev start
```

6. Exécuter le DAG `check_snowflake_connection`, puis activer `nyc_taxi_monthly`
   avec son interrupteur. Le scheduler rattrape janvier, février et mars 2025.
   Le mois vient de la date logique, jamais de la date du jour.

Les [procédures de chargement](docs/chargement_raw.md) détaillent le chargement
manuel, les options des scripts, les vérifications et les limites du rejeu.

## Choix techniques

- Un warehouse XS avec suspension automatique après 60 secondes limite le calcul inactif.
- Le rôle TRANSFORMER possède les droits de création et d'utilisation nécessaires
  dans NYC_TAXI. Les outils utilisent AIRFLOW_SVC avec une paire de clés.
- RAW accepte les valeurs manquantes et utilise FLOAT pour les nombres de trajets :
  les changements de types numériques entre mois sont acceptés sans arrondir les
  montants à l'entier. FLOAT est approché ; les transformations appliquent le typage métier.
- PUT dépose les fichiers à la racine du stage. COPY INTO renseigne `_source_file`
  et `_loaded_at`, conserve `FORCE = FALSE` et interrompt le chargement en cas d'erreur.
- `max_active_runs=1` traite un mois à la fois. Le téléchargement et PUT partagent
  une tâche afin de travailler sur le même fichier temporaire.
- La reconnaissance des fichiers déjà chargés empêche leur recopie lors des
  relances validées. Elle ne déduplique pas les trajets présents dans les sources
  et dépend des métadonnées de chargement Snowflake, conservées 64 jours.

## Résultats vérifiés

Chargements et comptages validés les 7 et 8 octobre 2026 :

| Données RAW | Lignes |
|---|---:|
| Janvier 2025 | 3 475 226 |
| Février 2025 | 3 577 543 |
| Mars 2025 | 4 145 257 |
| **Total trajets** | **11 198 026** |
| Référentiel des zones | 265 identifiants distincts |

Les trois exécutions Airflow ont réussi. Janvier et février, déjà présents avant
leur exécution dans Airflow, ont conservé leurs volumes. Ces résultats valident
l'ingestion RAW ; ils ne constituent pas une validation des transformations.

```sql
SELECT _source_file, COUNT(*) AS trip_count
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
GROUP BY _source_file
ORDER BY _source_file;
```

## Tests

Depuis la racine, dans l'environnement Python activé :

```bash
python -m unittest discover -s tests -v
```

Depuis `airflow/`, avec Docker disponible :

```bash
astro dev pytest
```

Les tests couvrent le traitement des réponses COPY, la découverte des DAGs,
les trois périodes mensuelles et le rendu des noms de fichiers. Ils complètent
les validations réelles dans Snowflake et Airflow.

## Organisation du dépôt

| Dossier ou document | Contenu |
|---|---|
| `snowflake/` | Infrastructure, droits, RAW et requêtes de vérification |
| `ingestion/` | Connexion, transfert et chargements paramétrés |
| `airflow/` | Projet Astro, DAGs, dépendances et tests |
| `airflow/include/sql/` | Transformations fournies et requête de chargement RAW |
| `docs/` | Fiche source, exploration et procédures techniques |
| `ETAPES.md` | Parcours et exigences par journée fournis avec le projet |
| `CONTRAT_RAW.md` | Noms et colonnes imposés aux tables sources |

La [fiche des trajets](docs/fiche_trajets.md) décrit les volumes, les colonnes,
les codes et les anomalies mesurées. Les SQL de transformation fournis sont
conservés sans modification.

## Paramètres des transformations fournies

Les fichiers SQL utilisent des expressions Jinja rendues par Airflow.
`ds` désigne la date logique au format AAAA-MM-JJ. Les paramètres attendus sont :

| Paramètre | Valeur |
|---|---|
| `max_trip_distance_miles` | 100 |
| `max_trip_duration_min` | 180 |
| `start_month` | 2025-01-01 |
| `end_month` | 2025-04-01 |

## Auteur

[LucasHzl](https://github.com/LucasHzl).

## Validation manuelle des transformations

Les [résultats de janvier](docs/validation_transformations_janvier.md) présentent
les rejets, le dédoublonnage, les volumes MARTS et le premier classement de demande.
Ces vérifications sont distinctes de la validation du DAG de chargement RAW.

## Validation du pipeline complet

Les [résultats du 9 octobre](docs/validation_pipeline.md) confirment les trois
exécutions complètes et 10 382 378 trajets dans FCT_TRIPS, avec autant de clés
distinctes et aucune clé manquante.
