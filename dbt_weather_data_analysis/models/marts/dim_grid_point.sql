-- models/marts/dim_grid_point.sql
{{ config(materialized='table') }}

select
    {{ dbt_utils.generate_surrogate_key(['arrondissement_id', 'point_grid_id']) }} as grid_point_id,
    arrondissement_id,
    arrondissement_name,
    point_grid_id,
    grid_lat,
    grid_lon
from {{ ref('stg_grid_points') }}