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
    where h.hour between {{ var('peak_hour_start') }} and {{ var('peak_hour_end') }}
),

drop_calc as (
    select
        *,
        {{ var('clear_sky_peak_radiation_w_m2') }} as clear_sky_reference_w_m2,

        least(100.0, greatest(0.0,
            ({{ var('clear_sky_peak_radiation_w_m2') }} - shortwave_radiation_w_m2)
            / {{ var('clear_sky_peak_radiation_w_m2') }} * 100
        )) as pct_drop_from_clear_sky

    from hourly
),

flagged as (
    select
        *,
        case when pct_drop_from_clear_sky > {{ var('grid_risk_threshold_pct') }} then 1 else 0 end
            as grid_stability_risk
    from drop_calc
),

persistence as (
    select
        *,
        -- FIX: partition by grid_point_id, not just arrondissement_id
        hour - row_number() over (
            partition by grid_point_id, date_id, grid_stability_risk
            order by hour
        ) as risk_grp
    from flagged
),

persistence_counted as (
    select
        *,
        count(*) over (partition by grid_point_id, date_id, risk_grp) as consecutive_risk_hours
    from persistence
    where grid_stability_risk = 1
)

select
    f.grid_point_id,
    f.arrondissement_id,
    f.arrondissement_name,
    f.date_id,
    f.hour_id,
    f.hour,
    round(f.shortwave_radiation_w_m2, 1)   as shortwave_radiation_w_m2,
    f.clear_sky_reference_w_m2,
    round(f.pct_drop_from_clear_sky, 1)    as pct_drop_from_clear_sky,
    f.grid_stability_risk,

    coalesce(
        (select 1
         from persistence_counted pc
         where pc.grid_point_id = f.grid_point_id     -- FIX: added
           and pc.date_id = f.date_id
           and pc.hour_id = f.hour_id
           and pc.consecutive_risk_hours >= {{ var('grid_risk_persistence_hours') }}
        ), 0
    ) as generator_activation_recommended

from flagged f