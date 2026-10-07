"""Load the TLC zone reference once, outside the monthly Airflow pipeline."""

import argparse
import csv
import logging
from pathlib import Path

import requests
import snowflake.connector

from upload_file import upload_to_stage

LOGGER = logging.getLogger(__name__)
FILENAME = "taxi_zone_lookup.csv"
URL = f"https://d37ci6vzurychx.cloudfront.net/misc/{FILENAME}"
INPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "input"


def validate_zones(path):
    """Require the source contract before sending the CSV to Snowflake."""
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source, strict=True)
        if next(reader, None) != ["LocationID", "Borough", "Zone", "service_zone"]:
            raise ValueError("Unexpected zone CSV header")
        rows = list(reader)
    if len(rows) != 265 or any(len(row) != 4 for row in rows):
        raise ValueError("Expected 265 zone rows with four fields each")
    identifiers = [int(row[0]) for row in rows]
    if len(set(identifiers)) != 265:
        raise ValueError("Zone identifiers must be unique")
    LOGGER.info("Local CSV verified: 265 rows, 265 unique identifiers")


def download_zones(directory):
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / FILENAME
    if destination.exists():
        validate_zones(destination)
        LOGGER.info("Reusing local file: %s", FILENAME)
        return destination
    temporary = destination.with_suffix(".csv.part")
    LOGGER.info("Downloading %s", URL)
    try:
        with requests.get(URL, stream=True, timeout=(10, 60),
                          headers={"User-Agent": "NYCTaxiTrainingPipeline/1.0"}) as response:
            response.raise_for_status()
            with temporary.open("wb") as output:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        output.write(chunk)
        validate_zones(temporary)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def copy_zones(cursor):
    # CSV_FORMAT skips the header, so map columns by position ($1 to $4).
    # Metadata adds traceability without changing the four source fields.
    cursor.execute("""
        COPY INTO NYC_TAXI.RAW.TAXI_ZONE_LOOKUP
            (locationid, borough, zone, service_zone, _source_file, _loaded_at)
        FROM (
            SELECT $1::INTEGER, $2::VARCHAR, $3::VARCHAR, $4::VARCHAR,
                   METADATA$FILENAME, METADATA$START_SCAN_TIME::TIMESTAMP_NTZ
            FROM @NYC_TAXI.RAW.TLC_STAGE
        )
        FILES = ('taxi_zone_lookup.csv')
        FILE_FORMAT = (FORMAT_NAME = 'NYC_TAXI.RAW.CSV_FORMAT')
        ON_ERROR = ABORT_STATEMENT
        FORCE = FALSE
    """)
    for result in cursor.fetchall():
        result = {name.lower(): value for name, value in result.items()}
        LOGGER.info("COPY result: %s", result)
        status = result.get("status")
        already_loaded = (status == "LOAD_SKIPPED"
                          and result.get("first_error") == "File was loaded before.")
        if int(result.get("errors_seen") or 0) and not already_loaded:
            raise RuntimeError("Zone COPY reported errors")
        if status is not None and status not in {"LOADED", "LOAD_SKIPPED"}:
            raise RuntimeError(f"Unexpected zone COPY status: {status}")

    cursor.execute("""
        SELECT COUNT(*) AS zone_count,
               COUNT(DISTINCT locationid) AS unique_ids,
               COUNT_IF(_source_file IS NULL
                        OR _source_file <> 'taxi_zone_lookup.csv'
                        OR _loaded_at IS NULL) AS invalid_metadata,
               MIN(_loaded_at) AS first_loaded_at,
               MAX(_loaded_at) AS last_loaded_at
        FROM NYC_TAXI.RAW.TAXI_ZONE_LOOKUP
    """)
    result = {name.lower(): value for name, value in cursor.fetchone().items()}
    if result["zone_count"] != 265 or result["unique_ids"] != 265 or result["invalid_metadata"]:
        raise RuntimeError(f"Zone validation failed: {result}")
    LOGGER.info("RAW zones: %s", result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True, help="ORGANIZATION-ACCOUNT")
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--private-key", default="~/.ssh/snowflake/rsa_key.p8")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("snowflake.connector").setLevel(logging.WARNING)
    key_path = Path(args.private_key).expanduser()
    if not key_path.is_file():
        parser.error(f"Private key file not found: {key_path}")
    directory = args.input_dir.expanduser().resolve()
    if any(character in str(directory) for character in "*?[]"):
        parser.error("Wildcard characters are not supported in the input directory")
    try:
        source = download_zones(directory)
        with snowflake.connector.connect(
            account=args.account, user="AIRFLOW_SVC", authenticator="SNOWFLAKE_JWT",
            private_key_file=str(key_path), role="TRANSFORMER", warehouse="NYC_TAXI_WH",
            database="NYC_TAXI", schema="RAW", login_timeout=30,
        ) as connection:
            with connection.cursor(snowflake.connector.DictCursor) as cursor:
                cursor.execute("USE SECONDARY ROLES NONE")
                upload_to_stage(cursor, source)
                copy_zones(cursor)
        LOGGER.info("Zone loading finished successfully")
    except (requests.RequestException, OSError, ValueError, csv.Error, RuntimeError,
            snowflake.connector.Error) as error:
        LOGGER.error("Zone loading failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
