-- models/marts/kpi_grid_stability.sql
{{ config(materialized='table') }}

WITH hourly AS (
    SELECT
        f.grid_point_id,
        g.arrondissement_id,
        g.arrondissement_name,
        f.date_id,
        f.hour_id,
        h.hour,
        f.shortwave_radiation_w_m2,
        f.precipitation_mm
    FROM {{ ref('fact_hourly_weather') }} f
    JOIN {{ ref('dim_grid_point') }} g ON f.grid_point_id = g.grid_point_id
    JOIN {{ ref('dim_hourly') }} h ON f.hour_id = h.hour_id
),

peak_baseline AS (
    --REFERENCE: expected clear-sky radiation at peak hour (STC-adjacent ceiling)
    SELECT
        arrondissement_id,
        date_id,
        max(shortwave_radiation_w_m2) AS peak_radiation_w_m2
    FROM hourly
    WHERE hour BETWEEN {{ var('peak_hour_start') }} AND {{ var('peak_hour_end') }}
    GROUP BY 1, 2
),

drop_calc AS (
    SELECT
        h.*,
        p.peak_radiation_w_m2,
        CASE
            WHEN p.peak_radiation_w_m2 > 0 THEN
                (p.peak_radiation_w_m2 - h.shortwave_radiation_w_m2) / p.peak_radiation_w_m2 * 100
            ELSE 0
        END as pct_drop_from_peak
    FROM hourly h
    JOIN peak_baseline p
        ON h.arrondissement_id = p.arrondissement_id
        AND h.date_id = p.date_id
    WHERE h.hour BETWEEN {{ var('peak_hour_start') }} AND {{ var('peak_hour_end') }}
)

SELECT
    grid_point_id,
    arrondissement_id,
    arrondissement_name,
    date_id,
    hour_id,
    round(pct_drop_from_peak, 1) AS pct_drop_from_peak,

    CASE WHEN pct_drop_from_peak > {{ var('grid_risk_threshold_pct') }} THEN 1 
        ELSE 0 
    END AS grid_stability_risk,

    CASE WHEN pct_drop_from_peak > {{ var('grid_risk_threshold_pct') }} THEN 1 
        ELSE 0 
    END AS generator_activation_recommended

FROM drop_calc