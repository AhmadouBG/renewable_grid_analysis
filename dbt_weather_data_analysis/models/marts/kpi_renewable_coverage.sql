-- models/marts/kpi_renewable_coverage.sql
{{ config(materialized='table') }}

SELECT
    g.arrondissement_id,
    g.arrondissement_name,
    f.date_id,

    count(CASE WHEN f.shortwave_radiation_w_m2 >= {{ var('solar_coverage_threshold_w_m2') }} THEN 1 END) AS solar_coverage_hours,

    count(CASE WHEN (f.wind_speed_80m_kmh / 3.6) >= {{ var('wind_cutin_speed_ms') }} THEN 1 END) AS wind_coverage_hours,

    count(CASE WHEN
        f.shortwave_radiation_w_m2 >= {{ var('solar_coverage_threshold_w_m2') }}
        OR (f.wind_speed_80m_kmh / 3.6) >= {{ var('wind_cutin_speed_ms') }}
        THEN 1 END) AS combined_renewable_coverage_hours

FROM {{ ref('fact_hourly_weather') }} f
JOIN {{ ref('dim_grid_point') }} g ON f.grid_point_id = g.grid_point_id
GROUP BY 1, 2, 3