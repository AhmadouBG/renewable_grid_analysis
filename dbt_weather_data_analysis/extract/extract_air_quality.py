import duckdb
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import time
import config

con = duckdb.connect("output/weather_grid_analysis_database.duckdb")
grid_df = con.execute("select * from stg_grid_points").df()

if grid_df.empty:
    raise RuntimeError("stg_grid_points returned 0 rows — check dbt run completed")

cache_session = requests_cache.CachedSession(config.CACHE_PATH, expire_after=config.CACHE_EXPIRE_AFTER_SEC)
retry_session = retry(cache_session, retries=config.RETRY_COUNT, backoff_factor=config.RETRY_BACKOFF_FACTOR)
openmeteo = openmeteo_requests.Client(session=retry_session)

con.execute("create schema if not exists raw")
con.execute("""create table if not exists raw.raw_air_quality (
    timestamp timestamp, arrondissement_name varchar, point_grid_id int,
    latitude double, longitude double,
    pm10 double, pm2_5 double, dust double
)""")
con.execute("""create table if not exists raw.extraction_failures (
    arrondissement_name varchar, error varchar, run_ts timestamp
)""")

for arr_name, group in grid_df.groupby("arrondissement_name"):
    try:
        params = {
            "latitude": group["grid_lat"].tolist(),
            "longitude": group["grid_lon"].tolist(),
            "hourly": config.AIR_QUALITY_HOURLY_VARIABLES,
            "timezone": config.TIMEZONE,
            "past_days": config.PAST_DAYS,
            "forecast_days": config.FORECAST_DAYS,
        }
        responses = openmeteo.weather_api(config.AIR_QUALITY_API_URL, params=params)

        if len(responses) != len(group):
            raise ValueError(f"expected {len(group)} responses, got {len(responses)}")

        arr_aq = []
        for p_idx, response in enumerate(responses):
            point_id = group.iloc[p_idx]["point_grid_id"]

            hourly = response.Hourly()
            h_dates = pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )
            arr_aq.append(pd.DataFrame({
                "timestamp": h_dates,
                "arrondissement_name": arr_name,
                "point_grid_id": point_id,
                "latitude": response.Latitude(),
                "longitude": response.Longitude(),
                "pm10": hourly.Variables(0).ValuesAsNumpy(),
                "pm2_5": hourly.Variables(1).ValuesAsNumpy(),
                "dust": hourly.Variables(2).ValuesAsNumpy(),
            }))

        arr_aq_df = pd.concat(arr_aq, ignore_index=True)
        con.execute("insert into raw.raw_air_quality select * from arr_aq_df")
        print(f"✅ {arr_name} : {len(arr_aq_df)} lignes qualité de l'air écrites")

    except Exception as e:
        print(f"⚠️ {arr_name} sauté : {e}")
        con.execute(
            "insert into raw.extraction_failures values (?, ?, ?)",
            [arr_name, str(e), pd.Timestamp.now()]
        )
        time.sleep(config.SLEEP_ON_ERROR_SEC)
        continue

    time.sleep(config.SLEEP_BETWEEN_REQUESTS_SEC)

print("\n✅ Extraction qualité de l'air terminée.")
print(con.execute("select count(*) from raw.raw_air_quality").fetchone())