-- models/marts/fact_hourly_air_quality.sql
{{ config(materialized='table') }}

SELECT
    g.grid_point_id,
    d.date_id,
    h.hour_id,
    f.pm10,
    f.pm2_5,
    f.dust
FROM {{ ref('stg_air_quality') }} f
JOIN {{ ref('dim_grid_point') }} g
    ON f.arrondissement_id = g.arrondissement_id
    AND f.point_grid_id = g.point_grid_id
JOIN {{ ref('dim_daily') }} d
    ON CAST(f.timestamp AS date) = d.date
JOIN {{ ref('dim_hourly') }} h
    ON extract(hour from f.timestamp) = h.hour_id