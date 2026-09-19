<div align="center">

<img src="branding/team_logo.png" alt="GeoShield Logo" width="200" />

# 🛡️ GeoShield

### AI-Based Landslide Risk Monitoring & Early-Warning Software Platform
**Final-Year Major Project — AI/ML + Communication Engineering | North Eastern Region, India**

![Major Project](https://img.shields.io/badge/Final_Year-Major_Project-green?style=for-the-badge)
![Release](https://img.shields.io/badge/Release-v1.2.0-blue?style=for-the-badge)
![CI](https://github.com/YashAgarwal-31/GeoShield-AI-Landslide-Early-Warning-System/actions/workflows/ci.yml/badge.svg)
![Operational Core](https://img.shields.io/badge/Operational_Core-Sensor_Ingestion-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![AI/ML](https://img.shields.io/badge/AI/ML-Random_Forest-orange?style=for-the-badge)

**Operational software build with persistent data, authenticated gateway ingestion, ML inference, GIS monitoring, alert workflows, desktop packaging, Android packaging, and tested backup/recovery.**

**Current verified release:** `v1.2.0` adds the ACT emergency-communications layer on top of the v1.0 academic freeze baseline. See [docs/COMMUNICATIONS.md](docs/COMMUNICATIONS.md) for SMS/Web Push architecture and [docs/FINAL_PROJECT_FREEZE.md](docs/FINAL_PROJECT_FREEZE.md) for the original freeze policy.

</div>

---

> [!IMPORTANT]
> **Major-project development repository.** This repository is being extended
> and validated by **Yash Agarwal**. Third-party attribution and provenance are
> documented in [NOTICE.md](NOTICE.md), while data lineage and limitations are
> documented in [DATA_PROVENANCE.md](DATA_PROVENANCE.md).

> [!NOTE]
> GeoShield is a fully integrated **major-project software platform** with persistent
> users/stations, SQLite and PostgreSQL support, authenticated external sensor/gateway
> ingestion, ML risk inference, alert persistence, GIS dashboards, and production-style
> Docker verification. Physical sensors are not bundled with the repository, and field
> landslide-warning accuracy still requires calibrated hardware and prospective validation.
>
> For the complete operational setup and real gateway flow, see
> **[OPERATIONAL_GUIDE.md](OPERATIONAL_GUIDE.md)**.

---

## 📋 Table of Contents

1. [Problem Statement](#-problem-statement)
2. [Why Landslides Happen in NER](#-why-landslides-happen-in-ner)
3. [Our Solution](#-our-solution)
4. [System Architecture](#-system-architecture)
5. [AI/ML Model](#-aiml-model)
6. [Real Data Sources](#-real-data-sources)
7. [Frontend Features](#-frontend-features)
8. [Backend API](#-backend-api)
9. [Historical Data Analysis](#-historical-data-analysis)
10. [Early Warning System](#-early-warning-system)
11. [GIS Risk Mapping](#-gis-risk-mapping)
12. [Landslide Simulator](#-landslide-simulator)
13. [Satellite Data Integration](#-satellite-data-integration)
14. [Multilingual Support](#-multilingual-support)
15. [Quick Start](#-quick-start)
16. [Project Structure](#-project-structure)
17. [Tech Stack](#-tech-stack)
18. [Results & Impact](#-results--impact)
19. [Future Roadmap](#-future-roadmap)
20. [Team](#-team)

---

## 🎯 Problem Statement

### The Crisis

The **North Eastern Region (NER)** of India comprises 8 states — Sikkim, Assam, Manipur, Mizoram, Meghalaya, Nagaland, Tripura, and Arunachal Pradesh — home to **45 million people**. This region is geologically young, tectonically active, and receives some of the highest rainfall in the world (Cherrapunji receives 11,777mm annually).

### Why Landslides Happen in NER

Landslides in NER are caused by a complex interplay of **geological, meteorological, and anthropogenic factors**:

```
  LANDSLIDE TRIGGER FACTORS
  ═══════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────┐
  │              GEOLOGICAL FACTORS                     │
  │                                                     │
  │  • Young, weak sedimentary rocks (Tertiary age)     │
  │  • Active tectonic zone (India-Eurasia collision)   │
  │  • Steep slopes (30-60° angles common)             │
  │  • Weathered soil layers over bedrock              │
  │  • Seismic activity (Zone IV-V earthquake zone)    │
  └─────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────┐
  │              METEOROLOGICAL FACTORS                  │
  │                                                     │
  │  • Extreme monsoon rainfall (June-September)        │
  │  • Intense rainfall events (>100mm in 24 hours)    │
  │  • Prolonged saturation of soil layers              │
  │  • Cyclonic storms from Bay of Bengal              │
  │  • Rapid snowmelt in Himalayan zones               │
  └─────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────┐
  │              ANTHROPOGENIC FACTORS                   │
  │                                                     │
  │  • Road construction cutting through slopes         │
  │  • Deforestation for agriculture                    │
  │  • unplanned urbanization on hill slopes            │
  │  • Mining and quarrying activities                  │
  │  • Poor drainage infrastructure                     │
  └─────────────────────────────────────────────────────┘
```

### The Numbers

```
  NER LANDSLIDE IMPACT (2011-2024)
  ═══════════════════════════════════════════════════════

  Total Events:     ████████████████████████████████████████████  44
  Total Deaths:     ████████████████████████████████████████████  88
  Road Blockades:   ████████████████████████████████████████████  31
  People Affected:  ████████████████████████████████████████████  8,087+

  BY STATE (events):
  Sikkim        ████████████████████  8 events  (46 deaths - highest)
  Meghalaya     ██████████████████   7 events  (18 deaths)
  Assam         ████████████████     6 events   (9 deaths)
  Arunachal     ████████████████     6 events   (6 deaths)
  Manipur       ██████████████       5 events   (4 deaths)
  Mizoram       ██████████████       5 events   (3 deaths)
  Nagaland      ██████████           4 events   (2 deaths)
  Tripura       ████████             3 events   (0 deaths)

  TRIGGER BREAKDOWN:
  Rain:      ████████████████████████████████████████  91% (40 events)
  Earthquake ██                                              5% (2 events)
  Flood:     ██                                              5% (2 events)

  SEVERITY:
  Large:     ████████████████████████████  27% (12 events)
  Medium:    ████████████████████████████████████████████  43% (19 events)
  Small:     ████████████████████████████████  30% (13 events)
```

### What's Missing Today

| Gap | Current State | Impact |
|-----|---------------|--------|
| **No centralized monitoring** | Each state handles independently | Delayed response |
| **No AI prediction** | Manual inspection only | Reactive, not preventive |
| **No real-time sensors** | Rain gauges at district level | Missing local events |
| **No multilingual alerts** | English only | 60% population excluded |
| **No citizen reporting** | No mobile infrastructure | Missed early signs |
| **No GIS visualization** | Paper maps | Poor situational awareness |

---

## 🛡️ Our Solution

### GeoShield — A Complete Monitoring Platform

GeoShield is a **full-stack AI-powered landslide monitoring prototype** designed specifically for the North Eastern Region. It combines **authenticated sensor/gateway ingestion**, **live and fallback-labelled geospatial/weather/flood sources**, **machine learning prediction**, **offline-capable field workflows**, and **multilingual warning delivery** in a single platform.

### 6 Core Capabilities

| # | Capability | Description | Technology |
|---|------------|-------------|------------|
| 1 | **Operational Monitoring** | Persistent stations plus authenticated sensor/gateway readings with source provenance, idempotency, readiness checks, and admin provisioning | FastAPI + PostgreSQL/SQLite |
| 2 | **AI Risk Prediction** | Experimental RF+GB VotingClassifier trained on regional and realistically generated terrain samples; independent validation is planned | scikit-learn |
| 3 | **Multi-Channel Warning Communication** | Sensor observation → ML assessment → persistent alert → district-aware WebSocket, Twilio SMS, ntfy and VAPID Web Push, with delivery logging and RBAC controls | WebSocket + Twilio + Web Push |
| 4 | **GIS Risk Mapping** | Interactive Leaflet.js heatmaps showing the prototype risk distribution, road status, village locations, and station profiles | Leaflet.js |
| 5 | **Citizen Reporting** | Geo-tagged photo/video reporting workflow for field officers and local residents | React + FastAPI |
| 6 | **Multilingual UI** | Interface translation in English, Hindi, Bengali, Assamese, and Odia | i18n system |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     🖥️  PRESENTATION LAYER                      │
│                     (React 18 + TypeScript + Tailwind CSS)       │
│                                                                 │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │
│  │  📊       │ │  🗺️       │ │  🚨       │ │  📝       │       │
│  │ Dashboard │ │  GIS Map  │ │  Alerts   │ │ Reports   │       │
│  │           │ │           │ │           │ │           │       │
│  │ • Stats   │ │ • Heatmap │ │ • Filter  │ │ • Submit  │       │
│  │ • Charts  │ │ • Roads   │ │ • Ack     │ │ • View    │       │
│  │ • Rankings│ │ • Villages│ │ • Resolve │ │ • Upload  │       │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘       │
│  ┌─────┴─────┐ ┌─────┴─────┐ ┌─────┴─────┐                    │
│  │  ⚡       │ │  🛰️       │ │  📡       │                    │
│  │ Simulator │ │ Satellite │ │ Station   │                    │
│  │           │ │           │ │           │                    │
│  │ • 4 level │ │ • 20 stn  │ │ • Charts  │                    │
│  │ • AI eval │ │ • Cached  │ │ • AI risk │                    │
│  │ • History │ │ • Demo    │ │ • Weather │                    │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘                    │
├────────┴─────────────┴─────────────┴────────────────────────────┤
│                     ⚙️  BUSINESS LAYER                          │
│                     (Python FastAPI)                             │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    REST API (expanded capability surface)                │   │
│  │                                                          │   │
│  │  /api/dashboard/*    → Stats, heatmap, trends, states   │   │
│  │  /api/sensors/*      → Stations, readings, history      │   │
│  │  /api/alerts/*       → CRUD, acknowledge, resolve       │   │
│  │  /api/reports/*      → Submit, list, verify             │   │
│  │  /api/weather/*      → Current + forecast               │   │
│  │  /api/satellite/*    → Snapshot + live SRTM/Sentinel-2 data │   │
│  │  /api/simulate/*     → Landslide simulation             │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    🤖 AI/ML ENGINE                        │   │
│  │                                                          │   │
│  │  ┌────────────────┐     ┌────────────────┐              │   │
│  │  │  Random Forest │     │    Gradient    │              │   │
│  │  │  200 trees     │     │    Boosting    │              │   │
│  │  │  max_depth=15  │     │    150 trees   │              │   │
│  │  │  balanced      │     │    lr=0.1      │              │   │
│  │  └───────┬────────┘     └───────┬────────┘              │   │
│  │          └──────────┬───────────┘                        │   │
│  │          VotingClassifier (soft, weights=[0.4, 0.6])     │   │
│  │                                                          │   │
│  │  Training: regional + generated samples | 9 features    │   │
│  │  Validation: experimental; independent review pending   │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     💾  DATA LAYER                               │
│                                                                 │
│  ┌───────────┐ ┌───────────────┐ ┌──────────────┐              │
│  │  SQLite   │ │  Open-Meteo   │ │  NASA GLC    │              │
│  │  Database │ │  Satellite API│ │  Landslide   │              │
│  │           │ │               │ │  Catalog     │              │
│  │ • Stations│ │ • Elevation   │ │ • 44 events  │              │
│  │ • Sensors │ │ • Soil moist. │ │ • 8 states   │              │
│  │ • Alerts  │ │ • Rainfall    │ │ • 2011-2024  │              │
│  │ • Reports │ │ • NDVI        │ │              │              │
│  └───────────┘ └───────────────┘ └──────────────┘              │
│  ┌───────────┐ ┌───────────────┐ ┌──────────────┐              │
│  │  Kaggle   │ │  IMD India    │ │  USGS SRTM   │              │
│  │  Datasets │ │  Rainfall     │ │  DEM Data    │              │
│  │           │ │               │ │              │              │
│  │ • 3 files │ │ • District    │ │ • 30m res    │              │
│  │ • 528KB   │ │   rainfall    │ │ • Ready to   │              │
│  │           │ │ • 1901-2015   │ │   integrate  │              │
│  └───────────┘ └───────────────┘ └──────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 AI/ML Model

### Why Machine Learning for Landslide Prediction?

Traditional landslide susceptibility mapping relies on **static geological maps** and **manual expert assessment**. This approach:
- Cannot adapt to changing weather conditions
- Requires expensive field surveys
- Takes weeks to produce results
- Cannot provide real-time predictions

GeoShield's prototype explores these problems by:
- Processing **seeded and simulated sensor readings**
- Learning from a mix of **regional and realistically generated samples**
- Returning interactive demonstration predictions
- Representing seasonal monsoon-related features

### Model Architecture

```
  VOTING CLASSIFIER ENSEMBLE
  ═══════════════════════════════════════════════════════

  Input Features (9):
  ┌─────────────────────────────────────────────────────┐
  │ slope │ elevation │ aspect │ rainfall_daily │       │
  │ rainfall_7day │ ndvi │ soil_moisture │              │
  │ distance_to_road │ month                            │
  └─────────────────────────────────────────────────────┘
         │                         │
         ▼                         ▼
  ┌──────────────┐        ┌──────────────┐
  │   Random     │        │   Gradient   │
  │   Forest     │        │   Boosting   │
  │              │        │              │
  │ 200 trees    │        │ 150 trees    │
  │ max_d=15     │        │ max_d=8      │
  │ balanced     │        │ lr=0.1       │
  │ min_split=5  │        │ min_split=5  │
  │              │        │              │
  │ Weight: 0.4  │        │ Weight: 0.6  │
  └──────┬───────┘        └──────┬───────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────┐
         │  Soft Voting      │
         │  (probability     │
         │   averaging)      │
         └─────────┬─────────┘
                   ▼
         ┌───────────────────┐
         │  Risk Score: 0-100│
         │  Level: L/M/H/C   │
         │  Probability: 0-1 │
         └───────────────────┘
```

### Feature Importance

```
  FEATURE IMPORTANCE RANKING
  ═══════════════════════════════════════════════════════

  1. Slope Angle     ██████████████████████████  25%
     Why: Steeper slopes have higher shear stress
     Source: live SRTM when available; cached regional fallback otherwise

  2. Daily Rainfall  ████████████████████        20%
     Why: Primary trigger for most NER landslides
     Source: Open-Meteo-compatible weather field

  3. Soil Moisture   ███████████████             15%
     Why: Saturated soil loses cohesive strength
     Source: Open-Meteo-compatible soil-moisture field

  4. 7-Day Rainfall  ███████████████             15%
     Why: Cumulative saturation effect
     Source: Open-Meteo hourly rainfall (7 days)

  5. NDVI Index      ███████████████             15%
     Why: Low vegetation = exposed soil = high risk
     Source: live Sentinel-2 L2A when available; cached estimated fallback otherwise

  6. Elevation       ██████████                  10%
     Why: Higher elevations have more potential energy
     Source: Open-Meteo elevation API (real)
```

### Risk Classification Thresholds

| Level | Score Range | Color | Response |
|-------|-------------|-------|----------|
| 🟢 **Low** | 0 - 25 | Green | Normal monitoring, routine checks |
| 🟡 **Moderate** | 25 - 50 | Amber | Enhanced monitoring, notify DDM authority |
| 🟠 **High** | 50 - 75 | Orange | Pre-position rescue teams, voluntary evacuation |
| 🔴 **Critical** | 75 - 100 | Red | IMMEDIATE EVACUATION, deploy emergency response |

### Model Performance

The inference pipeline and four risk classes are functional, but the existing
training data have mixed provenance and severe class imbalance. The upstream
accuracy figures are therefore excluded from this adaptation's verified results.
The Phase 2 evaluator now provides a checksum-bound data audit, majority-class
baseline, district-disjoint holdout, and five-fold grouped validation with
balanced accuracy, precision, recall, F1, ROC-AUC, PR-AUC, and a confusion
matrix. See [`datasets/evaluation/README.md`](datasets/evaluation/README.md).
These metrics describe generated/derived labels and are not field accuracy.

---

## 🛰️ Data Sources and Live Integrations

### Satellite & Sensor Data Integration

| Source | Data Type | Status | Coverage | Resolution |
|--------|-----------|--------|----------|------------|
| **Open-Meteo-derived file** | Elevation, Soil Moisture, Weather | Cached/demo | 20 station profiles | Snapshot |
| **NASA GLC extract** | Historical Landslide Catalog | Repository dataset | 8 NER states | Point data |
| **Kaggle rainfall extract** | India Rainfall (1901-2015) | Repository dataset | District | Monthly |
| **Kaggle landslide extract** | India Landslide Incidents | Repository dataset | India | District |
| **SRTM DEM** | Terrain/Elevation + local slope | ✅ Live on-demand | Global | ~30m |
| **Sentinel-2 L2A** | NDVI Vegetation Index | ✅ Live on-demand | Global | 10m source imagery |
| **IMD** | Current weather, district rainfall/warnings | ✅ Integrated with fail-soft fallback | India | Observation/product dependent |
| **GloFAS via Open-Meteo** | River discharge | ✅ Live on-demand | Global rivers | ~5km |
| **USGS** | Landslide Hazard Maps | 📋 Ready | Regional | Variable |

### Cached Satellite-Derived Metrics Per Station

```
  CACHED DEMONSTRATION DATA (Open-Meteo-derived)
  ═══════════════════════════════════════════════════════

  ELEVATION RANGE (meters):
  Agartala    ▓                                          12m
  Dimapur     ▓▓                                        147m
  Itanagar    ▓▓▓                                       160m
  Guwahati    ▓▓                                         52m
  Dima Hasao  ▓▓▓▓                                     413m
  Mangan      ▓▓▓▓▓▓▓                                 796m
  Imphal      ▓▓▓▓▓▓▓▓                                782m
  Churachand. ▓▓▓▓▓▓▓▓▓                               862m
  Aizawl      ▓▓▓▓▓▓▓▓▓▓                             1069m
  Cherrapunji ▓▓▓▓▓▓▓▓▓▓                             1029m
  Namchi      ▓▓▓▓▓▓▓▓▓▓                             814m
  Kohima      ▓▓▓▓▓▓▓▓▓▓▓▓                          1365m
  Shillong    ▓▓▓▓▓▓▓▓▓▓▓▓                          1436m
  Gangtok     ▓▓▓▓▓▓▓▓▓▓▓▓                          1487m
  Ziro        ▓▓▓▓▓▓▓▓▓▓▓▓                          1592m
  Tawang      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                   2791m

  SOIL MOISTURE (m³/m³ — higher = wetter = riskier):
  Tura        ▓▓▓▓▓▓▓▓▓              0.29  ← Driest
  Tawang      ▓▓▓▓▓▓▓▓▓▓▓            0.37
  Imphal      ▓▓▓▓▓▓▓▓▓▓▓            0.38
  Aizawl      ▓▓▓▓▓▓▓▓▓▓▓▓           0.39
  Agartala    ▓▓▓▓▓▓▓▓▓▓▓▓           0.40
  Gangtok     ▓▓▓▓▓▓▓▓▓▓▓▓           0.41
  Ziro        ▓▓▓▓▓▓▓▓▓▓▓▓           0.42
  Dima Hasao  ▓▓▓▓▓▓▓▓▓▓▓▓           0.43
  Guwahati    ▓▓▓▓▓▓▓▓▓▓▓▓▓          0.46
  Shillong    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓         0.50  ← Wettest

  NDVI VEGETATION INDEX (0-1 — lower = less vegetation = riskier):
  Tawang      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  0.528  ← Lowest
  Shillong    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 0.590
  Aizawl      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 0.593
  Kohima      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 0.595
  Ziro        ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 0.600
  Cherrapunji ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 0.611
  Imphal      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 0.621
  Dima Hasao  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 0.650
  Pasighat    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 0.691  ← Highest
```

---

## 🖥️ Application Modules

GeoShield's React application is organized around operational workflows rather
than a fixed page-count claim:

| Module | Purpose |
|---|---|
| **Login & RBAC** | JWT authentication with persistent users and admin-managed roles |
| **Dashboard** | Operational summary, rainfall/risk trends, alerts, reports, roads and state views |
| **Stations** | Live station inventory, latest telemetry and risk state |
| **Station Detail** | Sensor history, weather, ML risk and satellite context for one station |
| **Risk Map** | Leaflet GIS view, heatmap layers, infrastructure and click-to-predict |
| **Alerts** | Active warning workflow with acknowledge/resolve controls |
| **Citizen Reports** | Geo-tagged reports, evidence upload, ownership isolation and staff review |
| **Administration** | Persistent users, password reset, station provisioning/edit/deactivation |
| **Satellite & Flood** | Live SRTM/Sentinel-2 enrichment, cached fallback, live GloFAS discharge and compound-risk views |
| **Simulator** | Controlled test-only generation of risk events and alerts |
| **Verification Flow** | Guided academic walkthrough for reproducible demonstrations |

The operational views consume authenticated real-time events where appropriate
and retain polling fallbacks so temporary WebSocket loss does not permanently
stale the UI.

---

## ⚙️ Backend API

GeoShield exposes a FastAPI REST/WebSocket surface grouped by capability. The
exact route count is intentionally not frozen in documentation; the implemented
surface is verified by automated tests.

Key API groups include:

- **Authentication & users** — login, persistent account lifecycle, role checks,
  password reset and immediate session revocation.
- **Stations & telemetry** — station provisioning, history, latest readings and
  authenticated gateway ingestion with idempotent `external_id` handling.
- **Prediction & ML** — location prediction, terrain-enriched inference, ML
  health and risk grids.
- **Alerts** — list/filter, acknowledge, resolve, statistics, history, timeline
  and authenticated real-time alert streams.
- **Citizen reports** — submit, list by authorization scope, evidence retrieval,
  verify and dismiss.
- **Dashboard/GIS/export** — operational summaries, heatmaps, trends, GeoJSON,
  CSV and risk-zone exports.
- **Weather/satellite/flood** — IMD-preferred weather, live SRTM terrain,
  Sentinel-2 NDVI, live GloFAS discharge, explicit provenance and compound-risk context.
- **Health/readiness** — process liveness plus database-backed readiness.

Representative paths:

```text
POST /api/auth/login
GET  /api/health/ready
GET  /api/sensors/stations
POST /api/sensors/stations/{station_id}/readings
POST /api/predict
GET  /api/alerts
GET  /ws/alerts/{district}
POST /api/reports
GET  /api/dashboard/stats
GET  /api/export/geojson
GET  /api/integrations/terrain
GET  /api/integrations/imd/current
GET  /api/satellite/live/{station_id}
```

The complete route behavior is covered by backend, browser, PostgreSQL, Docker,
Windows, Android, Electron and disaster-recovery CI gates.

---

## 📊 Historical Data Analysis

### 44 Documented Landslide Events (2011-2024)

Our historical dataset covers **14 years** of landslide events across all 8 NER states, compiled from:
- NASA Global Landslide Catalog (GLC)
- Geological Survey of India reports
- IMD rainfall event documentation
- News reports and district administration records

### Event Timeline

```
  LANDSLIDE EVENTS BY YEAR
  ═══════════════════════════════════════════════════════

  2011  ████                  2 events
  2012  ██                    1 event
  2013  ████████████          4 events
  2014  ████████████████      5 events
  2015  ████████████████      5 events
  2016  ████                  2 events
  2017  ████████████          4 events
  2018  ████████████████████  6 events
  2019  ████                  1 event
  2020  ████████████████████  6 events
  2021  (data gap)            0 events
  2022  ████████████████████  6 events
  2023  ████████████████      5 events
  2024  ████████████████      5 events (incl. Sikkim flash flood)
```

### Fatality Analysis

| Severity | Events | Deaths | Road Blocks | Avg Response |
|----------|--------|--------|-------------|--------------|
| **Large** | 12 | 73 | 11 | 3+ days |
| **Medium** | 19 | 15 | 17 | 1-3 days |
| **Small** | 13 | 0 | 3 | <1 day |
| **Total** | **44** | **88** | **31** | — |

---

## 🚨 Early Warning System

### Alert Classification

| Level | Trigger | Response Time | Actions |
|-------|---------|---------------|---------|
| 🟢 **Normal** | Risk < 25 | 24 hours | Routine monitoring, log readings |
| 🟡 **Advisory** | Risk 25-50 | 6 hours | Enhanced monitoring, notify DDM |
| 🟠 **Warning** | Risk 50-75 | 2 hours | Pre-position rescue teams, voluntary evacuation |
| 🔴 **Emergency** | Risk > 75 | 30 minutes | IMMEDIATE EVACUATION, deploy sirens, close roads |

### Alert Workflow

```
  SENSOR DATA → AI ASSESSMENT → RISK SCORE → ALERT LEVEL
       │              │              │              │
       ▼              ▼              ▼              ▼
  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Rainfall│  │ RF + GB  │  │ 0-100    │  │ L/M/H/C  │
  │ Moisture│→ │ Ensemble │→ │ Score    │→ │ Level    │
  │ Displcm │  │ Predict  │  │          │  │          │
  │ Tilt    │  │          │  │          │  │          │
  └─────────┘  └──────────┘  └──────────┘  └─────┬────┘
                                                  │
                              ┌────────────────────┤
                              ▼                    ▼
                     ┌──────────────┐    ┌──────────────┐
                     │  In-App WS   │    │ Multi-channel│
                     │  Dashboard   │    │ SMS + ntfy + │
                     │  Alert       │    │ VAPID Push   │
                     └──────────────┘    └──────────────┘
```

---

### ACT Communication Layer

For high-risk and critical events, GeoShield can fan out the same persisted
alert over multiple independent communication transports:

- authenticated district-scoped WebSocket for live operations;
- **Twilio SMS**, with global and district-specific recipient routing;
- **ntfy push** for topic/mobile delivery;
- **standards-based VAPID Web Push**, with persistent browser/PWA subscriptions
  and service-worker delivery even when the application tab is not active;
- persistent delivery records plus an **Emergency Communication Center** where
  admin/district-admin users can inspect channel readiness and run test sends.

External provider failure is fail-soft: an SMS or push outage is logged without
blocking alert persistence or the remaining warning channels. Full setup is
documented in [docs/COMMUNICATIONS.md](docs/COMMUNICATIONS.md).

---

## 🗺️ GIS Risk Mapping

### Map Layers

| Layer | Description | Color Code |
|-------|-------------|------------|
| **Risk Heatmap** | Color-coded circles by risk level | 🟢🟡🟠🔴 |
| **Road Network** | 48 monitored roads with status | Green/Amber/Red |
| **Village Markers** | 18 villages with population | By risk zone |
| **Station Markers** | 20 sensor stations | Click for details |

### Monitored Roads

```
  ROAD STATUS
  ═══════════════════════════════════════════════════════

  🟢 OPEN (5 roads):
  ├── NH-10  (Siliguri-Gangtok)
  ├── NH-2   (Dimapur-Kohima)
  ├── NH-6   (Shillong-Tura)
  ├── NH-29  (Guwahati-Shillong)
  └── NH-415 (Itanagar-Bomdila)

  🟡 PARTIALLY BLOCKED (2 roads):
  ├── NH-37  (Guwahati-Jorhat) — Debris on one lane
  └── SH-4   (Haflong-North Cachar) — Reduced capacity

  🔴 BLOCKED (1 road):
  └── SH-1   (Aizawl-Lunglei) — Full blockage, landslide debris
```

---

## ⚡ Landslide Simulator

### For Live Project Demo

The simulator allows presenters to **trigger realistic landslide events** and watch the entire system respond in real-time:

1. **Select Station** — Pick any of the 20 NER stations
2. **Choose Intensity** — Low / Moderate / High / Critical
3. **Click Run** — Watch the system respond:
   - Sensor readings spike (rainfall, moisture, displacement)
   - AI model runs assessment (new risk score)
   - Alert generated if risk >= moderate
   - Dashboard updates in real-time

### Verification / Presentation Flow

```
  DEMO SEQUENCE (3 minutes)
  ═══════════════════════════════════════════════════════

  Step 1 (30s): Dashboard Overview
  → Show 20 stations, risk pie chart, rainfall trends
  → Explain the cached regional/satellite-derived demo metrics

  Step 2 (30s): GIS Risk Map
  → Show interactive map with heatmap
  → Click Cherrapunji station (known hotspot)
  → Show road status and village markers

  Step 3 (60s): Landslide Simulator
  → Navigate to Simulator page
  → Select Cherrapunji, intensity = CRITICAL
  → Click "Run Simulation"
  → Show: Risk score spikes to 95.4/100
  → Show: Alert generated with 12,000+ affected
  → Show: Contributing factors and recommendation

  Step 4 (30s): Satellite Data
  → Navigate to Satellite Data page
  → Show cached elevation, soil moisture, and NDVI fields
  → Compare Tawang (2791m, high risk) vs Agartala (12m, low risk)

  Step 5 (30s): Multilingual Support
  → Switch language to Hindi → Bengali → Assamese
  → Show all labels translate correctly

  Step 6 (30s): Station Deep Dive
  → Click any station
  → Show sensor charts, AI gauge, weather data
  → Show contributing factors and recommendation
```

---

## 🌊 Flood Risk Monitoring

### Compound Hazard Analysis

GeoShield combines **historical flood-landslide correlation** data for NER districts with **live GloFAS river-discharge guidance** fetched through Open-Meteo when available. The historical baseline remains available offline. The prototype compound-risk view uses 0.4 × flood baseline risk + 0.6 × current landslide risk and displays live discharge separately rather than presenting it as a field-certified flood probability.

| District | Flood Risk | Events | Rivers |
|----------|-----------|--------|--------|
| East Khasi Hills | 85 | 42 | Umiam, Wah Umkhrah |
| Kamrup | 78 | 38 | Brahmaputra, Kalu |
| Dimapur | 70 | 28 | Dhansiri, Dan |
| East Siang | 68 | 24 | Siang, Dibang |
| West Garo Hills | 65 | 22 | Simsang, Asanang |

### 3 Flood API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/flood/data` | District-level flood risk data |
| `GET /api/flood/summary` | Aggregated NER flood metrics |
| `GET /api/flood/correlation` | Flood × landslide compound risk scatter |

---

## 🌐 Multilingual Support

| Language | Code | Coverage | Script |
|----------|------|----------|--------|
| English | en | ✅ 90+ keys | Latin |
| Hindi | hi | ✅ 90+ keys | Devanagari |
| Bengali | bn | ✅ 90+ keys | Bengali |
| Assamese | as | ✅ 90+ keys | Bengali (Assamese) |

---

## 🚀 Quick Start

### Recommended presentation path (Windows)

Run once while internet is available:

```bat
prepare-demo.bat
```

Then, including on presentation day without internet:

```bat
start-offline.bat
```

Open **http://127.0.0.1:8000**.

### Linux/macOS local path

After creating `backend/venv`, installing `backend/requirements.txt`, and
running `npm ci && npm run build` in `frontend/`:

```bash
./start.sh
```

### Docker

```bash
docker compose up --build
```

Docker Compose binds the local demo to **127.0.0.1:8000**.

For production, use the Docker profile described in
[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md). Production requires a strong
`JWT_SECRET` and secret-managed `GEOSHIELD_ADMIN_EMAIL` /
`GEOSHIELD_ADMIN_PASSWORD`; built-in demo credentials are not intended for
public deployment.

**Local demo login:** `admin@geoshield.gov.in` / `admin123` when
`ENABLE_DEMO_USERS=true`.

---

## 📁 Project Structure

```
GeoShield/
├── README.md                              # This file
├── SIH_2026_PRESENTATION.md               # 15-slide pitch deck
├── PRESENTATION.md                        # Slide content with diagrams
├── DEPLOYMENT_GUIDE.md                    # Railway/Render/Docker
├── SATELLITE_INTEGRATION.md               # Satellite-data integration notes
├── BUILD_GUIDE.md                         # Desktop/mobile build instructions
├── Dockerfile                             # Docker deployment
├── Procfile                               # Railway deployment
├── start.bat                              # One-click local deploy (Windows)
├── start.sh                               # Quick launcher script
├── demo.sh                                # Polished demo presentation script
├── electron/
│   ├── main.js                            # Electron main process + backend auto-start
│   └── preload.js                         # Secure IPC bridge
├── branding/
│   ├── team_logo.png                      # Team logo
│
├── backend/                               # ⚙️ Python FastAPI
│   ├── app/
│   │   ├── main.py                        # App entry + static files
│   │   ├── models.py                      # 8 SQLAlchemy models
│   │   ├── database.py                    # SQLite connection
│   │   ├── seed_data.py                   # Realistic NER seeder
│   │   ├── ai_engine/
│   │   │   ├── risk_predictor.py          # RF + GB ensemble (original)
│   │   │   ├── enhanced_predictor.py     # XGBoost + terrain lookup (alternative)
│   │   │   └── terrain_lookup.py         # Nearest-neighbor NER terrain data
│   │   └── routers/
│   │       ├── sensors.py                 # Station APIs
│   │       ├── dashboard.py               # Stats, heatmap, trends
│   │       ├── alerts.py                  # Alert management
│   │       ├── reports.py                 # Reports + roads + villages
│   │       ├── weather.py                 # Weather data
│   │       ├── simulator.py               # Landslide simulator
│   │       ├── satellite.py               # Cached/derived satellite data
│   │       ├── flood.py                   # Flood risk + correlation
│   │       ├── alerts_timeline.py         # Timeline + history + trends
│   │       ├── predict.py                 # Click-to-predict API
│   │       ├── ml_enhanced.py             # Enhanced ML routes + risk grid
│   │       └── export.py                  # GeoJSON/CSV export
│   │   ├── schemas.py                     # Pydantic validation
│   │   ├── middleware/
│   │   │   └── rate_limiter.py            # Rate limiting (100/min)
│   │   └── tests/
│   │       ├── test_api.py                # API regression coverage
│   │       ├── test_e2e.py                # End-to-end workflows
│   │       ├── test_phase4_security.py    # Security/config regression coverage
│   │       └── test_stabilization.py      # Post-Phase-4 consistency regressions
│   └── uploads/                           # Photo uploads
│
├── frontend/                              # 🖥️ React + TypeScript
│   ├── src/
│   │   ├── App.tsx                        # Router + Auth + Sidebar
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx              # 3 tabs, charts, rankings
│   │   │   ├── RiskMap.tsx                # Leaflet GIS + click-to-predict
│   │   │   ├── Alerts.tsx                 # Timeline + 30-day history
│   │   │   ├── Reports.tsx                # Citizen reports
│   │   │   ├── StationDetail.tsx          # Station + AI + satellite
│   │   │   ├── Simulator.tsx              # Landslide simulator
│   │   │   ├── SatelliteData.tsx          # Satellite demo metrics
│   │   │   ├── FloodData.tsx              # 19 districts + correlation
│   │   │   └── DemoFlow.tsx               # 8-step verification guide
│   │   ├── components/
│   │   │   ├── ErrorBoundary.tsx           # Crash recovery UI
│   │   │   └── MobileFAB.tsx              # Mobile floating action button
│   │   ├── services/api.ts                # API client (45 endpoints)
│   │   └── i18n/translations.ts           # EN, HI, BN, AS, OR (5 languages)
│   └── dist/                              # Built frontend
│
├── datasets/                              # 📊 Data Sources
│   ├── processed/
│   │   ├── real_satellite_data.json        # Cached Open-Meteo-derived data
│   │   ├── real_ner_training_data.csv      # Mixed-provenance training samples
│   │   └── ner_landslide_events.csv        # Historical events
│   ├── raw/
│   │   ├── ner_historical_landslides.csv   # 44 events (2011-2024)
│   │   ├── nasa_landslide_catalog.csv      # NASA GLC
│   │   └── india_district_rainfall.csv     # IMD rainfall
│   └── download_datasets.py                # Data collection scripts
│
└── kaggle/                                # 📥 Downloaded datasets
    ├── catalog.csv
    ├── landslide_india.csv
    └── rainfall_india.csv
```

---

## 🔒 Security

| Feature | Implementation |
|---------|---------------|
| **Rate Limiting** | 100 req/min general, 10 req/min auth |
| **JWT Authentication** | HS256, 24h expiry, bcrypt password hashing |
| **RBAC** | 4 roles: admin, field_officer, district_admin, citizen |
| **Input Validation** | Pydantic schemas on all POST endpoints |
| **CORS** | Configurable origins |
| **Path Traversal** | Protected static file serving |

---

## 🎓 Phase 4 Presentation & Offline Demo

For final-year presentation preparation, deployment notes, the recommended live-demo sequence, safe claims, and **32 viva questions with answers**, see [PHASE4_GUIDE.md](PHASE4_GUIDE.md).

For a repeatable Windows demo:

```bat
REM Run once while internet is available
prepare-demo.bat

REM Presentation-day launcher; core flow works without internet
start-offline.bat
```

The offline launcher disables live weather and model retraining, uses the prepared frontend/cached data, and binds FastAPI only to `127.0.0.1:8000`.

---

## 🛠️ Tech Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | React | 18.2 | UI Framework |
| **Styling** | Tailwind CSS | 3.x | Responsive design |
| **Maps** | Leaflet.js | 1.9.4 | GIS visualization |
| **Charts** | Recharts | 2.x | Data visualization |
| **Icons** | Lucide React | Latest | UI icons |
| **Backend** | Python FastAPI | 0.115 | REST API server |
| **Database** | SQLite | 3.x | Data storage |
| **AI/ML** | scikit-learn | 1.x | Risk prediction (RF+GB VotingClassifier) |
| **Caching** | joblib | — | Model persistence across restarts |
| **APIs** | Open-Meteo | Free | Optional current-weather lookup with demo fallback |
| **Build** | Vite | 5.x | Frontend bundler |
| **HTTP** | Axios | 1.x | API client |
| **Mobile** | Capacitor | 6.x + Status Bar | Android wrapper, futuristic splash |
| **Desktop** | Electron | 44.x | Windows/Linux, auto-starts backend |
| **Testing** | pytest + TestClient + GitHub Actions | — | 105-test operational suite + audits/build/Docker/PostgreSQL CI |

---

## 📈 Results & Impact

### Verified Prototype Scope

| Area | Current verified scope |
|------|------------------------|
| **Backend** | FastAPI application starts and the health, dashboard, and prediction flows respond |
| **Frontend** | React 18 + TypeScript production build completes |
| **Automated tests** | 105 backend test functions cover the stabilized baseline plus persistent auth, station provisioning, readiness, sensor ingestion, idempotency, and security regressions |
| **Security checks** | `pip check`, root/frontend npm audits, TypeScript/Vite build, Docker build, and production-container API/login smoke checks pass in CI |
| **Input modes** | Authenticated external sensor/gateway readings, optional seeded reference history, controlled simulation, and cached/live external-data adapters |
| **ML status** | District-grouped prototype evaluation is reproducible; independent field validation remains future work |
| **Source transparency** | Weather/satellite APIs and UI expose live, cached, fallback, stale, and unavailable states |

### Intended Impact

GeoShield is intended to demonstrate how multi-source monitoring, risk scoring,
GIS views, and multilingual alerts could support earlier decision-making. Claims
about warning lead time, population protected, field coverage, or operational
response require real sensor deployment and prospective validation; they are not
claimed by the current prototype.

---

## ✅ Test Results

### Operational Regression Suite: 105 tests

```
Backend:   105-test operational regression suite
Frontend:  TypeScript + Vite production build
npm audit: root + frontend high-severity gates
pip check: dependency consistency check
Docker:    clean production image + database-readiness smoke
Postgres:  fresh Alembic migrations + operational-core integration tests
Runtime:   dashboard + stations + prediction + persistent login + sensor-ingestion paths
```

### Key Test Results

| Feature | What Was Tested | Result |
|---------|----------------|--------|
| **Dashboard** | Seeded station and alert summaries | ✅ API flow works |
| **Simulate** | Cherrapunji → risk=99.2/critical | ✅ Alert fires |
| **Alert Flow** | Count grew 101→102 after sim | ✅ Flow works |
| **AI Predict** | risk=89.4/critical, 2 factors | ✅ Nearest station found |
| **Flood Correlation** | 19 districts correlated | ✅ Scatter plot |
| **Export** | GeoJSON (20 features), CSV (21 lines) | ✅ Downloads work |
| **Security** | Invalid login→401, no auth→401, bad input→422 | ✅ All blocked |

---

## 📱 Mobile & Desktop Wrappers

Web, Docker, Android, Windows Electron, Linux Electron and the generated iOS
simulator application are covered by CI build gates. Mobile clients share the
same frontend and connect to the GeoShield FastAPI backend.

### Android / Capacitor

- Package ID: `com.geoshield.app`
- Installed APKs use the bundled frontend.
- The Python/FastAPI backend is **not** embedded in the APK; enter a reachable
  backend URL from the login/settings screen.
- A fresh checkout must run `npx cap add android` before `npx cap sync android`
  because generated Android platform files are not committed.
- CI generates the Capacitor Android project, builds the Gradle debug APK and
  verifies the package and local-backend transport.

### iOS / Capacitor

- The same responsive frontend is generated as a Capacitor iOS application.
- macOS CI creates the native iOS project and performs an unsigned iOS Simulator build.
- A physical-device/App Store IPA still requires the project owner's Apple
  Developer signing identity and provisioning profile; those credentials are
  intentionally not stored in the repository.

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for exact commands.

### Electron desktop

The wrapper configuration now uses packaged backend/dataset/frontend resources,
a real PNG icon, and writable per-user SQLite/model-cache paths. Root Electron
lockfile installation and main/preload JavaScript syntax are CI-verified.

Windows releases bundle their Python backend runtime. Linux AppImage builds now
bundle a prepared Python runtime and CI verifies that the packaged resources
contain the backend and interpreter. Local developer mode can still use the
system Python interpreter.

---

## 🗺️ Future Roadmap

| Phase | Timeline | Features |
|-------|----------|----------|
| **Phase 1** | ✅ Done | Baseline audit, dependency correction, risk-guidance consistency fix, provenance policy, verified backend/frontend baseline |
| **Phase 2** | ✅ Done | Dataset audit, provenance manifest, checksum-bound report, district-grouped ML evaluation, imbalance-aware metrics, regression tests |
| **Phase 3** | ✅ Done | Default live weather adapter, timeout and TTL cache, seeded fallback, satellite snapshot reload, timestamps, freshness, source badges, regression tests |
| **Phase 4** | ✅ Done | Production-safe configuration, restricted privileged operations, hardened Docker/Render deployment, CI verification, repeatable offline demo scripts, and presentation/viva guide |
| **Phase 5** | ✅ Done | Persistent operations, browser E2E, Android packaging, Windows desktop hardening, realtime sensor/report flows |
| **Phase 6** | ✅ Done | v1.0 project freeze, release assets, disaster recovery and final baseline verification |
| **Phase 7** | ✅ Done | Live SRTM + Sentinel-2, IMD, GloFAS flood data, offline queue/cache, district operations, Linux runtime packaging and iOS build verification |
| **Phase 8** | ✅ Done | ACT emergency communications: district-aware Twilio SMS, ntfy, VAPID Web Push, persistent push subscriptions, delivery audit log, service-worker notifications and Communication Center |

---

## 👤 Major Project Maintainer

**Yash Agarwal** — B.Tech ECE (EC-ACT), JIIT, Batch 2027

New development and validation in this major-project repository are maintained
by Yash Agarwal. Required third-party attribution is retained in [NOTICE.md](NOTICE.md).

---

<div align="center">

### 🛡️ GeoShield — Protecting North Eastern India

**Major-project adaptation maintained by Yash Agarwal**

[![GitHub](https://img.shields.io/badge/GitHub-YashAgarwal--31-181717?style=for-the-badge&logo=github)](https://github.com/YashAgarwal-31/GeoShield-AI-Landslide-Early-Warning-System)

</div>
