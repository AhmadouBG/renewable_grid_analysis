from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

DUCKDB_OUTPUT_DIR = "/opt/airflow/dbt_weather_data_analysis/output"
DUCKDB_PATH = f"{DUCKDB_OUTPUT_DIR}/weather_grid_analysis_database.duckdb"

with DAG(
    "weather_pipeline",
    schedule="0 */1 * * *",   # every hour
    start_date=datetime(2026, 8, 24),
    catchup=False,
    default_args=default_args,
) as dag:

    # Ensure the output directory and DuckDB file are writable by the Airflow user.
    # Docker on Windows mounts volumes owned by root; this task fixes permissions
    # so subsequent tasks can open/create the DuckDB file without "Permission denied".
    fix_permissions = BashOperator(
        task_id="fix_permissions",
        bash_command=(
            f"mkdir -p {DUCKDB_OUTPUT_DIR} && "
            f"chmod -R 777 {DUCKDB_OUTPUT_DIR}"
        ),
        # Run as root to be able to chmod; uses docker exec override via env var.
        # If the container doesn't allow root, remove the user override and rely
        # on the AIRFLOW_UID being set correctly in .env instead.
    )

    extract_weather = BashOperator(
        task_id="extract_weather",
        bash_command=f"python /opt/airflow/dbt_weather_data_analysis/extract/extract_weather.py",
    )

    extract_air_quality = BashOperator(
        task_id="extract_air_quality",
        bash_command=f"python /opt/airflow/dbt_weather_data_analysis/extract/extract_air_quality.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_weather_data_analysis && dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_weather_data_analysis && dbt test --profiles-dir .",
    )

    fix_permissions >> extract_weather >> extract_air_quality >> dbt_run >> dbt_test