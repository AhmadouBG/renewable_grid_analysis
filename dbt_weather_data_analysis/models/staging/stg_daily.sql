WITH
    source_data AS (
        SELECT
            *
        FROM
            {{source ('raw', 'raw_daily')}}
    ),
    transform_data_daily AS (
        SELECT
            date,
            arrondissement_name,
            point_grid_id,
            latitude,
            longitude,
            temp_max_2m,
            temp_mean_2m,
            temp_min_2m,
            precipitation_sum_mm,
            rain_sum_mm,
            precipitation_probability_max_pct,
            sunshine_duration_sec,
            daylight_duration_sec,
            wind_speed_max_10m_kmh,
            wind_gusts_max_10m_kmh,
            shortwave_radiation_sum_mj_m2,
            CASE
                WHEN shortwave_radiation_sum_mj_m2 >= {{var ('radiation_sunny_threshold')}} THEN 'Ensoleillé'
                WHEN shortwave_radiation_sum_mj_m2 < {{var ('radiation_cloudy_threshold')}} THEN 'Non Ensoleillé'
                ELSE 'Éclaircies / Mixte'
            END AS etat_ensoleillement,
        FROM
            source_data
    )
SELECT
    *
FROM
    transform_data_daily