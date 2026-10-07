"""Check the service user's Snowflake connection using a local private key."""

import argparse
from pathlib import Path

import snowflake.connector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True, help="ORGANIZATION-ACCOUNT")
    parser.add_argument("--private-key", default="~/.ssh/snowflake/rsa_key.p8")
    args = parser.parse_args()

    key_path = Path(args.private_key).expanduser()
    if not key_path.is_file():
        parser.error(f"Private key file not found: {key_path}")

    # The connector reads the key locally; the key itself is never printed.
    with snowflake.connector.connect(
        account=args.account,
        user="AIRFLOW_SVC",
        authenticator="SNOWFLAKE_JWT",
        private_key_file=str(key_path),
        role="TRANSFORMER",
        warehouse="NYC_TAXI_WH",
        database="NYC_TAXI",
        schema="RAW",
        login_timeout=30,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("USE SECONDARY ROLES NONE")
            cursor.execute("""
                SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(),
                       CURRENT_DATABASE(), CURRENT_SCHEMA()
            """)
            result = cursor.fetchone()

    expected = ("AIRFLOW_SVC", "TRANSFORMER", "NYC_TAXI_WH", "NYC_TAXI", "RAW")
    if result != expected:
        raise SystemExit(f"Unexpected connection context: {result}")

    print("Connection successful")
    for label, value in zip(("User", "Role", "Warehouse", "Database", "Schema"), result):
        print(f"{label}: {value}")


if __name__ == "__main__":
    main()
