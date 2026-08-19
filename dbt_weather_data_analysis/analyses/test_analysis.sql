
select
    grid_point_id,
    arrondissement_id,
    date_id,
    hour_id,
    solar_score,
    wind_score,
    kpi_potential_score
from weather_grid_analysis_database.main.kpi_generation_potential
where grid_point_id = 'ea66c06c1e1c05fa9f1aa39d98dc5bc1'
order by date_id, hour_id;


--describe the table kpi_grid_stability
select
    grid_point_id,
    arrondissement_id,
    date_id,
    hour_id,
    pct_drop_from_clear_sky,
    grid_stability_risk,
    generator_activation_recommended
from weather_grid_analysis_database.main.kpi_grid_stability
where grid_point_id = 'ea66c06c1e1c05fa9f1aa39d98dc5bc1'
order by date_id, hour_id;

-- Maintenance crew
DESCRIBE weather_grid_analysis_database.main.kpi_harmattan_risk;
DESCRIBE weather_grid_analysis_database.main.kpi_preventive_maintenance_window;

---OPERATION
DESCRIBE weather_grid_analysis_database.main.kpi_generation_potential;
DESCRIBE weather_grid_analysis_database.main.kpi_grid_stability;

SELECT grid_point_id, DATE_ID, HOUR_ID,harmattan_risk_score FROM weather_grid_analysis_database.main.kpi_harmattan_risk 
WHERE grid_point_id = 'ea66c06c1e1c05fa9f1aa39d98dc5bc1'
ORDER BY date_id, hour_id;



