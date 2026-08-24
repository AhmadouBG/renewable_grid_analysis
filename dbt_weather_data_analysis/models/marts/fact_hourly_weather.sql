-- models/marts/fact_hourly_weather.sql
{{ config(
    materialized='incremental',
    unique_key=['grid_point_id', 'date_id', 'hour_id'],
    incremental_strategy='delete+insert'
) }}
SELECT
    g.grid_point_id,
    d.date_id,
    h.hour_id,
    f.temperature_2m,
    f.cloud_cover_pct,
    f.direct_radiation_w_m2,
    f.shortwave_radiation_w_m2,
    f.wind_speed_80m_kmh,
    f.wind_direction_80m_deg,
    f.precipitation_mm,
    f.visibility_m,
    f.weather_code_wmo,
    f.etat_ensoleillement,
    f.alerte_visibilite
FROM
    {{ref ('stg_hourly')}} f
    JOIN {{ref ('dim_grid_point')}} g ON f.arrondissement_id = g.arrondissement_id
    AND f.point_grid_id = g.point_grid_id
    JOIN {{ref ('dim_daily')}} d ON cast(f.timestamp AS date) = d.date
    JOIN {{ref ('dim_hourly')}} h ON extract (
        hour
        FROM
            f.timestamp
    ) = h.hour_id

{% if is_incremental() %}
where cast(f.timestamp as date) >=
        (select max(d2.date) - interval '2 days' 
        from {{ this }} t
        join {{ ref('dim_daily') }} d2 on t.date_id = d2.date_id)
{% endif %}