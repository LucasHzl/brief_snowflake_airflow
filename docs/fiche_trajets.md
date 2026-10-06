# Fiche source — NYC Yellow Taxi, janvier 2025

## Identité

| Rubrique | Réponse |
|---|---|
| Source | Yellow Taxi Trip Records |
| Diffuseur | New York City Taxi & Limousine Commission (TLC) ; données transmises par les fournisseurs technologiques TPEP |
| Catalogue | [TLC Trip Record Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page) |
| Fichier | [Janvier 2025 — Parquet](https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet) |
| Accès | Public, sans authentification |
| Format | Parquet |
| Publication | Mensuelle ; délai habituel de deux mois annoncé par la TLC, pas une date de publication mesurée pour ce fichier |
| Unité d'observation | Une ligne correspond à un trajet enregistré |
| Période nominale | Janvier 2025 |

La TLC ne garantit pas l'exactitude des données transmises. Le fichier représente
les trajets publiés pour les taxis jaunes de New York, pas uniquement la flotte
Hudson Cab Partners.

## Volume mesuré et méthode

Exploration réalisée le 6 octobre 2026 avec **Parquet Visualizer de Lucien Martijn**,
dans VS Code : onglet Schema pour la structure et onglet Query pour les comptages.

| Fichier | Taille exacte | Lignes | Colonnes |
|---|---:|---:|---:|
| `yellow_tripdata_2025-01.parquet` | 59 158 238 octets | 3 475 226 | 20 |

Emplacement local : `data/input/yellow_tripdata_2025-01.parquet`. Les fichiers
Parquet sont exclus du dépôt par `.gitignore`.

Les quatre requêtes sont conservées dans [exploration_janvier.sql](exploration_janvier.sql).
Dans l'extension, utiliser le chemin absolu proposé à l'ouverture du fichier
à la place du chemin relatif. Exécuter les requêtes séparément. La taille exacte
a été relevée sur le fichier local ; sur macOS, elle se reproduit depuis la racine
avec :

```bash
stat -f %z data/input/yellow_tripdata_2025-01.parquet
```

## Colonnes

Types relevés dans l'onglet Schema. Toutes les colonnes autorisent `NULL` ; cela
ne signifie pas qu'elles contiennent toutes des valeurs manquantes.
Les exemples ci-dessous sont **illustratifs**, sauf ceux repris dans les mesures
plus bas ; ils ne constituent pas un relevé des valeurs distinctes.
Les significations sont synthétisées d'après le
[dictionnaire TLC du 18 mars 2025](https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf).

| Colonne | Type affiché | Signification | Exemple illustratif |
|---|---|---|---|
| `VendorID` | Int32 | Fournisseur TPEP | `1` |
| `tpep_pickup_datetime` | Timestamp | Activation du compteur | `2025-01-01 00:18:38` |
| `tpep_dropoff_datetime` | Timestamp | Arrêt du compteur | `2025-01-01 00:26:59` |
| `passenger_count` | Int64 | Passagers | `1` |
| `trip_distance` | Float64 | Distance en miles | `1.6` |
| `RatecodeID` | Int64 | Tarif final appliqué | `1` |
| `store_and_fwd_flag` | String | Transmission différée | `N` |
| `PULocationID` | Int32 | Zone de départ | `161` |
| `DOLocationID` | Int32 | Zone d'arrivée | `162` |
| `payment_type` | Int64 | Mode de paiement | `1` |
| `fare_amount` | Float64 | Tarif au compteur, USD | `10.0` |
| `extra` | Float64 | Suppléments, USD | `1.0` |
| `mta_tax` | Float64 | Taxe MTA, USD | `0.5` |
| `tip_amount` | Float64 | Pourboire enregistré, USD | `2.0` |
| `tolls_amount` | Float64 | Péages, USD | `0.0` |
| `improvement_surcharge` | Float64 | Surcharge d'amélioration, USD | `1.0` |
| `total_amount` | Float64 | Total facturé enregistré, USD | `18.0` |
| `congestion_surcharge` | Float64 | Surcharge congestion NYS, USD | `2.5` |
| `Airport_fee` | Float64 | Prise en charge JFK/LaGuardia, USD | `0.0` |
| `cbd_congestion_fee` | Float64 | Redevance Congestion Relief Zone, USD | `0.0` |

