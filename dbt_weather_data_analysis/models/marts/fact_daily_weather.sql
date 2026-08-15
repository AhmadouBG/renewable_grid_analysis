-- models/marts/fact_daily_weather.sql
{{config (materialized = 'table')}}
SELECT
    g.grid_point_id,
    d.date_id,
    f.temp_max_2m,
    f.temp_mean_2m,
    f.temp_min_2m,
    f.precipitation_sum_mm,
    f.rain_sum_mm,
    f.precipitation_probability_max_pct,
    f.sunshine_duration_sec,
    f.daylight_duration_sec,
    f.wind_speed_max_10m_kmh,
    f.wind_gusts_max_10m_kmh,
    f.shortwave_radiation_sum_mj_m2
FROM
    {{ref ('stg_daily')}} f
    JOIN {{ref ('dim_grid_point')}} g ON f.arrondissement_id = g.arrondissement_id
    AND f.point_grid_id = g.point_grid_id
    JOIN {{ref ('dim_date')}} d ON f.date = d.date