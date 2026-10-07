"""Upload one local TLC file to the root of the internal Snowflake stage."""

import argparse
from pathlib import Path

import snowflake.connector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True, help="ORGANIZATION-ACCOUNT")
    parser.add_argument("--file", required=True, help="Local CSV or Parquet file")
    parser.add_argument("--private-key", default="~/.ssh/snowflake/rsa_key.p8")
    args = parser.parse_args()

    source = Path(args.file).expanduser().resolve()
    key_path = Path(args.private_key).expanduser()
    if not source.is_file():
        parser.error(f"Source file not found: {source}")
    if source.suffix.lower() not in {".parquet", ".csv"}:
        parser.error("Expected a .parquet or .csv source file")
    if any(character in str(source) for character in "*?[]"):
        parser.error("Wildcard characters are not supported; select one file")
    if not key_path.is_file():
        parser.error(f"Private key file not found: {key_path}")

    print(f"Uploading {source.name} ({source.stat().st_size} bytes)", flush=True)
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
        with connection.cursor(snowflake.connector.DictCursor) as cursor:
            cursor.execute("USE SECONDARY ROLES NONE")
            # Keep the original filename and place it at the root of the stage.
            # Binding quotes the local URI without inserting it into SQL manually.
            cursor.execute(
                "PUT %s @NYC_TAXI.RAW.TLC_STAGE "
                "AUTO_COMPRESS = FALSE OVERWRITE = FALSE",
                ("file://" + source.as_posix(),),
            )
            results = cursor.fetchall()

    if not results:
        raise SystemExit("Upload returned no file status")
    for result in results:
        # Normalize metadata column names returned by the connector.
        result = {name.lower(): value for name, value in result.items()}
        status = result.get("status")
        print(f"{result.get('source')} -> {result.get('target')}: {status}")
        if result.get("message"):
            print(result["message"])
        if status not in {"UPLOADED", "SKIPPED"}:
            raise SystemExit("File upload did not succeed")
    print("Stage transfer finished. No table rows were loaded.")


if __name__ == "__main__":
    main()
