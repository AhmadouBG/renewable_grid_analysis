-- models/marts/fact_hourly_air_quality.sql
{{ config(materialized='table') }}

select
    g.grid_point_id,
    d.date_id,
    h.hour_id,
    f.pm10,
    f.pm2_5,
    f.dust
from {{ ref('stg_air_quality') }} f
join {{ ref('dim_grid_point') }} g
    on f.arrondissement_id = g.arrondissement_id
    and f.point_grid_id = g.point_grid_id
join {{ ref('dim_daily') }} d
    on cast(f.timestamp as date) = d.date
join {{ ref('dim_hourly') }} h
    on extract(hour from f.timestamp) = h.hour_id