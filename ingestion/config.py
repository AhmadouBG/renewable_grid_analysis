"""
config.py
Configuration centralisée pour api_weather.py (ingestion météo par grille de points).
"""
from pathlib import Path

# --- Chemins ---
GIT_REPO_ROOT = Path(__file__).parent
LOCATION_FILE = GIT_REPO_ROOT / "data" / "senegal_arrondissements_location.csv"

OUTPUT_HOURLY_DIR = "data_lake/grid_weather_hourly"
OUTPUT_DAILY_DIR = "data_lake/grid_weather_daily"

# --- Client Open-Meteo (cache + retry) ---
CACHE_PATH = ".cache"
CACHE_EXPIRE_AFTER_SEC = 86400        # cache persistant de 24h
RETRY_COUNT = 5
RETRY_BACKOFF_FACTOR = 1.5

API_URL = "https://api.open-meteo.com/v1/forecast"

# --- Variables interrogées ---
HOURLY_VARIABLES = [
    "temperature_2m", "cloud_cover", "direct_radiation",
    "shortwave_radiation", "wind_speed_80m", "wind_direction_80m",
    "precipitation", "visibility", "weather_code"
]

DAILY_VARIABLES = [
    "temperature_2m_max", "temperature_2m_mean", "temperature_2m_min",
    "precipitation_sum", "rain_sum", "precipitation_probability_max",
    "sunshine_duration", "daylight_duration", "wind_speed_10m_max",
    "wind_gusts_10m_max", "shortwave_radiation_sum"
]

# --- Fenêtre temporelle et fuseau horaire ---
TIMEZONE = "Africa/Dakar"
PAST_DAYS = 7
FORECAST_DAYS = 7

# --- Génération de la grille de points (16 points = 4x4) par arrondissement ---
GRID_COEFFICIENTS = [-0.9, -0.3, 0.3, 0.9]
KM_PER_DEG_LAT = 111.1  # ~ nombre de km par degré de latitude

# --- Cadence des requêtes (protection anti rate-limit) ---
SLEEP_BETWEEN_REQUESTS_SEC = 3.0
SLEEP_ON_ERROR_SEC = 10

# --- Seuils métier ---
RADIATION_SUNNY_THRESHOLD_W_M2 = 300     # >= : "Ensoleillé"
RADIATION_CLOUDY_THRESHOLD_W_M2 = 150    # <  : "Non Ensoleillé"
VISIBILITY_ALERT_KM = 5.0                # <= : alerte visibilité