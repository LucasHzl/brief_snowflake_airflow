"""Verify DAG discovery without contacting Snowflake."""

from pathlib import Path

from airflow.models import DagBag


def test_connection_dag_imports():
    dags_directory = Path(__file__).resolve().parents[2] / "dags"
    bag = DagBag(dag_folder=str(dags_directory), include_examples=False)
    assert not bag.import_errors, bag.import_errors
    assert "check_snowflake_connection" in bag.dags


def test_monthly_schedule_and_rendered_files():
    from airflow.timetables.base import TimeRestriction
    from pendulum import datetime

    dags_directory = Path(__file__).resolve().parents[2] / "dags"
    bag = DagBag(dag_folder=str(dags_directory), include_examples=False)
    assert not bag.import_errors, bag.import_errors
    dag = bag.dags["nyc_taxi_monthly"]
    assert dag.is_paused_upon_creation
    assert dag.max_active_runs == 1
    assert dag.get_task("wait_for_file").downstream_task_ids == {"download_and_stage"}
    assert dag.get_task("download_and_stage").downstream_task_ids == {"copy_into_raw"}

    restriction = TimeRestriction(earliest=dag.start_date, latest=dag.end_date, catchup=dag.catchup)
    previous = None
    logical_dates = []
    for _ in range(4):
        info = dag.timetable.next_dagrun_info(
            last_automated_data_interval=previous, restriction=restriction,
        )
        if info is None:
            break
        logical_dates.append(info.data_interval.start.strftime("%Y-%m"))
        previous = info.data_interval
    assert logical_dates == ["2025-01", "2025-02", "2025-03"]

    template = dag.get_template_env().get_template("raw/load_yellow_trips.sql")
    for month in (1, 2, 3):
        rendered = template.render(logical_date=datetime(2025, month, 1, tz="UTC"))
        assert f"yellow_tripdata_2025-{month:02d}.parquet" in rendered
        assert "FORCE = FALSE" in rendered
        assert "{{" not in rendered
