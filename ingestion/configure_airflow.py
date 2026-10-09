"""Create a local Airflow connection file without printing credentials."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True)
    parser.add_argument("--private-key", type=Path, default=Path.home() / ".ssh/snowflake/rsa_key.p8")
    args = parser.parse_args()
    account = args.account.strip()
    if not account or any(char in account for char in " /:\n\r"):
        parser.error("Use the account identifier, without a URL or domain suffix")
    key = args.private_key.expanduser().read_text()
    if "-----BEGIN PRIVATE KEY-----" not in key or "-----END PRIVATE KEY-----" not in key:
        parser.error("Expected an unencrypted PKCS8 PEM private key")
    connection = {"conn_type": "snowflake", "login": "AIRFLOW_SVC", "extra": {
        "account": account, "warehouse": "NYC_TAXI_WH", "database": "NYC_TAXI",
        "role": "TRANSFORMER", "private_key_content": key}}
    destination = Path(__file__).resolve().parents[1] / "airflow" / ".env"
    # Exclusive creation preserves any existing local configuration.
    payload = "AIRFLOW_CONN_SNOWFLAKE_NYC_TAXI='" + json.dumps(connection) + "'\n"
    if "'" in json.dumps(connection):
        parser.error("Unsupported single quote in connection values")
    try:
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        parser.exit(1, "airflow/.env already exists; existing configuration preserved.\n")
    with os.fdopen(fd, "w") as output:
        output.write(payload)
    print("Created airflow/.env with owner-only permissions; no credentials displayed.")


if __name__ == "__main__":
    main()
