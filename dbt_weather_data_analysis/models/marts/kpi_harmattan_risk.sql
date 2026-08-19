-- models/marts/kpi_harmattan_risk.sql
{{ config(materialized='table') }}

select
    aq.grid_point_id,
    g.arrondissement_id,
    g.arrondissement_name,
    aq.date_id,
    aq.hour_id,
    aq.pm10,
    aq.dust,

    case
        when aq.dust >= {{ var('harmattan_dust_severe') }} then 100
        when aq.dust >= {{ var('harmattan_dust_moderate') }} then 60
        when aq.dust >= {{ var('harmattan_dust_light') }} then 30
        else 0
    end as harmattan_risk_score

from {{ ref('fact_hourly_air_quality') }} aq
join {{ ref('dim_grid_point') }} g on aq.grid_point_id = g.grid_point_id