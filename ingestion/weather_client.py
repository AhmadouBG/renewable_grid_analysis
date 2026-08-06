import datetime
import math
import os
import time

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

import config

# 1. Configuration du client Open-Meteo avec cache persistant
cache_session = requests_cache.CachedSession(config.CACHE_PATH, expire_after=config.CACHE_EXPIRE_AFTER_SEC)
retry_session = retry(cache_session, retries=config.RETRY_COUNT, backoff_factor=config.RETRY_BACKOFF_FACTOR)
openmeteo = openmeteo_requests.Client(session=retry_session)

try:
    locations_df = pd.read_csv(config.LOCATION_FILE)
except FileNotFoundError:
    print(f"⚠️ Fichier {config.LOCATION_FILE.name} introuvable.")
    exit()

execution_date = datetime.datetime.now().strftime("%Y-%m-%d")

hourly_accumulated = []
daily_accumulated = []

print(f"📡 Extraction sécurisée de l'historique (15 jours) pour {len(locations_df)} arrondissements...")

# 2. Boucle stricte : 1 arrondissement à la fois pour éviter la coupure serveur
for idx, row in locations_df.iterrows():
    print(f"🚀 [{idx + 1}/{len(locations_df)}] Ingestion Grille (16 pts) : {row['NOM']}...")

    # Génération de la grille de 16 points pour CET arrondissement unique
    cote_km = math.sqrt(row['SUM_SUPERF'])
    decalage_km = cote_km / 2
    deg_lat_par_km = 1 / config.KM_PER_DEG_LAT
    deg_lon_par_km = 1 / (config.KM_PER_DEG_LAT * math.cos(math.radians(row['latitude'])))

    grid_latitudes = []
    grid_longitudes = []
    point_ids = []

    p_id = 1
    for dx in config.GRID_COEFFICIENTS:
        for dy in config.GRID_COEFFICIENTS:
            lat_p = row['latitude'] + (dx * decalage_km * deg_lat_par_km)
            lon_p = row['longitude'] + (dy * decalage_km * deg_lon_par_km)
            grid_latitudes.append(lat_p)
            grid_longitudes.append(lon_p)
            point_ids.append(p_id)
            p_id += 1

    # Paramètres de la requête pour les 16 points de cet arrondissement uniquement
    params = {
        "latitude": grid_latitudes,
        "longitude": grid_longitudes,
        "hourly": config.HOURLY_VARIABLES,
        "daily": config.DAILY_VARIABLES,
        "timezone": config.TIMEZONE,
        "past_days": config.PAST_DAYS,
        "forecast_days": config.FORECAST_DAYS
    }

    try:
        # Appel de l'API pour l'arrondissement en cours
        responses = openmeteo.weather_api(config.API_URL, params=params)

        # 3. Traitement des 16 réponses de la grille
        for p_idx, response in enumerate(responses):

            # --- BLOC HORAIRE ---
            hourly = response.Hourly()
            h_dates = pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            )

            loc_hourly_df = pd.DataFrame({
                "timestamp": h_dates,
                "arrondissement_name": row['NOM'],
                "point_grid_id": point_ids[p_idx],
                "latitude": response.Latitude(),
                "longitude": response.Longitude(),
                "arrondissement_area_km2": row['SUM_SUPERF'],
                "arrondissement_perimeter_km2": row['Shape_Leng'],
                "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
                "cloud_cover_pct": hourly.Variables(1).ValuesAsNumpy(),
                "direct_radiation_w_m2": hourly.Variables(2).ValuesAsNumpy(),
                "shortwave_radiation_w_m2": hourly.Variables(3).ValuesAsNumpy(),
                "wind_speed_80m_kmh": hourly.Variables(4).ValuesAsNumpy(),
                "wind_direction_80m_deg": hourly.Variables(5).ValuesAsNumpy(),
                "precipitation_mm": hourly.Variables(6).ValuesAsNumpy(),
                "visibility_m": hourly.Variables(7).ValuesAsNumpy(),
                "visibility_km": hourly.Variables(7).ValuesAsNumpy() / 1000,
                "weather_code_wmo": hourly.Variables(8).ValuesAsNumpy()
            })

            # Logique métier vectorisée
            loc_hourly_df["etat_ensoleillement"] = "Éclaircies / Mixte"
            loc_hourly_df.loc[
                loc_hourly_df["shortwave_radiation_w_m2"] >= config.RADIATION_SUNNY_THRESHOLD_W_M2,
                "etat_ensoleillement"
            ] = "Ensoleillé"
            loc_hourly_df.loc[
                loc_hourly_df["shortwave_radiation_w_m2"] < config.RADIATION_CLOUDY_THRESHOLD_W_M2,
                "etat_ensoleillement"
            ] = "Non Ensoleillé"

            loc_hourly_df["alerte_visibilite"] = False
            loc_hourly_df.loc[
                loc_hourly_df["visibility_km"] <= config.VISIBILITY_ALERT_KM,
                "alerte_visibilite"
            ] = True
            hourly_accumulated.append(loc_hourly_df)

            # --- BLOC JOURNALIER ---
            daily = response.Daily()
            d_dates = pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True).tz_convert(config.TIMEZONE),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            )

            loc_daily_df = pd.DataFrame({
                "date": d_dates.date,
                "arrondissement_name": row['NOM'],
                "point_grid_id": point_ids[p_idx],
                "latitude": response.Latitude(),
                "longitude": response.Longitude(),
                "arrondissement_superf_m2": row['SUM_SUPERF'],
                "temp_max_2m": daily.Variables(0).ValuesAsNumpy(),
                "temp_mean_2m": daily.Variables(1).ValuesAsNumpy(),
                "temp_min_2m": daily.Variables(2).ValuesAsNumpy(),
                "precipitation_sum_mm": daily.Variables(3).ValuesAsNumpy(),
                "rain_sum_mm": daily.Variables(4).ValuesAsNumpy(),
                "precipitation_probability_max_pct": daily.Variables(5).ValuesAsNumpy(),
                "sunshine_duration_sec": daily.Variables(6).ValuesAsNumpy(),
                "daylight_duration_sec": daily.Variables(7).ValuesAsNumpy(),
                "wind_speed_max_10m_kmh": daily.Variables(8).ValuesAsNumpy(),
                "wind_gusts_max_10m_kmh": daily.Variables(9).ValuesAsNumpy(),
                "shortwave_radiation_sum_mj_m2": daily.Variables(10).ValuesAsNumpy()
            })
            daily_accumulated.append(loc_daily_df)

    except Exception as e:
        print(f"⚠️ Arrondissement {row['NOM']} sauté temporairement (Coupure API). Erreur : {e}")
        time.sleep(config.SLEEP_ON_ERROR_SEC)  # Repos étendu si le serveur sature
        continue

    # 4. PAUSE DE SÉCURITÉ : Laisse expirer la fenêtre de requêtes par minute
    time.sleep(config.SLEEP_BETWEEN_REQUESTS_SEC)

# 5. CONSOLIDATION ET CRÉATION DES FICHIERS CSV
if hourly_accumulated and daily_accumulated:
    final_hourly = pd.concat(hourly_accumulated, ignore_index=True)
    final_daily = pd.concat(daily_accumulated, ignore_index=True)

    os.makedirs(config.OUTPUT_HOURLY_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DAILY_DIR, exist_ok=True)

    final_hourly.to_csv(f"{config.OUTPUT_HOURLY_DIR}/grid_weather_fetch_{execution_date}.csv", index=False)
    final_daily.to_csv(f"{config.OUTPUT_DAILY_DIR}/grid_weather_fetch_{execution_date}.csv", index=False)

    print(f"\n✅ REQUÊTAGE ET HISTORISATION RÉUSSIS AVEC SUCCÈS !")
    print(f"Total des lignes Horaires : {len(final_hourly)}")
    print(f"Total des lignes Journalières : {len(final_daily)}")
else:
    print("\n⚠️ Erreur critique : Aucun lot n'a pu être extrait.")