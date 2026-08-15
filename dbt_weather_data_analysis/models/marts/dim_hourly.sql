-- models/marts/dim_hourly.sql
{{config (materialized = 'table')}}
SELECT
    hour AS hour_id,
    hour,
    CASE
        WHEN hour BETWEEN 6 AND 11  THEN 'Matin'
        WHEN hour BETWEEN 12 AND 17  THEN 'Après-midi'
        WHEN hour BETWEEN 18 AND 21  THEN 'Soir'
        ELSE 'Nuit'
    END AS period_of_day
FROM
    (
        SELECT
            unnest(generate_series(0, 23)) AS hour
    )