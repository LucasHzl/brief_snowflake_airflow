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

## Commande mensuelle Python

[load_month.py](../ingestion/load_month.py) enchaîne le téléchargement, PUT,
COPY INTO et le comptage des lignes pour le fichier traité. Les objets RAW doivent
avoir été créés avant son exécution. Depuis la racine du dépôt :

```bash
source .venv/bin/activate
uv pip install -r ingestion/requirements.txt
read -r 'SNOWFLAKE_ACCOUNT?Identifiant de compte Snowflake : '
python ingestion/load_month.py --account "$SNOWFLAKE_ACCOUNT" --month 2025-01
```

Saisir l'identifiant réel du compte, obtenu via la requête de la procédure de
connexion. Le paramètre --month accepte un mois valide au format AAAA-MM.
--input-dir change le dossier de téléchargement ; --private-key change le chemin
de la clé privée. Par défaut, le script utilise data/input à la racine du dépôt
et ~/.ssh/snowflake/rsa_key.p8.

Un fichier local existant est réutilisé après vérification des marqueurs Parquet.
Cette vérification n'est pas une validation intégrale du contenu : COPY INTO
contrôle ensuite sa lecture et ses conversions. Un nouveau téléchargement est
écrit par morceaux dans un fichier .part, puis renommé une fois terminé.
En cas d'erreur ou d'interruption normale, le fichier temporaire est supprimé.
Après un arrêt brutal, un éventuel .part sera réécrit lors du prochain essai.
Le script est prévu pour une exécution à la fois par fichier local.

Le transfert réutilise la fonction upload_to_stage du script upload_file.py.
Le chargement conserve FORCE = FALSE et les options du SQL validé. Une réponse
LOAD_SKIPPED accompagnée de « File was loaded before. » est acceptée même lorsque
Snowflake renvoie errors_seen = 1. Le script vérifie ensuite qu'il existe des lignes
pour ce fichier et que _loaded_at est renseigné. Les autres erreurs restent bloquantes.

### Validation du script mensuel

Le 7 octobre 2026, exécution réelle sur janvier déjà chargé : réutilisation du
fichier local, transfert ignoré, chargement ignoré et 3 475 226 lignes confirmées
en RAW, avec fin d'exécution réussie. Ce test valide la relance sur janvier ;
il ne constitue pas un test réel du téléchargement d'un nouveau mois.

Les vérifications locales ont couvert le format du mois, la réutilisation du
fichier et le nettoyage après une interruption simulée du téléchargement.
Les tests de régression du traitement COPY s'exécutent sans accès à Snowflake :

```bash
python -m unittest discover -s tests -v
```

Cinq cas sont couverts : fichier déjà chargé, autre erreur de fichier ignoré,
chargement signalant des erreurs, absence de lignes RAW après une réponse ignorée,
et chargement réussi. Ces tests ne remplacent pas la validation réelle dans Snowflake.

## Référentiel des zones

[load_zones.py](../ingestion/load_zones.py) charge le référentiel TLC indépendamment
du pipeline mensuel et hors Airflow. Il télécharge le
[CSV public des zones](https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv)
s'il est absent de data/input, puis vérifie son en-tête, ses quatre champs par ligne,
ses 265 lignes et l'unicité de ses identifiants avant le transfert.

Depuis la racine du dépôt, dans l'environnement Python activé :

```bash
read -r 'SNOWFLAKE_ACCOUNT?Identifiant de compte Snowflake : '
python ingestion/load_zones.py --account "$SNOWFLAKE_ACCOUNT"
```

Le format CSV_FORMAT ignore l'en-tête et gère les guillemets. Le chargement associe
les quatre champs par position ($1 à $4), puis ajoute METADATA$FILENAME et
METADATA$START_SCAN_TIME. Les valeurs textuelles de la source telles que N/A ne
sont pas remplacées par une règle métier. FORCE = FALSE permet d'ignorer un fichier
reconnu comme déjà chargé, avec les mêmes limites que pour les trajets.

Relancer la même commande pour vérifier l'absence de doublons. Le script contrôle
la table entière : 265 lignes, 265 identifiants distincts et une traçabilité complète.
Le contrôle peut également être exécuté dans Snowsight avec
[verify_zones.sql](../snowflake/verify_zones.sql).

### Validation des zones du 7 octobre 2026

Les deux relances rapportées ont réutilisé le CSV local et obtenu SKIPPED pour PUT,
puis LOAD_SKIPPED avec « File was loaded before. » pour COPY INTO.
Les données étaient donc déjà présentes avant ces deux exécutions.

| Indicateur | Résultat après relance |
|---|---:|
| Lignes en RAW | 265 |
| Identifiants distincts | 265 |
| Métadonnées manquantes ou nom de fichier incorrect | 0 |
| Date minimale de chargement | 2026-10-07 07:24:16.539779 |
| Date maximale de chargement | 2026-10-07 07:24:16.539779 |

Les deux exécutions se terminent avec succès. Les dates sont des valeurs
TIMESTAMP_NTZ retranscrites sans déduction de fuseau horaire.

## Validation complémentaire du 7 octobre 2026

### Montants décimaux

La requête [verify_amounts.sql](../snowflake/verify_amounts.sql) a retourné dix
lignes de janvier comportant une partie décimale. Parmi les couples
(fare_amount, total_amount) affichés : (5.1, 12.12), (4.4, 11.75) et (19.1, 27.1).
Ces observations confirment la présence de décimales en RAW, sans constituer une
comparaison exhaustive avec les montants du fichier source.

### Téléchargement et premier chargement de février

Le script mensuel a été exécuté avec --month 2025-02. Contrairement à la relance
de janvier, cette exécution a téléchargé un nouveau fichier et ajouté ses lignes.

| Indicateur | Résultat |
|---|---|
| Fichier | yellow_tripdata_2025-02.parquet |
| Taille téléchargée | 60 343 086 octets |
| Statut PUT | UPLOADED |
| Statut COPY | LOADED |
| Lignes lues | 3 577 543 |
| Lignes chargées | 3 577 543 |
| Erreurs de chargement | 0 |
| Lignes vérifiées en RAW pour ce fichier | 3 577 543 |
| Première et dernière date de chargement affichées | 2026-10-07 07:48:34.432013 |
| Fin du script | Succès |

Le téléchargement réel, le transfert et le chargement d'un mois nouveau sont
ainsi validés. Le test de relance sans ajout de lignes reste celui effectué sur
janvier ; aucune relance de février n'est attestée par ces résultats.
