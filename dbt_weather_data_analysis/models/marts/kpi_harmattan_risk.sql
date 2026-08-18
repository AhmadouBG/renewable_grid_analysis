-- models/marts/kpi_harmattan_risk.sql
{{ config(materialized='table') }}

SELECT
    aq.grid_point_id,
    g.arrondissement_id,
    g.arrondissement_name,
    aq.date_id,
    aq.hour_id,
    aq.pm10,
    aq.dust,

    CASE
        WHEN aq.pm10 >= {{ var('harmattan_pm10_severe') }} THEN 100
        WHEN aq.pm10 >= {{ var('harmattan_pm10_moderate') }} THEN 60
        WHEN aq.pm10 >= {{ var('harmattan_pm10_light') }} THEN 30
        ELSE 0
    END AS harmattan_risk_score

FROM {{ ref('fact_hourly_air_quality') }} aq
JOIN {{ ref('dim_grid_point') }} g ON aq.grid_point_id = g.grid_point_id