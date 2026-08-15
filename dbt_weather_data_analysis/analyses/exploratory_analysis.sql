-- SQL queries investigations
SELECT
    *
FROM
    weather_grid_analysis_database.raw.raw_hourly
LIMIT
    5;

SELECT
    *
FROM
    weather_grid_analysis_database.raw.raw_daily
LIMIT
    5;

SELECT
    *
FROM
    weather_grid_analysis_database.stg_grid_points;

SELECT
    *
FROM
    weather_grid_analysis_database.main_seeds.senegal_arrondissements_location;

-- nombre total d'enregistrements
SELECT
    COUNT(*) AS total
FROM
    weather_grid_analysis_database.raw.raw_hourly;

-- nombre total d'enregistrements
SELECT
    COUNT(*) AS total
FROM
    weather_grid_analysis_database.raw.raw_daily;

-- verifier les colonnes et leurs types
DESCRIBE weather_grid_analysis_database.raw.raw_hourly;

-- verifier les colonnes et leurs types
DESCRIBE weather_grid_analysis_database.raw.raw_daily;

--
DESCRIBE weather_grid_analysis_database.main_seeds.senegal_arrondissements_location;

--
DESCRIBE weather_grid_analysis_database.stg_grid_points;

-- NUMBER OF POINT GRID
SELECT
    COUNT(DISTINCT point_grid_id) AS total
FROM
    weather_grid_analysis_database.raw.raw_hourly;

-- NOMBRE OF ARRONDISSEMENT
SELECT
    COUNT(DISTINCT arrondissement_name) AS total
FROM
    weather_grid_analysis_database.raw.raw_hourly;

SELECT DISTINCT
    COUNT(NOM) AS total,
    NOM AS arrondissement_name
FROM
    weather_grid_analysis_database.main_seeds.senegal_arrondissements_location
GROUP BY
    NOM
HAVING
    arrondissement_name NOT IN (
        SELECT DISTINCT
            arrondissement_name
        FROM
            weather_grid_analysis_database.raw.raw_hourly
    );

SELECT
    COUNT(*) AS total
FROM
    weather_grid_analysis_database.main_seeds.senegal_arrondissements_location;

SELECT
    COUNT(*)
FROM
    weather_grid_analysis_database.stg_grid_points;

-- RAPPORT ANALYSES:
-- Pas de cle primaire: (raw_hourly, raw_daily)
-- les arrondissements n'ont aucune valeur nulles (aucun null values)
-- il y a pas de temperature negatif par heure ni de valeur superieur a 50 (ceux qui est normal)
-- l'arrondissement 'saldé' n'est pas dans les tables
SELECT
    arrondissement_id,
    point_grid_id,
    grid_lat,
    grid_lon
FROM
    weather_grid_analysis_database.stg_grid_points;

SELECT
    FID,
    NOM,
    SUM_SUPERF,
    SHAPE_LENG,
    latitude,
    longitude
FROM
    weather_grid_analysis_database.main_seeds.senegal_arrondissements_location