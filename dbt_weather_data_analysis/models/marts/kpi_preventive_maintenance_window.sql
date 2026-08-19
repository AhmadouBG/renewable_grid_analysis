-- models/marts/kpi_preventive_maintenance_window.sql
{{ config(materialized='table') }}

with arrondissement_hourly as (
    select
        g.arrondissement_id,
        g.arrondissement_name,
        w.date_id,
        w.hour_id,
        h.hour,
        avg(w.wind_speed_80m_kmh) as avg_wind_speed_80m_kmh,
        sum(w.precipitation_mm)   as total_precipitation_mm,   -- any rain anywhere counts as rain
        avg(aq.pm10)              as avg_pm10
    from {{ ref('fact_hourly_weather') }} w
    join {{ ref('dim_grid_point') }} g on w.grid_point_id = g.grid_point_id
    join {{ ref('dim_hourly') }} h on w.hour_id = h.hour_id
    left join {{ ref('fact_hourly_air_quality') }} aq
        on w.grid_point_id = aq.grid_point_id
        and w.date_id = aq.date_id
        and w.hour_id = aq.hour_id
    group by 1, 2, 3, 4, 5
)

select
    arrondissement_id,
    arrondissement_name,
    date_id,
    hour_id,
    hour,
    round(avg_wind_speed_80m_kmh, 1) as avg_wind_speed_80m_kmh,
    total_precipitation_mm,
    round(avg_pm10, 1) as avg_pm10,

    (avg_wind_speed_80m_kmh <= {{ var('maintenance_max_wind_kmh') }})
        and (total_precipitation_mm = 0)
        and (coalesce(avg_pm10, 0) <= {{ var('maintenance_max_pm10') }})
        as is_ideal_hour

from arrondissement_hourly