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


def test_transformations_and_quality_gates():
    from airflow.providers.common.sql.operators.sql import SQLCheckOperator, SQLExecuteQueryOperator
    from jinja2 import StrictUndefined
    from pendulum import datetime

    bag = DagBag(dag_folder=str(Path(__file__).resolve().parents[2] / "dags"), include_examples=False)
    assert not bag.import_errors, bag.import_errors
    dag = bag.dags["nyc_taxi_monthly"]
    dag.topological_sort()  # Reject dependency cycles.
    env = dag.get_template_env()
    env.undefined = StrictUndefined
    params = dict(dag.params)
    sql_files = []
    sql_root = Path(__file__).resolve().parents[2] / "include" / "sql"
    source_paths = {p.read_text(): str(p.relative_to(sql_root)) for p in sql_root.rglob("*.sql")}
    for task in dag.tasks:
        assert getattr(task.trigger_rule, "value", task.trigger_rule) == "all_success"
        if not isinstance(task, (SQLCheckOperator, SQLExecuteQueryOperator)):
            continue
        # DagBag may have already expanded the SQL file into template text.
        sql_path = source_paths.get(task.sql, task.sql)
        sql_files.append(sql_path)
        for month in (1, 2, 3):
            date = datetime(2025, month, 1, tz="UTC")
            rendered = env.get_template(sql_path).render(
                logical_date=date, ds=date.strftime("%Y-%m-%d"), params=params,
            )
            assert "{{" not in rendered
            if "DELETE FROM" in rendered:
                assert task.split_statements is True
                assert task.autocommit is False
                assert date.strftime("%Y-%m-%d") in rendered
        if isinstance(task, SQLCheckOperator):
            assert task.retries == 0
    supplied = Path(__file__).resolve().parents[2] / "include" / "sql"
    assert set(sql_files) == {str(p.relative_to(supplied)) for p in supplied.rglob("*.sql")}
    assert len(sql_files) == len(set(sql_files))

    for gate_id, blocked_id in (
        ("check_raw_month", "staging.yellow_trips"),
        ("intermediate.check_rejection_rate", "intermediate.enriched"),
        ("intermediate.check_trip_keys", "marts.fct_trips"),
    ):
        upstream = dag.get_task(blocked_id).get_flat_relative_ids(upstream=True)
        assert gate_id in upstream
    for task_id in ("marts.hourly_demand", "marts.daily_revenue", "marts.data_quality"):
        assert "marts.fct_trips" in dag.get_task(task_id).upstream_task_ids


def test_quality_operator_rejects_false_results():
    from unittest.mock import MagicMock, patch
    import pytest
    from airflow.exceptions import AirflowException
    from airflow.providers.common.sql.operators.sql import SQLCheckOperator

    task = SQLCheckOperator(task_id="check_behavior", sql="SELECT 1", retries=0)
    hook = MagicMock()
    with patch.object(task, "get_db_hook", return_value=hook):
        hook.get_first.return_value = (True, True, True)
        task.execute(context={})
        for result in ((True, False, True), (False, False), (True, None), None):
            hook.get_first.return_value = result
            with pytest.raises(AirflowException):
                task.execute(context={})
