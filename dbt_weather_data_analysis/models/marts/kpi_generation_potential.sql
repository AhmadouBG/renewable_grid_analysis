-- models/marts/kpi_potential.sql
{{ config(materialized='table') }}

with base as (
    select
        f.grid_point_id,
        f.date_id,
        f.hour_id,
        g.arrondissement_id,
        f.temperature_2m,
        f.shortwave_radiation_w_m2,
        f.wind_speed_80m_kmh,
        f.wind_speed_80m_kmh / 3.6 as wind_speed_ms
    from {{ ref('fact_hourly_weather') }} f
    join {{ ref('dim_grid_point') }} g
        on f.grid_point_id = g.grid_point_id
),

calc as (
    select
        *,

        -- SOLAR: cell temperature via NOCT (Skoplaki et al. 2008 / Sun et al. 2020)
        temperature_2m
            + ((({{ var('pv_noct_c') }} - 20.0) / 800.0) * shortwave_radiation_w_m2)
            as cell_temp_c,

        -- SOLAR: normalized score, 0-100, based on irradiance vs STC (resource availability only)
        least(100.0, greatest(0.0,
            (shortwave_radiation_w_m2 / {{ var('solar_reference_irradiance_w_m2') }}) * 100
        )) as solar_score,

        -- WIND: power density (W/m^2) via 0.5 * rho * v^3
        0.5 * {{ var('air_density_kg_m3') }} * power(wind_speed_ms, 3) as wind_power_density_w_m2,

        -- WIND: normalized score, 0-100, cubic ramp between cut-in and rated speed
        case
            when wind_speed_ms < {{ var('wind_cutin_speed_ms') }} then 0.0
            when wind_speed_ms >= {{ var('wind_rated_speed_ms') }} then 100.0
            else
                least(100.0, greatest(0.0,
                    (power(wind_speed_ms, 3) - power({{ var('wind_cutin_speed_ms') }}, 3))
                    / (power({{ var('wind_rated_speed_ms') }}, 3) - power({{ var('wind_cutin_speed_ms') }}, 3))
                    * 100
                ))
        end as wind_score

    from base
),

final as (
    select
        *,

        -- SOLAR: performance ratio, temperature-derated (Jerez et al. 2015)
        1 + ({{ var('pv_gamma_per_c') }} * (cell_temp_c - {{ var('pv_tstc_c') }}))
            as performance_ratio,

        -- SOLAR: raw production estimate, kWh per hour per 1 kW installed (Mavromatakis et al. 2010)
        {{ var('pv_nominal_power_kw') }}
            * (1 + ({{ var('pv_gamma_per_c') }} * (cell_temp_c - {{ var('pv_tstc_c') }})))
            * (shortwave_radiation_w_m2 / {{ var('solar_reference_irradiance_w_m2') }})
            as solar_output_kwh_per_kw

    from calc
)

select
    grid_point_id,
    arrondissement_id,
    date_id,
    hour_id,

    round(shortwave_radiation_w_m2, 1)     as shortwave_radiation_w_m2,
    round(temperature_2m, 1)               as temperature_2m,
    round(cell_temp_c, 1)                  as cell_temp_c,
    round(performance_ratio, 4)            as performance_ratio,
    round(solar_output_kwh_per_kw, 4)      as solar_output_kwh_per_kw,
    round(solar_score, 1)                  as solar_score,

    round(wind_speed_ms, 2)                as wind_speed_ms,
    round(wind_power_density_w_m2, 1)      as wind_power_density_w_m2,
    round(wind_score, 1)                   as wind_score,

    round((coalesce(solar_score, 0) + coalesce(wind_score, 0)) / 2, 1) as kpi_potential_score

from final