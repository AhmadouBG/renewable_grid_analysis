-- models/staging/stg_air_quality.sql
{{ config(materialized='view') }}

select
    a.timestamp,
    trim(a.arrondissement_name) as arrondissement_name,
    a.point_grid_id,
    a.pm10,
    a.pm2_5,
    a.dust,
    s.arrondissement_id
from {{ source('raw', 'raw_air_quality') }} a
join {{ ref('stg_grid_points') }} s
    on trim(a.arrondissement_name) = s.arrondissement_name
    and a.point_grid_id = s.point_grid_id