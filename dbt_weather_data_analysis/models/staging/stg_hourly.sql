WITH
    source_data AS (
        SELECT
            *
        FROM
            {{source ('raw', 'raw_hourly')}}
    ),
    transform_data_hourly AS (
        SELECT
            timestamp,
            arrondissement_name,
            point_grid_id,
            latitude,
            longitude,
            temperature_2m,
            cloud_cover_pct,
            direct_radiation_w_m2,
            shortwave_radiation_w_m2,
            wind_speed_80m_kmh,
            wind_direction_80m_deg,
            precipitation_mm,
            visibility_m,
            visibility_m / 1000.0 AS visibility_km,
            weather_code_wmo,
            CASE
                WHEN shortwave_radiation_w_m2 >= {{var ('radiation_sunny_threshold')}} THEN 'Ensoleillé'
                WHEN shortwave_radiation_w_m2 < {{var ('radiation_cloudy_threshold')}} THEN 'Non Ensoleillé'
                ELSE 'Éclaircies / Mixte'
            END AS etat_ensoleillement,
            visibility_m / 1000.0 <= {{var ('visibility_alert_km')}} AS alerte_visibilite
        FROM
            source_data
    )
SELECT
    *
FROM
    transform_data_hourly