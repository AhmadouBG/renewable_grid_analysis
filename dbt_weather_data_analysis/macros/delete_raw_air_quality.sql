{% macro delete_future_air_quality(cutoff_date='2026-08-29') %}

    {%- set delete_sql -%}
        delete from {{ source('raw', 'raw_air_quality') }}
        where cast(timestamp as date) >= '{{ cutoff_date }}'
    {%- endset -%}

    {% do log("Running: " ~ delete_sql, info=True) %}
    {% do run_query(delete_sql) %}
    {% do log("Deleted raw_air_quality rows with timestamp >= " ~ cutoff_date, info=True) %}

{% endmacro %}
