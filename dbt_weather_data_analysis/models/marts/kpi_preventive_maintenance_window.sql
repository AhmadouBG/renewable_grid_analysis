-- models/marts/kpi_preventive_maintenance_window.sql
{{ config(materialized='table') }}

WITH combined AS (
    SELECT
        w.grid_point_id,
        g.arrondissement_id,
        g.arrondissement_name,
        w.date_id,
        w.hour_id,
        h.hour,
        w.wind_speed_80m_kmh,
        w.precipitation_mm,
        aq.pm10
    FROM {{ref('fact_hourly_weather')}} w
    JOIN {{ref('dim_grid_point')}} g ON w.grid_point_id = g.grid_point_id
    JOIN {{ref('dim_hourly')}} h ON w.hour_id = h.hour_id
    LEFT JOIN {{ref('fact_hourly_air_quality')}} aq
        ON w.grid_point_id = aq.grid_point_id
        AND w.date_id = aq.date_id
        AND w.hour_id = aq.hour_id
),

flagged AS (
    SELECT
        *,
        (wind_speed_80m_kmh <= {{ var('maintenance_max_wind_kmh') }})
            AND (precipitation_mm = 0)
            AND (coalesce(pm10, 0) <= {{ var('maintenance_max_pm10') }})
            AS is_ideal_hour
    FROM combined
)

SELECT
    arrondissement_id,
    arrondissement_name,
    date_id,
    hour_id,
    hour,
    wind_speed_80m_kmh,
    precipitation_mm,
    pm10,
    is_ideal_hour
FROM flagged