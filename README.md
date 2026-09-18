<div align="center">

<img src="branding/team_logo.png" alt="GeoShield Logo" width="200" />

# 🛡️ GeoShield

### AI-Based Early Warning & Landslide Risk Monitoring System
**North Eastern Region, India — Smart India Hackathon 2026**

![SIH 2026](https://img.shields.io/badge/SIH-2026-green?style=for-the-badge)
![Problem ID](https://img.shields.io/badge/Problem_ID-26001-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![AI/ML](https://img.shields.io/badge/AI/ML-Random_Forest-orange?style=for-the-badge)

**Ministry of Development of North Eastern Region (MDoNER)**

</div>

---

> [!IMPORTANT]
> **Major-project development repository.** This repository is being extended
> and validated by **Yash Agarwal**. Third-party attribution and provenance are
> documented in [NOTICE.md](NOTICE.md), while data lineage and limitations are
> documented in [DATA_PROVENANCE.md](DATA_PROVENANCE.md).

> [!NOTE]
> This is a research and demonstration prototype, not a certified public-warning
> system. The current build combines historical/regional inputs with seeded,
> simulated, and realistically generated samples; it does not ingest a live
> physical sensor network by default.

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

GeoShield is a **full-stack AI-powered landslide monitoring prototype** designed specifically for the North Eastern Region. It combines **seeded sensor scenarios**, **cached regional data**, **machine learning prediction**, and **multilingual warning workflows** into a single unified platform.

### 6 Core Capabilities

| # | Capability | Description | Technology |
|---|------------|-------------|------------|
| 1 | **Monitoring Dashboard** | 20 seeded station profiles across 8 NER states with rainfall, soil moisture, ground displacement, tilt, and pore pressure fields | FastAPI + SQLite |
| 2 | **AI Risk Prediction** | Experimental RF+GB VotingClassifier trained on regional and realistically generated terrain samples; independent validation is planned | scikit-learn |
| 3 | **Warning Workflow** | Multi-level alert framework (Low → Moderate → High → Critical); external SMS/push delivery is planned | WebSocket + REST |
| 4 | **GIS Risk Mapping** | Interactive Leaflet.js heatmaps showing the prototype risk distribution, road status, village locations, and station profiles | Leaflet.js |
| 5 | **Citizen Reporting** | Geo-tagged photo/video reporting workflow for field officers and local residents | React + FastAPI |
| 6 | **Multilingual UI** | Full interface translation in English, Hindi, Bengali, and Assamese covering all 90+ UI strings | i18n system |

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
│  │                    REST API (17 Endpoints)                │   │
│  │                                                          │   │
│  │  /api/dashboard/*    → Stats, heatmap, trends, states   │   │
│  │  /api/sensors/*      → Stations, readings, history      │   │
│  │  /api/alerts/*       → CRUD, acknowledge, resolve       │   │
│  │  /api/reports/*      → Submit, list, verify             │   │
│  │  /api/weather/*      → Current + forecast               │   │
│  │  /api/satellite/*    → Cached data, summary, risk zones │   │
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
     Source: SRTM DEM / Open-Meteo elevation API

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
     Source: Sentinel-2 satellite (estimated)

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

## 🛰️ Data Sources and Planned Integrations

### Satellite & Sensor Data Integration

| Source | Data Type | Status | Coverage | Resolution |
|--------|-----------|--------|----------|------------|
| **Open-Meteo-derived file** | Elevation, Soil Moisture, Weather | Cached/demo | 20 station profiles | Snapshot |
| **NASA GLC extract** | Historical Landslide Catalog | Repository dataset | 8 NER states | Point data |
| **Kaggle rainfall extract** | India Rainfall (1901-2015) | Repository dataset | District | Monthly |
| **Kaggle landslide extract** | India Landslide Incidents | Repository dataset | India | District |
| **SRTM DEM** | Terrain/Elevation | 📋 Ready | Global | 30m |
| **Sentinel-2** | NDVI Vegetation Index | 📋 Ready | Global | 10m |
| **IMD** | Official Indian Rainfall | 📋 Ready | District | Daily |
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

## 🖥️ Frontend Features

### 10 Interactive Pages

| Page | Description | Key Features |
|------|-------------|--------------|
| **🔐 Login** | Authentication gate | 4 demo accounts, role-based access |
| **📊 Dashboard** | Prototype overview | 3 tabs (Overview/Stations/Alerts), radar chart, rankings |
| **🗺️ Risk Map** | GIS visualization | Leaflet heatmap, roads, villages, click-to-predict |
| **🚨 Alerts** | Warning management | Filter by status/risk, acknowledge, resolve workflow |
| **📝 Reports** | Citizen reporting | Photo upload, geo-tagging, multi-type reports |
| **⚡ Simulator** | Live demo tool | 4 intensity levels, AI assessment, alert generation |
| **🛰️ Satellite** | Cached data view | 20 station profiles, demo metrics, risk scoring |
| **📡 Station** | Deep dive | Sensor charts, AI gauge, weather, satellite data |
| **🌊 Flood Risk** | Compound hazard | Flood-landslide correlation scatter plot |
| **🎯 Demo Flow** | Judge walkthrough | 8-step guide, live simulation, key metrics |

### Dashboard Overview Tab

```
  ┌─────────────────────────────────────────────────────────────┐
  │  🛡️ GeoShield Dashboard                    DEMO  SIH 2026 │
  ├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┤
  │ Active  │ Active  │ People  │ Pending │ Avg     │ High-   │
  │ Sensors │ Alerts  │ at Risk │ Reports │ Risk    │ Risk    │
  │   20    │   36    │ 31,977  │   15    │  43.8   │    6    │
  ├─────────┴─────────┴─────────┴─────────┴─────────┴─────────┤
  │                                                           │
  │  ┌─────────────────────────┐  ┌───────────────────────┐   │
  │  │   Rainfall Trend (48h)  │  │   Risk Distribution   │   │
  │  │   ▁▂▃▄▅▆▇█▇▆▅▄▃▂▁▂▃   │  │      ◉ Donut Chart    │   │
  │  │   48 data points        │  │   Low:101 Mod:536     │   │
  │  └─────────────────────────┘  │   High:338 Crit:5     │   │
  │                               └───────────────────────┘   │
  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
  │  │ Risk Trend   │ │ Road Status  │ │ State Overview   │   │
  │  │ 48h line     │ │ Open: 5      │ │ Arunachal  45.2  │   │
  │  │ chart        │ │ Partial: 2   │ │ Sikkim     42.1  │   │
  │  │              │ │ Blocked: 1   │ │ Meghalaya  38.5  │   │
  │  └──────────────┘ └──────────────┘ └──────────────────┘   │
  └─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Backend API

### 45 RESTful Endpoints

```
  API ENDPOINT STATUS
  ═══════════════════════════════════════════════════════

  DASHBOARD
  ✅ GET  /api/dashboard/stats          → 20 stations, 5 alerts
  ✅ GET  /api/dashboard/risk-heatmap   → 20 GIS points
  ✅ GET  /api/dashboard/rainfall-trend → 48h hourly data
  ✅ GET  /api/dashboard/risk-trend     → 48h risk scores
  ✅ GET  /api/dashboard/state-summary  → 8 NER states

  SENSORS
  ✅ GET  /api/sensors/stations         → 20 stations
  ✅ GET  /api/sensors/stations/{id}    → Station + readings + AI
  ✅ GET  /api/sensors/stations/{id}/history → Time-range readings

  ALERTS
  ✅ GET  /api/alerts                   → All alerts (filtered)
  ✅ GET  /api/alerts/active            → Active alerts only
  ✅ PUT  /api/alerts/{id}/acknowledge  → Acknowledge alert
  ✅ PUT  /api/alerts/{id}/resolve      → Resolve alert

  REPORTS & INFRASTRUCTURE
  ✅ GET  /api/reports                  → Citizen reports
  ✅ POST /api/reports                  → Submit new report
  ✅ GET  /api/roads                    → 48 monitored roads
  ✅ GET  /api/villages                 → 18 tracked villages

  PREDICT (Click-to-Predict)
  ✅ POST /api/predict                  → AI risk at any lat/lng

  EXPORT
  ✅ GET  /api/export/geojson           → GIS-ready GeoJSON
  ✅ GET  /api/export/csv               → Excel/analysis CSV
  ✅ GET  /api/export/risk-zones        → High-risk polygons

  ALERT TIMELINE
  ✅ GET  /api/alerts/timeline          → Chronological view
  ✅ GET  /api/alerts/history           → 30-day trend data
  ✅ GET  /api/alerts/stats             → Alert summary stats

  WEATHER
  ✅ GET  /api/weather/{id}             → Weather/demo data
  ✅ GET  /api/weather/{id}/forecast    → 48h forecast

  SATELLITE
  ✅ GET  /api/satellite/data           → 20 station data profiles
  ✅ GET  /api/satellite/summary        → NER-wide metrics
  ✅ GET  /api/satellite/risk-zones     → Risk from available data

  SIMULATION
  ✅ POST /api/simulate/landslide       → Trigger simulation
  ✅ POST /api/simulate/batch           → Multi-station sim

  WEATHER
  ✅ GET  /api/weather/{station}        → Weather/demo data

  AUTH
  ✅ POST /api/auth/login                  → JWT token

  Endpoint flows are covered by the automated backend suite.
```

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
                     │  In-App      │    │  SMS/Push    │
                     │  Dashboard   │    │  Notification│
                     │  Alert       │    │  (planned)   │
                     └──────────────┘    └──────────────┘
```

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

### For Live SIH Demo

The simulator allows presenters to **trigger realistic landslide events** and watch the entire system respond in real-time:

1. **Select Station** — Pick any of the 20 NER stations
2. **Choose Intensity** — Low / Moderate / High / Critical
3. **Click Run** — Watch the system respond:
   - Sensor readings spike (rainfall, moisture, displacement)
   - AI model runs assessment (new risk score)
   - Alert generated if risk >= moderate
   - Dashboard updates in real-time

### Demo Flow for Judges

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

GeoShield integrates **flood-landslide correlation** data for all 19 NER districts, sourced from the Asia Flood Atlas and IMD historical records. The system computes **compound risk** (0.4 × flood risk + 0.6 × landslide risk) to identify districts facing dual hazards.

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
|  | Flood × landslide compound risk scatter |

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
├── demo.sh                                # Polished demo script for judges
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
│   │   │   └── DemoFlow.tsx               # 8-step guide for judges
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
| **Testing** | pytest + TestClient + GitHub Actions | — | 100-test stabilized suite + audits/build/Docker runtime smoke CI |

---

## 📈 Results & Impact

### Verified Prototype Scope

| Area | Current verified scope |
|------|------------------------|
| **Backend** | FastAPI application starts and the health, dashboard, and prediction flows respond |
| **Frontend** | React 18 + TypeScript production build completes |
| **Automated tests** | 100 backend test functions pass in GitHub Actions, including Phase 4 security/config and post-Phase-4 stabilization regressions |
| **Security checks** | `pip check`, root/frontend npm audits, TypeScript/Vite build, Docker build, and production-container API/login smoke checks pass in CI |
| **Demonstration data** | 20 seeded station profiles across 8 NER states, plus cached, historical, and generated inputs |
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

### Latest Clean Verification: 100/100 PASSED

```
Backend:   100 passed
Frontend:  TypeScript + Vite production build passed
npm audit: root + frontend report 0 vulnerabilities
pip check: No broken requirements found
Docker:    production image build + runtime smoke passed
Runtime:   health + dashboard + stations + prediction + production login smoke passed
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

The **web/Docker/offline runtime is the fully CI-verified project path**. Mobile
and Electron wrappers share the same frontend but have platform-specific
prerequisites.

### Android / Capacitor

- Package ID: `com.geoshield.app`
- Installed APKs use the bundled frontend.
- The Python/FastAPI backend is **not** embedded in the APK; enter a reachable
  backend URL from the login/settings screen.
- A fresh checkout must run `npx cap add android` before `npx cap sync android`
  because generated Android platform files are not committed.
- CI verifies the shared TypeScript/Vite build, not a complete Android SDK/Gradle
  APK build.

See [BUILD_GUIDE.md](BUILD_GUIDE.md) for exact commands.

### Electron desktop

The wrapper configuration now uses packaged backend/dataset/frontend resources,
a real PNG icon, and writable per-user SQLite/model-cache paths. Root Electron
lockfile installation and main/preload JavaScript syntax are CI-verified.

The current wrapper still relies on a compatible **system Python environment
with GeoShield backend dependencies installed**; it does not embed a
platform-specific Python runtime. For a fully repeatable academic demo, prefer
`start-offline.bat` or Docker.

---

## 🗺️ Future Roadmap

| Phase | Timeline | Features |
|-------|----------|----------|
| **Phase 1** | ✅ Done | Baseline audit, dependency correction, risk-guidance consistency fix, provenance policy, verified backend/frontend baseline |
| **Phase 2** | ✅ Done | Dataset audit, provenance manifest, checksum-bound report, district-grouped ML evaluation, imbalance-aware metrics, regression tests |
| **Phase 3** | ✅ Done | Optional live weather adapter, timeout and TTL cache, seeded fallback, satellite snapshot reload, timestamps, freshness, source badges, regression tests |
| **Phase 4** | ✅ Done | Production-safe configuration, restricted privileged operations, hardened Docker/Render deployment, CI verification, repeatable offline demo scripts, and presentation/viva guide |

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
