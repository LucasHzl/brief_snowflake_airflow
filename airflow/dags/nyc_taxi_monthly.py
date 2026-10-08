"""Load January through March 2025 into RAW, one scheduled run per month."""

from datetime import timedelta
import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from airflow.sdk import DAG
from airflow.timetables.interval import CronDataIntervalTimetable
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.sensors.python import PythonSensor
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from pendulum import datetime

CONNECTION_ID = "snowflake_nyc_taxi"
MONTH = '{{ logical_date.strftime("%Y-%m") }}'
LOGGER = logging.getLogger(__name__)


def source_url(month):
    # Restrict ingestion to the three months in the project scope.
    if month not in {"2025-01", "2025-02", "2025-03"}:
        raise ValueError(f"Month outside the project scope: {month}")
    return f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet"


def file_is_available(month):
    import requests

    url = source_url(month)
    with requests.head(url, timeout=(10, 30), allow_redirects=True) as response:
        if response.status_code == 404:
            LOGGER.info("File not published yet: %s", url)
            return False
        response.raise_for_status()
    LOGGER.info("File available for %s", month)
    return True


def download_and_stage(month):
    import requests
    import snowflake.connector
    from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook

    url = source_url(month)
    filename = f"yellow_tripdata_{month}.parquet"
    # Download and PUT share the same task and local temporary directory.
    # No file path needs to be passed to another worker.
    with TemporaryDirectory(prefix="nyc_taxi_") as directory:
        source = Path(directory) / filename
        LOGGER.info("Downloading %s", url)
        with requests.get(url, stream=True, timeout=(10, 60),
                          headers={"User-Agent": "NYCTaxiAirflowPipeline/1.0"}) as response:
            response.raise_for_status()
            with source.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)
        if source.stat().st_size < 12:
            raise ValueError("Downloaded Parquet is too short")
        with source.open("rb") as downloaded:
            first = downloaded.read(4)
            downloaded.seek(-4, 2)
            last = downloaded.read(4)
        if first != b"PAR1" or last != b"PAR1":
            raise ValueError("Downloaded file has invalid Parquet markers")
        LOGGER.info("Downloaded %s bytes for %s", source.stat().st_size, month)

        hook = SnowflakeHook(snowflake_conn_id=CONNECTION_ID)
        with hook.get_conn() as connection:
            with connection.cursor(snowflake.connector.DictCursor) as cursor:
                cursor.execute("USE SECONDARY ROLES NONE")
                cursor.execute(
                    "PUT %s @NYC_TAXI.RAW.TLC_STAGE "
                    "AUTO_COMPRESS = FALSE OVERWRITE = FALSE",
                    ("file://" + source.as_posix(),),
                )
                results = cursor.fetchall()
                if not results:
                    raise RuntimeError("PUT returned no file status")
                for row in results:
                    row = {name.lower(): value for name, value in row.items()}
                    LOGGER.info("PUT file=%s status=%s message=%s", filename,
                                row.get("status"), row.get("message"))
                    if row.get("status") not in {"UPLOADED", "SKIPPED"}:
                        raise RuntimeError("PUT did not succeed")


with DAG(
    dag_id="nyc_taxi_monthly",
    description="Load the three monthly TLC files into Snowflake RAW",
    start_date=datetime(2025, 1, 1, tz="UTC"),
    # Latest logical date: March 1, whose interval ends on April 1.
    end_date=datetime(2025, 3, 1, tz="UTC"),
    schedule=CronDataIntervalTimetable("0 0 1 * *", timezone="UTC"),
    catchup=True,
    max_active_runs=1,
    is_paused_upon_creation=True,
    default_args={"owner": "nyc_taxi", "retries": 2,
                  "retry_delay": timedelta(seconds=30)},
    template_searchpath=[str(Path(__file__).resolve().parents[1] / "include" / "sql")],
    tags=["nyc_taxi", "monthly", "raw"],
) as dag:
    wait_for_file = PythonSensor(
        task_id="wait_for_file",
        python_callable=file_is_available,
        op_kwargs={"month": MONTH},
        mode="reschedule",
        poke_interval=60,
        timeout=3600,
        retries=0,
    )
    stage_file = PythonOperator(
        task_id="download_and_stage",
        python_callable=download_and_stage,
        op_kwargs={"month": MONTH},
        execution_timeout=timedelta(minutes=15),
        do_xcom_push=False,
    )
    copy_into_raw = SQLExecuteQueryOperator(
        task_id="copy_into_raw",
        conn_id=CONNECTION_ID,
        sql="raw/load_yellow_trips.sql",
        autocommit=True,
        show_return_value_in_logs=True,
        execution_timeout=timedelta(minutes=15),
    )

    wait_for_file >> stage_file >> copy_into_raw
