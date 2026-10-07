"""Download, stage and load one month of NYC Yellow Taxi data into RAW."""

import argparse
from datetime import datetime
import logging
from pathlib import Path
import re

import requests
import snowflake.connector

from upload_file import upload_to_stage

LOGGER = logging.getLogger(__name__)
INPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "input"


def parse_month(value):
    """Require a real calendar month in YYYY-MM format."""
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}", value):
        raise argparse.ArgumentTypeError("Expected YYYY-MM, for example 2025-01")
    try:
        datetime.strptime(value, "%Y-%m")
    except ValueError as error:
        raise argparse.ArgumentTypeError("Invalid calendar month") from error
    return value


def check_parquet(path):
    """Check file markers, not the full Parquet contents (COPY validates those)."""
    if path.stat().st_size < 12:
        raise ValueError(f"Parquet file is too short: {path}")
    with path.open("rb") as source:
        first = source.read(4)
        source.seek(-4, 2)
        last = source.read(4)
    if first != b"PAR1" or last != b"PAR1":
        raise ValueError(f"Missing Parquet markers: {path}")


def download_month(month, directory):
    """Reuse a local file or publish a download only after it has finished."""
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"yellow_tripdata_{month}.parquet"
    if destination.exists():
        check_parquet(destination)
        LOGGER.info("Reusing local file: %s", destination.name)
        return destination

    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{destination.name}"
    temporary = destination.with_suffix(".parquet.part")
    LOGGER.info("Downloading %s", url)
    try:
        with requests.get(
            url, stream=True, timeout=(10, 60),
            headers={"User-Agent": "NYCTaxiTrainingPipeline/1.0"},
        ) as response:
            response.raise_for_status()
            with temporary.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)
        check_parquet(temporary)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    LOGGER.info("Downloaded %s bytes", destination.stat().st_size)
    return destination


def copy_month(cursor, filename):
    """Load the selected file with the same options as the validated SQL."""
    cursor.execute("""
        COPY INTO NYC_TAXI.RAW.YELLOW_TRIPDATA
        FROM @NYC_TAXI.RAW.TLC_STAGE
        FILES = (%s)
        FILE_FORMAT = (FORMAT_NAME = 'NYC_TAXI.RAW.PARQUET_FORMAT')
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
        INCLUDE_METADATA = (
            _source_file = METADATA$FILENAME,
            _loaded_at = METADATA$START_SCAN_TIME
        )
        ON_ERROR = ABORT_STATEMENT
        FORCE = FALSE
    """, (filename,))
    for result in cursor.fetchall():
        result = {name.lower(): value for name, value in result.items()}
        LOGGER.info("COPY result: %s", result)
        status = result.get("status")
        errors = int(result.get("errors_seen") or 0)
        # Snowflake can report errors_seen=1 for a normal replay skip.
        already_loaded = (
            status == "LOAD_SKIPPED"
            and result.get("first_error") == "File was loaded before."
        )
        if errors and not already_loaded:
            raise RuntimeError("COPY reported errors")
        if status is not None and status not in {"LOADED", "LOAD_SKIPPED"}:
            raise RuntimeError(f"Unexpected COPY status: {status}")
        if status == "LOAD_SKIPPED":
            LOGGER.info("File already loaded; verifying existing RAW rows")

    cursor.execute("""
        SELECT COUNT(*) AS trip_count,
               COUNT_IF(_loaded_at IS NULL) AS missing_loaded_at,
               MIN(_loaded_at) AS first_loaded_at,
               MAX(_loaded_at) AS last_loaded_at
        FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
        WHERE _source_file = %s
    """, (filename,))
    summary = {name.lower(): value for name, value in cursor.fetchone().items()}
    if summary["trip_count"] == 0 or summary["missing_loaded_at"]:
        raise RuntimeError(f"RAW verification failed: {summary}")
    LOGGER.info("RAW file=%s rows=%s first_loaded_at=%s last_loaded_at=%s",
                filename, summary["trip_count"], summary["first_loaded_at"],
                summary["last_loaded_at"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--account", required=True, help="ORGANIZATION-ACCOUNT")
    parser.add_argument("--month", required=True, type=parse_month)
    parser.add_argument("--input-dir", type=Path, default=INPUT_DIR)
    parser.add_argument("--private-key", default="~/.ssh/snowflake/rsa_key.p8")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # Keep library diagnostics quiet while retaining their warnings and errors.
    logging.getLogger("snowflake.connector").setLevel(logging.WARNING)
    key_path = Path(args.private_key).expanduser()
    if not key_path.is_file():
        parser.error(f"Private key file not found: {key_path}")
    directory = args.input_dir.expanduser().resolve()
    if any(character in str(directory) for character in "*?[]"):
        parser.error("Wildcard characters are not supported in the input directory")
    try:
        source = download_month(args.month, directory)
        with snowflake.connector.connect(
            account=args.account, user="AIRFLOW_SVC", authenticator="SNOWFLAKE_JWT",
            private_key_file=str(key_path), role="TRANSFORMER", warehouse="NYC_TAXI_WH",
            database="NYC_TAXI", schema="RAW", login_timeout=30,
        ) as connection:
            with connection.cursor(snowflake.connector.DictCursor) as cursor:
                cursor.execute("USE SECONDARY ROLES NONE")
                LOGGER.info("Uploading %s to TLC_STAGE", source.name)
                upload_to_stage(cursor, source)
                LOGGER.info("Loading %s into RAW", args.month)
                copy_month(cursor, source.name)
        LOGGER.info("Month %s finished successfully", args.month)
    except (requests.RequestException, OSError, ValueError, RuntimeError,
            snowflake.connector.Error) as error:
        LOGGER.error("Month %s failed: %s", args.month, error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
