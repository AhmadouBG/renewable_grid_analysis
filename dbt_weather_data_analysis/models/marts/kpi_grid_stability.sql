-- models/marts/kpi_grid_stability.sql
{{ config(materialized='table') }}

with hourly as (
    select
        f.grid_point_id,
        g.arrondissement_id,
        g.arrondissement_name,
        f.date_id,
        f.hour_id,
        h.hour,
        f.shortwave_radiation_w_m2,
        f.precipitation_mm
    from {{ ref('fact_hourly_weather') }} f
    join {{ ref('dim_grid_point') }} g on f.grid_point_id = g.grid_point_id
    join {{ ref('dim_hourly') }} h on f.hour_id = h.hour_id
),

peak_baseline as (
    -- reference: expected clear-sky radiation at peak hour (STC-adjacent ceiling)
    select
        arrondissement_id,
        date_id,
        max(shortwave_radiation_w_m2) as peak_radiation_w_m2
    from hourly
    where hour between {{ var('peak_hour_start') }} and {{ var('peak_hour_end') }}
    group by 1, 2
),

drop_calc as (
    select
        h.*,
        p.peak_radiation_w_m2,
        case
            when p.peak_radiation_w_m2 > 0 then
                (p.peak_radiation_w_m2 - h.shortwave_radiation_w_m2) / p.peak_radiation_w_m2 * 100
            else 0
        end as pct_drop_from_peak
    from hourly h
    join peak_baseline p
        on h.arrondissement_id = p.arrondissement_id
        and h.date_id = p.date_id
    where h.hour between {{ var('peak_hour_start') }} and {{ var('peak_hour_end') }}
)

select
    grid_point_id,
    arrondissement_id,
    arrondissement_name,
    date_id,
    hour_id,
    round(pct_drop_from_peak, 1) as pct_drop_from_peak,

    case when pct_drop_from_peak > {{ var('grid_risk_threshold_pct') }} then 1 else 0 end
        as grid_stability_risk,

    case when pct_drop_from_peak > {{ var('grid_risk_threshold_pct') }} then 1 else 0 end
        as generator_activation_recommended

from drop_calc