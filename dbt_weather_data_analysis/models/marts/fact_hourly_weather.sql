-- models/marts/fact_hourly_weather.sql
{{config (materialized = 'table')}}
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
    JOIN {{ref ('dim_date')}} d ON cast(f.timestamp AS date) = d.date
    JOIN {{ref ('dim_hourly')}} h ON extract (
        hour
        FROM
            f.timestamp
    ) = h.hour_id