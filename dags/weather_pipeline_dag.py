from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

DBT_CMD = "cd /opt/airflow/dbt_weather_data_analysis && dbt"

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "weather_pipeline_ingest",
    schedule="0 6 */2 * *",   # every 2 days at 6am
    start_date=datetime(2026, 8, 1),
    catchup=False,
    default_args=default_args,
    tags=["scheduled"],
    description="Recurring ingest: extract new weather/air-quality data, upsert into facts, refresh KPIs.",
) as dag:

    extract_weather = BashOperator(
        task_id="extract_weather",
        bash_command="python /opt/airflow/extract/extract_weather.py",
    )

    extract_air_quality = BashOperator(
        task_id="extract_air_quality",
        bash_command="python /opt/airflow/extract/extract_air_quality.py",
    )

    dbt_staging = BashOperator(
        task_id="dbt_staging",
        bash_command=f"{DBT_CMD} run --select stg_hourly stg_daily stg_air_quality --profiles-dir .",
    )

    dbt_build_dims = BashOperator(
        task_id="dbt_build_dims",
        bash_command=f"{DBT_CMD} run --select dim_daily dim_hourly --profiles-dir .",
    )

    dbt_facts = BashOperator(
        task_id="dbt_facts",
        bash_command=f"{DBT_CMD} run --select fact_hourly_weather fact_daily_weather fact_hourly_air_quality --profiles-dir .",
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
        extract_weather
        >> extract_air_quality
        >> dbt_staging
        >> dbt_build_dims
        >> dbt_facts
        >> dbt_marts
        >> dbt_test
    )