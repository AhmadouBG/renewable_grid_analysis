from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from datetime import datetime
import os

DBT_CMD = "cd /opt/airflow/dbt_weather_data_analysis && dbt"
DB_PATH = "/opt/airflow/output/weather_grid_analysis_database.duckdb"
WAL_PATH = f"{DB_PATH}.wal"


def confirm_and_remove_db(**context):
    from airflow.sdk import Variable
    confirmation = Variable.get("allow_db_reset", default="yes")
    if confirmation != "yes":
        raise ValueError(
            "Refusing to delete database: set Airflow Variable 'allow_db_reset' to 'yes' "
            "to confirm you intend to permanently destroy all pipeline history."
        )
    for path in [DB_PATH, WAL_PATH]:
        if os.path.exists(path):
            os.remove(path)
            print(f"Removed {path}")
        else:
            print(f"Not found (already clean): {path}")


with DAG(
    "weather_pipeline_reset",
    schedule=None,          # NEVER scheduled — manual trigger only
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["destructive", "manual-only"],
    description="DESTRUCTIVE: wipes the database and rebuilds everything from scratch. Requires Airflow Variable allow_db_reset=yes.",
) as dag:

    remove_db = PythonOperator(
        task_id="remove_db",
        python_callable=confirm_and_remove_db,
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"{DBT_CMD} seed --profiles-dir .",
    )

    dbt_build_grid = BashOperator(
        task_id="dbt_build_grid",
        bash_command=f"{DBT_CMD} run --select stg_grid_points dim_grid_point --profiles-dir .",
    )

    extract_weather = BashOperator(
        task_id="extract_weather",
        bash_command="python /opt/airflow/dbt_weather_data_analysis/extract/extract_weather.py",
    )

    extract_air_quality = BashOperator(
        task_id="extract_air_quality",
        bash_command="python /opt/airflow/dbt_weather_data_analysis/extract/extract_air_quality.py",
    )

    dbt_staging = BashOperator(
        task_id="dbt_staging",
        bash_command=f"{DBT_CMD} run --select stg_hourly stg_daily stg_air_quality --profiles-dir .",
    )

    dbt_build_dims = BashOperator(
        task_id="dbt_build_dims",
        bash_command=f"{DBT_CMD} run --select dim_daily dim_hourly --profiles-dir .",
    )

    dbt_facts_full_refresh = BashOperator(
        task_id="dbt_facts_full_refresh",
        bash_command=(
            f"{DBT_CMD} run --select fact_hourly_weather fact_daily_weather "
            f"fact_hourly_air_quality --full-refresh --profiles-dir ."
        ),
    )

    dbt_marts = BashOperator(
        task_id="dbt_marts",
        bash_command=(
            f"{DBT_CMD} run --exclude stg_grid_points dim_grid_point "
            f"stg_hourly stg_daily stg_air_quality dim_daily dim_hourly "
            f"fact_hourly_weather fact_daily_weather fact_hourly_air_quality --profiles-dir ."
        ),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"{DBT_CMD} test --profiles-dir .",
    )

    (
        remove_db
        >> dbt_seed
        >> dbt_build_grid
        >> extract_weather
        >> extract_air_quality
        >> dbt_staging
        >> dbt_build_dims
        >> dbt_facts_full_refresh
        >> dbt_marts
        >> dbt_test
    )