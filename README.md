# ⚡ Renewable Grid Analysis

> **End-to-end data pipeline** that ingests weather & air-quality data, transforms it with dbt, orchestrates with Apache Airflow, and surfaces KPIs for renewable-energy grid planning in Senegal / West Africa via Power BI.

**Data Source (geo):** [Le Géoportail du Sénégal — Limite administrative](https://senegal.africageoportal.com/maps/6ec9d1cf60944eaba2ec776147270ddb/about) (04/08/2026)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Data](#Data)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Pipeline DAG](#pipeline-dag)
- [dbt Data Models](#dbt-data-models)
- [KPIs](#kpis)
- [Power BI Dashboard](#power-bi-dashboard)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)

---

## Overview

This project builds a fully automated pipeline to support renewable energy grid planning decisions in Senegal. It:

1. **Extracts** hourly & daily weather data (wind speed, solar radiation, temperature, humidity) and air-quality data (PM2.5, AQI) from the [Open-Meteo API](https://open-meteo.com/) for a set of grid points across Senegal.
2. **Stages & transforms** raw data through a multi-layer dbt project (staging → dimensions → facts → marts/KPIs) stored in DuckDB.
3. **Orchestrates** all steps on a bi-daily schedule via an Apache Airflow DAG running in Docker.
4. **Exports** final mart tables as Parquet files for Power BI consumption.

---
## Data

#### Daily:

| Variable | Type | Description |
|---|---|---|
| arrondissement_name | varchar | Name of the arrondissement |
| point_grid_id | bigint | Unique identifier of the grid point |
| latitude | double | Latitude of the grid point |
| longitude | double | Longitude of the grid point |
| temp_max_2m | float | Maximum daily air temperature at 2 meters above ground |
| temp_mean_2m | float | Mean daily air temperature at 2 meters above ground |
| temp_min_2m | float | Minimum daily air temperature at 2 meters above ground |
| precipitation_sum_mm | float | Sum of daily precipitation |
| rain_sum_mm | float | Sum of daily rainfall |
| precipitation_probability_max_pct | float | Maximum daily precipitation probability |
| sunshine_duration_sec | float | Daily sum of sunshine duration |
| daylight_duration_sec | float | Daily sum of daylight duration |
| wind_speed_max_10m_kmh | float | Maximum daily wind speed at 10 meters |
| wind_gusts_max_10m_kmh | float | Maximum daily wind gusts at 10 meters |
| shortwave_radiation_sum_mj_m2 | float | Daily sum of shortwave radiation |

#### Hourly:

| Variable | Type | Description |
|---|---|---|
| arrondissement_name | varchar | Name of the arrondissement |
| point_grid_id | bigint | Unique identifier of the grid point |
| latitude | double | Latitude of the grid point |
| longitude | double | Longitude of the grid point |
| temperature_2m | float | Temperature at 2 meters above ground |
| cloud_cover_pct | float | Cloud cover percentage |
| direct_radiation_w_m2 | float | Direct radiation in Watts per square meter |
| shortwave_radiation_w_m2 | float | Shortwave radiation in Watts per square meter |
| wind_speed_80m_kmh | float | Wind speed at 80 meters in kilometers per hour |
| wind_direction_80m_deg | float | wind direction |
| precipitation_mm | float | precipitation |
| visibility_m | float | visibility |
| weather_code_wmo | float | weather code |
---
## Architecture

```
Open-Meteo API
      │
      ▼
 Python Extractors
 (extract_weather.py / extract_air_quality.py)
      │
      ▼
  DuckDB (local analytical DB)
      │
      ▼
  dbt Transformations
  ┌─────────────────────────────────────────────────────┐
  │  Staging  →  Dimensions  →  Facts  →  Marts / KPIs  │
  └─────────────────────────────────────────────────────┘
      │
      ▼
  Parquet Export  ──→  Power BI Dashboard
      ▲
      │
  Apache Airflow (Docker, CeleryExecutor — schedules & runs all tasks)
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Orchestration | Apache Airflow 3.3.1 (CeleryExecutor) |
| Transformation | dbt-core 1.12.0 |
| Database | DuckDB 1.10.1 |
| Data Source | Open-Meteo API |
| Geospatial | GeoPandas, Shapely, PyProj |
| Containerisation | Docker / Docker Compose |
| Visualisation | Power BI |
| Language | Python 3.x |

---

## Project Structure

```
renewable_grid_analysis/
├── dags/
│   ├── weather_pipeline_dag.py        # Main scheduled DAG (every 2 days @ 6am)
│   └── weather_pipeline_reset.py      # Utility DAG to reset/reinitialise
├── dbt_weather_data_analysis/
│   ├── models/
│   │   ├── staging/                   # Raw → cleaned & typed
│   │   │   ├── stg_hourly.sql
│   │   │   ├── stg_daily.sql
│   │   │   ├── stg_air_quality.sql
│   │   │   └── stg_grid_points.sql
│   │   └── marts/                     # Business-ready tables & KPIs
│   │       ├── dim_daily.sql
│   │       ├── dim_hourly.sql
│   │       ├── dim_grid_point.sql
│   │       ├── fact_hourly_weather.sql
│   │       ├── fact_daily_weather.sql
│   │       ├── fact_hourly_air_quality.sql
│   │       ├── kpi_generation_potential.sql
│   │       ├── kpi_grid_stability.sql
│   │       ├── kpi_harmattan_risk.sql
│   │       └── kpi_preventive_maintenance_window.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── extract/                           # Python extraction scripts
├── config/
│   └── airflow.cfg
├── output/                            # Parquet export destination (Power BI source)
├── docs/                              # ← PUT YOUR SCREENSHOTS & VIDEOS HERE
│   ├── airflow/                       # Airflow DAG screenshots & screen recordings
│   └── powerbi/                       # Power BI dashboard screenshots & screen recordings
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
└── .env
```

---

## Pipeline DAG

**DAG ID:** `weather_pipeline_ingest`  
**Schedule:** Every 2 days at 06:00 UTC (`0 6 */2 * *`)

### Task Graph

```
extract_weather
      │
      ▼
extract_air_quality
      │
      ▼
dbt_staging          (stg_hourly, stg_daily, stg_air_quality)
      │
      ▼
dbt_build_dims       (dim_daily, dim_hourly)
      │
      ▼
dbt_facts            (fact_hourly_weather, fact_daily_weather, fact_hourly_air_quality)
      │
      ▼
dbt_marts            (KPI models & remaining marts)
      │
      ▼
dbt_test             (dbt data quality tests)
      │
      ▼
export_parquet       (writes Parquet files to /output)
```

### 📸 Airflow DAG — Screenshots & Video

> **How to add media:**
> 1. Create the folder `docs/airflow/` in the project root.
> 2. Drop your files in using the filenames below.
> 3. Uncomment the matching image lines in this README.
>
> | Suggested filename | What to capture |
> |---|---|
> | `dag_graph_view.png` | DAG graph view from the Airflow UI |
> | `dag_gantt.png` | Gantt / timeline view of a successful run |
> | `dag_run_log.png` | Task log showing a green/successful run |
> | `dag_demo.gif` | Screen recording of a live DAG run (convert mp4 → gif with e.g. [gifski](https://gif.ski/)) |

<!-- Airflow DAG Graph View -->
<!-- ![DAG Graph View](docs/airflow/dag_graph_view.png) -->

<!-- Airflow Gantt / Timeline -->
<!-- ![DAG Gantt View](docs/airflow/dag_gantt.png) -->

<!-- Airflow Demo Recording -->
<!-- ![DAG Demo](docs/airflow/dag_demo.gif) -->

---

## dbt Data Models

### Staging
| Model | Description |
|---|---|
| `stg_hourly` | Hourly weather readings (wind, solar, temperature, humidity) |
| `stg_daily` | Daily aggregated weather |
| `stg_air_quality` | Hourly air-quality readings (PM2.5, AQI) |
| `stg_grid_points` | Reference grid points (lat/lon) across Senegal |

### Dimensions
| Model | Description |
|---|---|
| `dim_daily` | Date dimension enriched with seasonal & calendar attributes |
| `dim_hourly` | Hour-level time dimension |
| `dim_grid_point` | Spatial dimension for grid locations |

### Facts
| Model | Description |
|---|---|
| `fact_hourly_weather` | Grain: 1 row per grid point × hour |
| `fact_daily_weather` | Grain: 1 row per grid point × day |
| `fact_hourly_air_quality` | Grain: 1 row per grid point × hour |

### KPI Marts
| Model | Description |
|---|---|
| `kpi_generation_potential` | Solar & wind generation potential scores per location |
| `kpi_grid_stability` | Grid stability risk index based on weather variability |
| `kpi_harmattan_risk` | Harmattan dust-season risk score (affects panel/turbine efficiency) |
| `kpi_preventive_maintenance_window` | Optimal maintenance windows based on weather conditions |

---

## KPIs

The four KPI models answer key operational questions for grid planners:

| KPI | Question answered |
|---|---|
| **Generation Potential** | Which sites and time periods produce the most renewable energy? |
| **Grid Stability** | When is weather variability high enough to threaten grid reliability? |
| **Harmattan Risk** | When does harmattan dust reduce solar panel output significantly? |
| **Preventive Maintenance Window** | When is it safest to take equipment offline for maintenance? |

---

## Power BI Dashboard

The Power BI report connects directly to the Parquet files exported by the pipeline (`output/*.parquet`).

### 📸 Power BI — Screenshots & Video

> **How to add media:**
> 1. Create the folder `docs/powerbi/` in the project root.
> 2. Drop your files in using the filenames below.
> 3. Uncomment the matching image lines in this README.
>
> | Suggested filename | What to capture |
> |---|---|
> | `overview_page.png` | Dashboard landing / overview page |
> | `generation_kpi.png` | Generation potential KPI page |
> | `stability_kpi.png` | Grid stability KPI page |
> | `harmattan_kpi.png` | Harmattan risk page |
> | `maintenance_kpi.png` | Maintenance window page |
> | `dashboard_demo.gif` | Full walkthrough screen recording |

<!-- Power BI Overview Page -->
<!-- ![Power BI Overview](docs/powerbi/overview_page.png) -->

<!-- Generation Potential KPI -->
<!-- ![Generation Potential](docs/powerbi/generation_kpi.png) -->

<!-- Grid Stability KPI -->
<!-- ![Grid Stability](docs/powerbi/stability_kpi.png) -->

<!-- Harmattan Risk -->
<!-- ![Harmattan Risk](docs/powerbi/harmattan_kpi.png) -->

<!-- Maintenance Window -->
<!-- ![Maintenance Window](docs/powerbi/maintenance_kpi.png) -->

<!-- Full Dashboard Demo -->
<!-- ![Dashboard Demo](docs/powerbi/dashboard_demo.gif) -->

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Python 3.10+

### 1 — Clone the repo

```bash
git clone https://github.com/<your-username>/renewable_grid_analysis.git
cd renewable_grid_analysis
```

### 2 — Configure environment variables

Edit `.env` as needed (see [Environment Variables](#environment-variables) below).

### 3 — Start Airflow

```bash
# Initialise the database (first time only)
docker compose up airflow-init

# Start all services
docker compose up -d
```

Airflow UI → **http://localhost:8080** (user: `airflow` / pass: `airflow`)

### 4 — Trigger the pipeline

In the Airflow UI, enable and trigger the **`weather_pipeline_ingest`** DAG, or let it run on its schedule.

### 5 — Inspect dbt models locally (optional)

```bash
cd dbt_weather_data_analysis
pip install -r ../requirements.txt
dbt run --profiles-dir .
dbt test --profiles-dir .
```

### 6 — Open in Power BI

Open your `.pbix` file and point the data source to the **`output/`** folder containing the exported Parquet files.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `AIRFLOW_UID` | ✅ | UID for Airflow containers (default `50000`) |
| `AIRFLOW_IMAGE_NAME` | ✅ | Docker image tag (default `apache/airflow:3.3.1`) |
| `FERNET_KEY` | ✅ | Fernet encryption key for Airflow secrets |
| `_AIRFLOW_WWW_USER_USERNAME` | ⬜ | Admin UI username (default: `airflow`) |
| `_AIRFLOW_WWW_USER_PASSWORD` | ⬜ | Admin UI password (default: `airflow`) |


