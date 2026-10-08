"""Verify DAG discovery without contacting Snowflake."""

from pathlib import Path

from airflow.models import DagBag


def test_connection_dag_imports():
    dags_directory = Path(__file__).resolve().parents[2] / "dags"
    bag = DagBag(dag_folder=str(dags_directory), include_examples=False)
    assert not bag.import_errors, bag.import_errors
    assert "check_snowflake_connection" in bag.dags
