# Infrastructure et connexion Snowflake

## Prérequis

Compte Snowflake avec les rôles SYSADMIN et SECURITYADMIN accessibles,
Python 3.12, uv et OpenSSL. Les commandes du terminal s'exécutent depuis la racine
du dépôt, sauf les commandes SQL qui s'exécutent dans Snowsight.

## Infrastructure

Exécuter les scripts dans cet ordre, en sélectionnant toutes les instructions
ou en les exécutant une par une :

1. [01_infrastructure.sql](../snowflake/01_infrastructure.sql) : warehouse XS,
   suspension automatique après 60 secondes, base et quatre schémas.
2. [02_roles.sql](../snowflake/02_roles.sql) : rôle TRANSFORMER et droits du contrat RAW.
3. [verify_context.sql](../snowflake/verify_context.sql) : vérification du contexte
   sous TRANSFORMER, avec les rôles secondaires désactivés.
4. [03_service_user.sql](../snowflake/03_service_user.sql) : utilisateur AIRFLOW_SVC
   de type SERVICE et attribution de TRANSFORMER.

Les clauses IF NOT EXISTS conservent les objets existants sans corriger leurs
paramètres : vérifier les résultats des commandes SHOW lors d'une réexécution.

## Paire de clés locale

Les fichiers sont conservés hors du dépôt. La clé privée non chiffrée correspond
au format du fichier airflow/.env.example ; son accès est limité par les
permissions du système. Ne jamais publier son contenu.

```bash
mkdir -p ~/.ssh/snowflake
chmod 700 ~/.ssh/snowflake
ls -la ~/.ssh/snowflake
```

Si rsa_key.p8 ou rsa_key.pub existe déjà, ne pas le remplacer : réutiliser la paire
appropriée ou choisir de nouveaux chemins et adapter les commandes.
Pour une nouvelle paire :

```bash
(
    umask 077
    openssl genrsa 2048 |
        openssl pkcs8 -topk8 -inform PEM \
        -out ~/.ssh/snowflake/rsa_key.p8 -nocrypt
    openssl rsa -in ~/.ssh/snowflake/rsa_key.p8 \
        -pubout -out ~/.ssh/snowflake/rsa_key.pub
)
```

Afficher uniquement la clé publique, sans délimiteurs et sur une ligne :

```bash
awk '!/-----/ {printf "%s", $0} END {print ""}' ~/.ssh/snowflake/rsa_key.pub
```

Produire l'instruction d'enregistrement depuis le fichier de clé publique :

```bash
python - <<'PYCODE'
from pathlib import Path
public_key = "".join(
    line.strip() for line in Path.home().joinpath(".ssh/snowflake/rsa_key.pub").read_text().splitlines()
    if not line.startswith("-----")
)
print("USE ROLE SECURITYADMIN;")
print("ALTER USER AIRFLOW_SVC SET RSA_PUBLIC_KEY = '" + public_key + "';")
print("DESCRIBE USER AIRFLOW_SVC;")
PYCODE
```

Exécuter les trois instructions produites dans Snowsight.

Vérifier que RSA_PUBLIC_KEY_FP contient une empreinte. Cette vérification constate
l'enregistrement d'une clé publique ; le test Python valide ensuite la connexion.

## Test depuis Python

Obtenir l'identifiant du compte dans Snowsight :

```sql
SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME()
    AS account_identifier;
```

Préparer l'environnement Python une seule fois s'il n'existe pas :

```bash
uv venv --python 3.12
```

Activer l'environnement et installer le connecteur :

```bash
source .venv/bin/activate
uv pip install -r ingestion/requirements.txt
```

Saisir l'identifiant obtenu, sans URL ni suffixe de domaine :

```bash
read -r 'SNOWFLAKE_ACCOUNT?Identifiant de compte Snowflake : '
python ingestion/check_connection.py --account "$SNOWFLAKE_ACCOUNT"
```

L'option --private-key permet d'utiliser un autre chemin de clé privée.
Le script ne modifie aucune donnée et ferme la connexion après la vérification.
Une erreur de connexion ou un contexte différent de celui attendu produit un
code de sortie non nul.

## Validation du 7 octobre 2026

Exécution depuis le poste local avec authentification par clé :

```text
Connection successful
User: AIRFLOW_SVC
Role: TRANSFORMER
Warehouse: NYC_TAXI_WH
Database: NYC_TAXI
Schema: RAW
```

Ce résultat valide l'authentification et le contexte de connexion. Il ne prouve
pas encore le chargement des fichiers, la création des tables RAW ni l'exécution
des transformations.

Références : [authentification par clé](https://docs.snowflake.com/en/user-guide/key-pair-auth),
[connecteur Python](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect).