Les pourboires en espèces sont absents de `tip_amount` et de `total_amount`.
Un montant facturé ne mesure donc pas à lui seul la rentabilité d'un trajet.
Les types affichés décrivent ce fichier de janvier, sans garantir un schéma
identique pour les autres mois. Les colonnes techniques `_source_file` et
`_loaded_at` sont absentes du fichier et seront renseignées au chargement RAW.

## Codes documentés

Référence : dictionnaire TLC cité ci-dessus. Cette liste décrit les codes de la
source ; leur présence effective dans janvier n'a pas été comptée ici.

| Colonne | Code | Signification |
|---|---|---|
| `VendorID` | 1 | Creative Mobile Technologies, LLC |
| `VendorID` | 2 | Curb Mobility, LLC |
| `VendorID` | 6 | Myle Technologies Inc |
| `VendorID` | 7 | Helix |
| `RatecodeID` | 1 | Standard |
| `RatecodeID` | 2 | JFK |
| `RatecodeID` | 3 | Newark |
| `RatecodeID` | 4 | Nassau / Westchester |
| `RatecodeID` | 5 | Négocié |
| `RatecodeID` | 6 | Collectif |
| `RatecodeID` | 99 | Inconnu |
| `payment_type` | 0 | Flex Fare |
| `payment_type` | 1 | Carte bancaire |
| `payment_type` | 2 | Espèces |
| `payment_type` | 3 | Gratuit |
| `payment_type` | 4 | Litige |
| `payment_type` | 5 | Inconnu |
| `payment_type` | 6 | Annulé |
| `store_and_fwd_flag` | Y | Transmission différée |
| `store_and_fwd_flag` | N | Sans transmission différée |

Les identifiants de zones se rapprochent du fichier `taxi_zone_lookup.csv`.

## Résultats de l'exploration

Mesures obtenues sur l'ensemble du fichier avec les requêtes 1, 3 et 4.
La requête 2 affiche uniquement un échantillon de dix lignes, sans ordre garanti.

| Mesure | Résultat |
|---|---:|
| Nombre de trajets | 3 475 226 |
| Nombre de passagers absent | 540 149 |
| Nombre de passagers égal à zéro | 24 656 |
| Distance absente | 0 |
| Distance inférieure ou égale à zéro | 90 893 |
| Montant total négatif | 63 037 |
| Date de départ absente | 0 |
| Départ hors de janvier 2025 | 22 |
| Arrivée antérieure ou égale au départ | 2 051 |

| Borne temporelle des départs | Valeur |
|---|---|
| Minimum | `2024-12-31 20:47:55` |
| Maximum | `2025-02-01 00:00:44` |

Ces indicateurs peuvent concerner les mêmes trajets : leur somme ne représente
pas un nombre de trajets distincts à rejeter. Les comparaisons SQL ne comptent pas
les valeurs `NULL` ; les durées non positives ne constituent donc pas un contrôle
de complétude des deux dates. Les mesures ne démontrent pas la cause des valeurs
observées et ne remplacent pas les règles des transformations SQL fournies.

## Ce qui a surpris

Aucune distance n'est absente, mais 90 893 sont nulles ou négatives : complétude
et validité sont différentes. Le fichier mensuel contient 22 départs hors janvier,
d'où l'intérêt de conserver son nom d'origine indépendamment des dates de trajet.
Les passagers absents, montants négatifs et durées non positives justifient des
contrôles avant l'analyse, tout en conservant les valeurs sources en RAW.
