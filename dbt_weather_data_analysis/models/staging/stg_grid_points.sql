WITH
    base AS (
        SELECT
            nom,
            latitude,
            longitude,
            sum_superf,
            shape_leng,
            1.0 / {{var ('km_per_deg_lat')}} AS deg_lat_per_km,
            1.0 / (
                {{var ('km_per_deg_lat')}} * cos(radians(latitude))
            ) AS deg_lon_per_km,
            SQRT(sum_superf) / 2 AS offset_km
        FROM
            {{ref ('senegal_arrondissements_location')}}
    ),
    grid AS (
        SELECT
            b.nom AS arrondissement_name,
            b.latitude AS centroid_lat,
            b.longitude AS centroid_lon,
            b.sum_superf AS arrondissement_area_km2,
            b.shape_leng AS arrondissement_perimeter_km2,
            row_number() over (
                PARTITION BY
                    b.nom
                ORDER BY
                    dx.coef,
                    dy.coef
            ) AS point_grid_id,
            b.latitude + (dx.coef * b.offset_km * b.deg_lat_per_km) AS grid_lat,
            b.longitude + (dy.coef * b.offset_km * b.deg_lon_per_km) AS grid_lon
        FROM
            base b
            CROSS JOIN {{ref ('grid_coefficients')}} dx
            CROSS JOIN {{ref ('grid_coefficients')}} dy
    )
SELECT
    *
FROM
    grid