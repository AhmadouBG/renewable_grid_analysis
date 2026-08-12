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
con.execute("""create table if not exists raw.raw_hourly (
    timestamp timestamp, arrondissement_name varchar, point_grid_id int,
    latitude double, longitude double, temperature_2m double,
    cloud_cover_pct double, direct_radiation_w_m2 double,
    shortwave_radiation_w_m2 double, wind_speed_80m_kmh double,
    wind_direction_80m_deg double, precipitation_mm double,
    visibility_m double, weather_code_wmo double
)""")
con.execute("""create table if not exists raw.raw_daily (
    date date, arrondissement_name varchar, point_grid_id int,
    latitude double, longitude double, temp_max_2m double,
    temp_mean_2m double, temp_min_2m double, precipitation_sum_mm double,
    rain_sum_mm double, precipitation_probability_max_pct double,
    sunshine_duration_sec double, daylight_duration_sec double,
    wind_speed_max_10m_kmh double, wind_gusts_max_10m_kmh double,
    shortwave_radiation_sum_mj_m2 double
)""")
con.execute("""create table if not exists raw.extraction_failures (
    arrondissement_name varchar, error varchar, run_ts timestamp
)""")

for arr_name, group in grid_df.groupby("arrondissement_name"):
    try:
        params = {
            "latitude": group["grid_lat"].tolist(),
            "longitude": group["grid_lon"].tolist(),
            "hourly": config.HOURLY_VARIABLES,
            "daily": config.DAILY_VARIABLES,
            "timezone": config.TIMEZONE,
            "past_days": config.PAST_DAYS,
            "forecast_days": config.FORECAST_DAYS,
        }
        responses = openmeteo.weather_api(config.API_URL, params=params)

        if len(responses) != len(group):
            raise ValueError(f"expected {len(group)} responses, got {len(responses)}")

        arr_hourly, arr_daily = [], []
        for p_idx, response in enumerate(responses):
            point_id = group.iloc[p_idx]["point_grid_id"]

            hourly = response.Hourly()
            h_dates = pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )
            arr_hourly.append(pd.DataFrame({
                "timestamp": h_dates,
                "arrondissement_name": arr_name,
                "point_grid_id": point_id,
                "latitude": response.Latitude(),
                "longitude": response.Longitude(),
                "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
                "cloud_cover_pct": hourly.Variables(1).ValuesAsNumpy(),
                "direct_radiation_w_m2": hourly.Variables(2).ValuesAsNumpy(),
                "shortwave_radiation_w_m2": hourly.Variables(3).ValuesAsNumpy(),
                "wind_speed_80m_kmh": hourly.Variables(4).ValuesAsNumpy(),
                "wind_direction_80m_deg": hourly.Variables(5).ValuesAsNumpy(),
                "precipitation_mm": hourly.Variables(6).ValuesAsNumpy(),
                "visibility_m": hourly.Variables(7).ValuesAsNumpy(),
                "weather_code_wmo": hourly.Variables(8).ValuesAsNumpy(),
            }))

            daily = response.Daily()
            d_dates = pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left",
            )
            arr_daily.append(pd.DataFrame({
                "date": d_dates.date,
                "arrondissement_name": arr_name,
                "point_grid_id": point_id,
                "latitude": response.Latitude(),
                "longitude": response.Longitude(),
                "temp_max_2m": daily.Variables(0).ValuesAsNumpy(),
                "temp_mean_2m": daily.Variables(1).ValuesAsNumpy(),
                "temp_min_2m": daily.Variables(2).ValuesAsNumpy(),
                "precipitation_sum_mm": daily.Variables(3).ValuesAsNumpy(),
                "rain_sum_mm": daily.Variables(4).ValuesAsNumpy(),
                "precipitation_probability_max_pct": daily.Variables(5).ValuesAsNumpy(),
                "sunshine_duration_sec": daily.Variables(6).ValuesAsNumpy(),
                "daylight_duration_sec": daily.Variables(7).ValuesAsNumpy(),
                "wind_speed_max_10m_kmh": daily.Variables(8).ValuesAsNumpy(),
                "wind_gusts_max_10m_kmh": daily.Variables(9).ValuesAsNumpy(),
                "shortwave_radiation_sum_mj_m2": daily.Variables(10).ValuesAsNumpy(),
            }))

        # write THIS arrondissement immediately
        arr_hourly_df = pd.concat(arr_hourly, ignore_index=True)
        arr_daily_df = pd.concat(arr_daily, ignore_index=True)
        con.execute("insert into raw.raw_hourly select * from arr_hourly_df")
        con.execute("insert into raw.raw_daily select * from arr_daily_df")
        print(f"✅ {arr_name} : {len(arr_hourly_df)} lignes horaires écrites")

    except Exception as e:
        print(f"⚠️ {arr_name} sauté : {e}")
        con.execute(
            "insert into raw.extraction_failures values (?, ?, ?)",
            [arr_name, str(e), pd.Timestamp.now()]
        )
        time.sleep(config.SLEEP_ON_ERROR_SEC)
        continue

    time.sleep(config.SLEEP_BETWEEN_REQUESTS_SEC)

print("\n✅ Extraction terminée.")
print(con.execute("select count(*) from raw.raw_hourly").fetchone())
print(con.execute("select count(*) from raw.raw_daily").fetchone())