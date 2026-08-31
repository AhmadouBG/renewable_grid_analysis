# extract/export_parquet.py
import duckdb
import config

TABLES_TO_EXPORT = [
    "dim_grid_point", "dim_daily", "dim_hourly",
    "fact_hourly_weather", "fact_daily_weather", "fact_hourly_air_quality",
    "kpi_generation_potential","kpi_grid_stability", "kpi_harmattan_risk",
    "kpi_preventive_maintenance_window",
]

con = duckdb.connect(str(config.DUCKDB_PATH), read_only=True)
for table in TABLES_TO_EXPORT:
    out_path = config.PARQUET_DIR / f"{table}.parquet"
    con.execute(f"COPY {table} TO '{out_path}' (FORMAT PARQUET)")
    print(f"Exported {table}")
con.close()