"""Manually verify the Snowflake connection used by the NYC Taxi pipeline."""

from airflow.sdk import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from pendulum import datetime

with DAG(
    dag_id="check_snowflake_connection",
    description="Display the Snowflake service user and connection context",
    start_date=datetime(2025, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    default_args={"owner": "nyc_taxi", "retries": 0},
    tags=["nyc_taxi", "connection"],
) as dag:
    check_connection = SQLExecuteQueryOperator(
        task_id="check_connection",
        conn_id="snowflake_nyc_taxi",
        sql="""
            SELECT CURRENT_USER() AS service_user,
                   CURRENT_ROLE() AS active_role,
                   CURRENT_WAREHOUSE() AS active_warehouse,
                   CURRENT_DATABASE() AS active_database
        """,
        show_return_value_in_logs=True,
    )
