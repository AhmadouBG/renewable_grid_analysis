-- models/marts/dim_grid_point.sql
{{config (materialized = 'table')}}
SELECT
    {
        {
            dbt_utils.generate_surrogate_key (['arrondissement_id', 'point_grid_id'])
        }
    } AS grid_point_id,
    arrondissement_id,
    arrondissement_name,
    point_grid_id,
    grid_lat,
    grid_lon,
    centroid_lat,
    centroid_lon,
    arrondissement_area_km2,
    arrondissement_perimeter_km2
FROM
    {{ref ('stg_grid_points')}}