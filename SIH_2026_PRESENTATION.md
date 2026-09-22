# 🏔️ GeoShield — SIH 2026 Presentation

## Smart India Hackathon 2026 | Problem Statement #26001
### Ministry of Development of North Eastern Region (MDoNER)

---

# Slide 1: Title Slide

**🛡️ GeoShield**
**AI-Based Early Warning & Landslide Risk Monitoring System for NER**

- **Problem ID:** 26001
- **Theme:** Disaster Management
- **Team Name:** GeoShield

| Member | Roll No |
|--------|---------|
| Arghya Bose | 24155380 |
| Arindam Tripathi | 24155614 |
| Arnab Pal | 24155615 |
| Aaditree Shreya | 24155371 |
| Ankan Nag | 2405791 |
| Akash Das | 24155155 |

---

# Slide 2: The Problem

## North Eastern Region — Landslide Crisis

- **8 states**, 45 million people at risk
- **150+ landslide events** every monsoon season
- **88+ deaths** documented in NER (2011-2024)
- **31 major road blockades** cutting off connectivity
- **No centralized early warning system** exists

### What's Missing?
- Real-time sensor monitoring across NER
- AI-powered predictive risk assessment
- Multilingual early warning dissemination
- Citizen reporting infrastructure
- GIS-based visual risk mapping

---

# Slide 3: Our Solution

## 🛡️ GeoShield — Full-Stack Monitoring Platform

### 6 Core Capabilities:

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Monitoring Workflow** | 20 seeded reference stations plus authenticated external gateway ingestion |
| 2 | **AI Risk Prediction** | RF + Gradient Boosting runtime ensemble; separately reproducible district-grouped prototype evaluation |
| 3 | **Early Warning** | Multi-level alerts; WebSocket locally, SMS/push when providers are configured |
| 4 | **GIS Risk Mapping** | Interactive Leaflet.js heatmaps with click-to-predict |
| 5 | **Citizen Reporting** | Geo-tagged photo/video reports from field officers |
| 6 | **Multilingual UI** | English, Hindi, Bengali, Assamese support |

---

# Slide 4: System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React + TypeScript)         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Dashboard │ │ GIS Map  │ │ Alerts   │ │ Reports  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │Simulator │ │Satellite │ │Station   │               │
│  └──────────┘ └──────────┘ └──────────┘               │
├─────────────────────────────────────────────────────────┤
│                    BACKEND (Python FastAPI)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Dashboard │ │ Sensors  │ │ Alerts   │ │Reports   │  │
│  │  API     │ │  API     │ │  API     │ │  API     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │Satellite │ │Simulator │ │ Weather  │               │
│  │  API     │ │  API     │ │  API     │               │
│  └──────────┘ └──────────┘ └──────────┘               │
├─────────────────────────────────────────────────────────┤
│                    AI/ML ENGINE                          │
│  ┌──────────────────────┐ ┌──────────────────────┐     │
│  │ Random Forest        │ │ Gradient Boosting    │     │
│  │ (200 trees, d=15)    │ │ (150 trees, d=8)     │     │
│  └──────────────────────┘ └──────────────────────┘     │
│  Training: 12,000 mixed/derived samples | 9 features       │
├─────────────────────────────────────────────────────────┤
│                    DATA LAYER                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ SQLite   │ │ Open-    │ │ NASA GLC │ │ Real-    │  │
│  │ Database │ │ Meteo    │ │ Catalog  │ │ time     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

# Slide 5: AI/ML Model

## Risk Prediction Engine

### Model Architecture
- **Algorithm:** Voting Classifier (RF + Gradient Boosting)
- **Training Data:** 12,000 mixed regional, derived and realistically generated prototype samples
- **Features:** 9 input features
- **Validation:** district-disjoint evaluation is reproducible; reported metrics are not field accuracy

### Feature Importance

| Feature | Weight | Source |
|---------|--------|--------|
| Slope Angle | 25% | DEM (Open-Meteo) |
| Rainfall Daily | 20% | IMD + Open-Meteo |
| Soil Moisture | 15% | NASA SMAP + Open-Meteo |
| Rainfall 7-day | 15% | Cumulative from hourly data |
| NDVI (Vegetation) | 15% | Sentinel-2 estimation |
| Elevation | 10% | SRTM DEM |

### Risk Classification

| Level | Score | Action |
|-------|-------|--------|
| 🟢 Low | 0-25 | Normal monitoring |
| 🟡 Moderate | 25-50 | Enhanced monitoring |
| 🟠 High | 50-75 | Pre-position rescue teams |
| 🔴 Critical | 75-100 | IMMEDIATE EVACUATION |

---

# Slide 6: Real Data Sources

## Satellite & Sensor Data Integration

| Source | Data Type | Status | Resolution |
|--------|-----------|--------|------------|
| **Open-Meteo API** | Elevation, Soil Moisture, Weather | ✅ Live | Real-time |
| **NASA GLC** | Historical Landslide Catalog | ✅ 44 events | Point data |
| **Kaggle** | India Rainfall (1901-2015) | ✅ Integrated | Monthly |
| **Kaggle** | India Landslide Incidents | ✅ 200+ events | District |
| **SRTM DEM** | Terrain/Elevation | 📋 Ready | 30m |
| **Sentinel-2** | NDVI Vegetation Index | 📋 Ready | 10m |
| **IMD** | Official Indian Rainfall | 📋 Ready | District |
| **USGS** | Landslide Hazard Maps | 📋 Ready | Regional |

### Real Satellite Data Per Station
- Elevation: 12m (Agartala) to 2,791m (Tawang)
- Soil Moisture: 0.29 to 0.50 m³/m³
- NDVI: 0.53 to 0.69
- Rainfall: Live hourly readings

