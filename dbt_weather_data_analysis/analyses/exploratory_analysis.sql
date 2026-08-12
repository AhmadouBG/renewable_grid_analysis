SELECT
    *
FROM
    database_weather.raw.raw_hourly
LIMIT
    5;

SELECT
    *
FROM
    database_weather.raw.raw_daily
LIMIT
    5;

-- nombre total d'enregistrements
SELECT
    COUNT(*) AS total
FROM
    database_weather.raw.raw_hourly;

-- nombre total d'enregistrements
SELECT
    COUNT(*) AS total
FROM
    database_weather.raw.raw_daily;

-- verifier les colonnes et leurs types
DESCRIBE database_weather.raw.raw_hourly;

-- verifier les colonnes et leurs types
DESCRIBE database_weather.raw.raw_daily;

-- NUMBER OF POINT GRID
SELECT
    COUNT(DISTINCT point_grid_id) AS total
FROM
    database_weather.raw.raw_hourly;

-- NOMBRE OF ARRONDISSEMENT
SELECT
    COUNT(DISTINCT arrondissement_name) AS total
FROM
    database_weather.raw.raw_hourly;

SELECT DISTINCT
    NOM AS arrondissement_name
FROM
    database_weather.main_seeds.senegal_arrondissements_location
WHERE
    arrondissement_name NOT IN (
        SELECT DISTINCT
            arrondissement_name
        FROM
            database_weather.raw.raw_hourly
    );

SELECT
    COUNT(*) AS total
FROM
    database_weather.main_seeds.senegal_arrondissements_location;

SELECT
    arrondissement_name,
    COUNT(*) AS total
FROM
    database_weather.stg_grid_points
GROUP BY
    arrondissement_name
HAVING
    arrondissement_name = 'saldé';

-- RAPPORT ANALYSES:
-- Pas de cle primaire: (timestamp, arrondissement_name, point_grid_id) mais on peut la creer avec md5
-- les arrondissements n'ont aucune valeur nulles (aucun null values)
-- il y a pas de temperature negatif par heure ni de valeur superieur a 50 (ceux qui est normal)
-- l'arrondissement 'saldé' n'est pas dans la table raw_daily and raw_hourly (ceux qui n'est pas normal)