# Chargement RAW — janvier 2025

## Préparation

La [procédure de connexion](connexion_snowflake.md) décrit les prérequis et
l'authentification du compte de service. Exécuter ensuite
[04_raw.sql](../snowflake/04_raw.sql) dans Snowsight : il crée les deux tables RAW,
les formats Parquet et CSV et le stage interne TLC_STAGE, sous le rôle TRANSFORMER.

Le fichier local est placé dans `data/input/yellow_tripdata_2025-01.parquet`.
Il est exclu de Git. Les types FLOAT des colonnes numériques de trajets évitent
l'arrondi à l'entier d'un NUMBER sans échelle et acceptent les variations de types
entre fichiers mensuels. FLOAT reste un type approché ; le typage métier est
réalisé par les transformations fournies. Les dates sont en TIMESTAMP_NTZ et les
valeurs sources manquantes restent autorisées dans RAW.

## Transfert vers le stage

Depuis la racine du dépôt, activer l'environnement et installer les dépendances :

```bash
source .venv/bin/activate
uv pip install -r ingestion/requirements.txt
```

Saisir l'identifiant du compte, obtenu avec la requête de la procédure de connexion :

```bash
read -r 'SNOWFLAKE_ACCOUNT?Identifiant Snowflake (ORGANISATION-COMPTE) : '
python ingestion/upload_file.py \
    --account "$SNOWFLAKE_ACCOUNT" \
    --file data/input/yellow_tripdata_2025-01.parquet
```

La commande de saisie ci-dessus utilise zsh, le terminal macOS du projet.
L'option --private-key permet de changer le chemin de clé ; par défaut,
le script utilise `~/.ssh/snowflake/rsa_key.p8`.

Le script envoie un fichier à la racine de `NYC_TAXI.RAW.TLC_STAGE` avec PUT,
sans compression gzip supplémentaire et avec OVERWRITE = FALSE. Il affiche
le statut retourné par Snowflake et ne charge aucune ligne de table.
Un statut SKIPPED doit être interprété avec le message retourné : il ne constitue
pas une vérification indépendante de l'identité du contenu local et distant.

Vérifier la présence du fichier dans Snowsight :

```sql
USE ROLE TRANSFORMER;
LIST @NYC_TAXI.RAW.TLC_STAGE;
```

## Chargement et relance

1. Exécuter [05_load_january.sql](../snowflake/05_load_january.sql).
2. Exécuter [verify_january.sql](../snowflake/verify_january.sql).
3. Relancer le même script de chargement, puis la vérification.

COPY INTO associe les colonnes par leur nom sans tenir compte de la casse.
Les métadonnées FILENAME et START_SCAN_TIME alimentent respectivement
_source_file et _loaded_at. Le chargement est annulé en cas d'erreur de lecture
ou de conversion ; les anomalies métier, comme les montants négatifs, sont conservées.

## Validation du 7 octobre 2026

| Vérification | Résultat |
|---|---|
| Fichier visible sur le stage | `tlc_stage/yellow_tripdata_2025-01.parquet` |
| Nom enregistré dans _source_file | `yellow_tripdata_2025-01.parquet` |
| Lignes après le premier chargement | 3 475 226 |
| Date minimale de chargement affichée | `2026-10-07 06:26:11.647` |
| Lignes après relance du même COPY INTO | 3 475 226 |
| Bornes de chargement après relance | Inchangées |

La date est retranscrite telle qu'affichée dans la colonne TIMESTAMP_NTZ ;
aucun fuseau horaire ne peut être déduit de cette valeur seule.

## Portée du test de relance

FORCE = FALSE permet d'ignorer un fichier inchangé déjà reconnu comme chargé
pour cette table. Ce test valide deux chargements successifs du même fichier
sur la même table, sans modification de celle-ci entre les deux exécutions.
Il ne déduplique pas les trajets présents plusieurs fois dans un fichier ou
répartis entre plusieurs fichiers.

Cette protection repose sur les métadonnées de chargement de Snowflake,
dont la conservation est limitée (64 jours). Elle ne constitue pas une garantie
permanente pour un fichier modifié, renommé ou après remise à zéro de la table.
FORCE = TRUE peut recharger les données et créer des doublons. DELETE ne réinitialise
pas ces métadonnées ; TRUNCATE les réinitialise et vide la table entière.

Références : [PUT](https://docs.snowflake.com/en/sql-reference/sql/put),
[COPY INTO](https://docs.snowflake.com/en/sql-reference/sql/copy-into-table).