---

# Slide 7: Live Demo — Dashboard

## Key Metrics Displayed

| Metric | Value |
|--------|-------|
| Active Sensors | 20 across 8 states |
| Active Alerts | 5 high-risk warnings |
| People at Risk | 31,977 |
| Avg Risk Score | 43.0/100 |
| Villages Monitored | 18 (6 high-risk) |
| Roads Monitored | 8 (5 open, 2 partial, 1 blocked) |

### Dashboard Features
- Real-time risk pie chart
- 48-hour rainfall trend
- 48-hour risk trend
- State-wise risk comparison
- Radar chart for cross-state analysis
- Top 5 highest-risk stations

---

# Slide 8: Live Demo — GIS Risk Map

## Interactive Mapping System

### Map Layers
- **Risk Heatmap:** Color-coded circles by risk level
- **Road Network:** 8 monitored roads with status colors
- **Village Markers:** 18 villages with population data
- **Station Markers:** Click any station for AI assessment

### Map Technology
- Leaflet.js with OpenStreetMap tiles
- Dark theme matching dashboard
- Popup details on click
- Real-time data refresh (30-second intervals)

---

# Slide 9: Live Demo — Landslide Simulator

## For Live Presentation Demo

### How It Works:
1. Select a station from the dropdown
2. Choose intensity: Low / Moderate / High / Critical
3. Click "Run Simulation"
4. Watch: Sensor spike → AI assessment → Alert generation

### Demo Flow for Judges:
1. Show Cherrapunji station (known landslide hotspot)
2. Select "CRITICAL" intensity
3. Click "Run Simulation"
4. Result: Risk score spikes to 95.4/100
5. Alert generated: "CRITICAL - Immediate Landslide Threat"
6. Dashboard updates in real-time

---

# Slide 10: Live Demo — Satellite Data

## Real-Time Satellite Metrics

### Per-Station Data
- Real elevation from Open-Meteo API
- Soil moisture at 3 depths (0-7cm, 7-28cm, 28-100cm)
- NDVI vegetation index
- Live temperature, humidity, wind speed
- 24h and 7-day rainfall totals

### NER-Wide Summary
- 20 seeded reference stations with live/cached/fallback-labelled environmental data
- Composite prototype risk scoring from source-labelled live/cached/fallback inputs
- Automatic risk zone classification

---

# Slide 11: Historical Data Analysis

## 44 Documented Landslide Events (2011-2024)

### By State
| State | Events | Deaths | Road Blocks |
|-------|--------|--------|-------------|
| Sikkim | 8 | 46 | 7 |
| Meghalaya | 7 | 18 | 4 |
| Assam | 6 | 9 | 4 |
| Arunachal Pradesh | 6 | 6 | 5 |
| Manipur | 5 | 4 | 4 |
| Mizoram | 5 | 3 | 4 |
| Nagaland | 4 | 2 | 3 |
| Tripura | 3 | 0 | 0 |

### Key Findings
- **91% triggered by rain** (monsoon season)
- **70% caused road blockages**
- **Sikkim** has highest fatality rate
- **Peak months:** June-August

---

# Slide 12: Early Warning System

## Multi-Level Alert Framework

### Alert Levels
| Level | Response Time | Action |
|-------|--------------|--------|
| 🟢 Normal | 24h | Routine monitoring |
| 🟡 Advisory | 6h | Enhanced monitoring, notify DDM |
| 🟠 Warning | 2h | Pre-position teams, voluntary evacuation |
| 🔴 Emergency | 30min | Immediate evacuation, deploy sirens |

### Alert Channels
- In-app dashboard alerts
- SMS notifications
- WebSocket real-time updates
- Multilingual messages (EN/HI/BN/AS)

---

# Slide 13: Tech Stack

## Technologies Used

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 19 + TypeScript | UI Framework |
| Styling | Tailwind CSS | Responsive design |
| Maps | Leaflet.js | GIS visualization |
| Charts | Recharts | Data visualization |
| Backend | Python FastAPI | REST API server |
| Database | SQLite | Data storage |
| AI/ML | scikit-learn | Risk prediction |
| APIs | Open-Meteo | Real-time weather |
| Icons | Lucide React | UI icons |
| Build | Vite | Frontend bundler |

---

# Slide 14: Results & Impact

## Key Results

| Metric | Value |
|--------|-------|
| **Prototype ML validation** | District-grouped evaluation on generated/derived labels; not field accuracy |
| **Sensor Stations** | 20 across 8 NER states |
| **API Surface** | Auth, monitoring, prediction, alerts, reports, integrations and communications |
| **Historical Events** | 44 documented (2011-2024) |
| **Real Satellite Data** | 20 stations with live metrics |
| **Response Time** | <30 seconds for AI assessment |
| **Languages Supported** | 5 (EN, HI, BN, AS, OR) |
| **Deployment Ready** | Docker, Railway, Render |

### Potential Impact
- **31,977 people** currently at risk can be warned
- **31 road blockades** per year can be predicted
- **6+ hours** advance warning for landslide events
- **Real-time** monitoring replacing manual inspection

---

# Slide 15: Thank You

## 🛡️ GeoShield — Protecting NER

### Team GeoShield

| Name | Roll No |
|------|---------|
| Arghya Bose | 24155380 |
| Arindam Tripathi | 24155614 |
| Arnab Pal | 24155615 |
| Aaditree Shreya | 24155371 |
| Ankan Nag | 2405791 |
| Akash Das | 24155155 |

### Links
- **GitHub:** https://github.com/officialarghya29/GeoShield
- **Live Demo:** http://localhost:8000

### Thank You!
*Questions?*
