-- models/marts/dim_daily.sql
{{config (materialized = 'table')}}
WITH
    dates AS (
        SELECT DISTINCT
            cast(timestamp AS date) AS date
        FROM
            {{ref ('stg_hourly')}}
        UNION
        SELECT DISTINCT
            date
        FROM
            {{ref ('stg_daily')}}
    )
SELECT
    {{dbt_utils.generate_surrogate_key (['date'])}} AS date_id,
    date,
    extract (
        year
        FROM
            date
    ) AS year,
    extract (
        month
        FROM
            date
    ) AS month,
    extract (
        day
        FROM
            date
    ) AS day,
    extract (
        dow
        FROM
            date
    ) AS day_of_week,
    strftime(date, '%A') AS day_name,
    strftime(date, '%B') AS month_name
FROM
    dates