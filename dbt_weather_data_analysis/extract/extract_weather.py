import duckdb
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
import time
import config

con = duckdb.connect("output/weather_grid_analysis_database.duckdb")
grid_df = con.execute("select * from stg_grid_points").df()

cache_session = requests_cache.CachedSession(config.CACHE_PATH, expire_after=config.CACHE_EXPIRE_AFTER_SEC)
retry_session = retry(cache_session, retries=config.RETRY_COUNT, backoff_factor=config.RETRY_BACKOFF_FACTOR)
openmeteo = openmeteo_requests.Client(session=retry_session)

hourly_raw = []
daily_raw = []

for arr_name, group in grid_df.groupby("arrondissement_name"):
    params = {
        "latitude": group["grid_lat"].tolist(),
        "longitude": group["grid_lon"].tolist(),
        "hourly": config.HOURLY_VARIABLES,
        "daily": config.DAILY_VARIABLES,
        "timezone": config.TIMEZONE,
        "past_days": config.PAST_DAYS,
        "forecast_days": config.FORECAST_DAYS,
    }
    try:
        responses = openmeteo.weather_api(config.API_URL, params=params)
    except Exception as e:
        print(f"⚠️ Arrondissement {arr_name} sauté temporairement (Erreur API) : {e}")
        time.sleep(config.SLEEP_ON_ERROR_SEC)
        continue

    for p_idx, response in enumerate(responses):
        point_id = group.iloc[p_idx]["point_grid_id"]

        hourly = response.Hourly()
        h_dates = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True).tz_convert(config.TIMEZONE),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True).tz_convert(config.TIMEZONE),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
        hourly_raw.append(pd.DataFrame({
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
        daily_raw.append(pd.DataFrame({
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
    time.sleep(config.SLEEP_BETWEEN_REQUESTS_SEC)


final_hourly = pd.concat(hourly_raw, ignore_index=True)
final_daily = pd.concat(daily_raw, ignore_index=True)

con.execute("create schema if not exists raw")
con.execute("create or replace table raw.raw_hourly as select * from final_hourly")
con.execute("create or replace table raw.raw_daily as select * from final_daily")
con.close()