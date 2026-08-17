WITH
    base AS (
        SELECT
            FID AS arrondissement_id,
            nom AS arrondissement_name,
            latitude AS centroid_lat,
            longitude AS centroid_lon,
            sum_superf AS arrondissement_area_km2,
            shape_leng AS arrondissement_perimeter_km2,
            1.0 / {{var ('km_per_deg_lat')}} AS deg_lat_per_km,
            1.0 / (
                {{var ('km_per_deg_lat')}} * cos(radians(latitude))
            ) AS deg_lon_per_km,
            SQRT(sum_superf) / 2 AS offset_km
        FROM
            {{ref ('senegal_arrondissements_location')}}
        WHERE
            latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND sum_superf > 0
    ),
    grid AS (
        SELECT
            b.arrondissement_id,
            b.arrondissement_name,
            row_number() over (
                PARTITION BY
                    b.arrondissement_id
                ORDER BY
                    dx.coef,
                    dy.coef
            ) AS point_grid_id,
            b.centroid_lat + (dx.coef * b.offset_km * b.deg_lat_per_km) AS grid_lat,
            b.centroid_lon + (dy.coef * b.offset_km * b.deg_lon_per_km) AS grid_lon
        FROM
            base b
            CROSS JOIN {{ref ('grid_coefficients')}} dx
            CROSS JOIN {{ref ('grid_coefficients')}} dy
    )
SELECT
    *
FROM
    grid
    -- grille de coordonnees par arrondissement dx/dy pour avoir des points dans les arrondissements