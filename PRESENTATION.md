# 🏆 GeoShield — SIH 2026 Presentation Deck

<p align="center">
  <img src="branding/team_logo.png" width="150" alt="Team GeoShield Logo">
</p>

## Team GeoShield | Problem Statement SIH26001 | MDoNER

---

## 📌 Slide 1: Title

### 🛡️ GeoShield
#### AI-Based Early Warning & Landslide Risk Monitoring System
**North Eastern Region (NER)**

**Smart India Hackathon 2026**
Problem Statement: SIH26001
Ministry: Ministry of Development of North Eastern Region (MDoNER)
Theme: Disaster Management

---

## 👥 Slide 2: Team GeoShield

| Name | Roll No |
|------|----------|
| **Arghya Bose** | 24155380 |
| **Arindam Tripathi** | 24155614 |
| **Arnab Pal** | 24155615 |
| **Aaditree Shreya** | 24155371 |
| **Ankan Nag** | 2405791 |
| **Akash Das** | 24155155 |

---

## 🎯 Slide 3: The Problem

### Why NER Needs This System

- **NER faces 200+ landslide events annually** — most detected reactively
- **70% of road blockages** from landslides delay emergency response by hours/days
- **Remote villages isolated for days** with no early warning
- **No real-time predictive system** exists for the region
- **Climate change increasing** rainfall intensity and landslide frequency

> "Currently, monitoring of vulnerable zones is mostly reactive and dependent on manual reporting." — SIH26001 Brief

---

## 💡 Slide 4: Our Solution

### GeoShield — Predict. Warn. Protect.

**Three Pillars:**

1. **🛰️ SENSE** — 20 IoT sensor stations across 8 NER states collecting real-time data
2. **🤖 PREDICT** — AI/ML ensemble model analyzes 15 features to predict landslide risk
3. **🚨 ACT** — Automated alerts to district authorities, SMS/push notifications, citizen reporting

**One Platform** that gives disaster managers a **single pane of glass** for the entire NER region.

---

## 🏗️ Slide 5: System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GeoShield Platform                          │
├─────────────┬───────────────────┬───────────────────────────────┤
│             │                   │                               │
│  🖥️ React UI │  ⚙️ FastAPI Server  │  🤖 AI/ML Engine              │
│  Leaflet Map │  REST + WebSocket │  RF + GB Ensemble            │
│  Recharts    │  SQLite Database  │  15 Feature Inputs           │
│  TailwindCSS │  Auto-scaling     │  Real-time Scoring           │
│             │                   │                               │
├─────────────┴───────────────────┴───────────────────────────────┤
│                      📡 Data Layer                               │
│  Rainfall • Soil Moisture • NDVI • DEM • Landslide History       │
│  Weather API • Citizen Reports • Satellite Feeds                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Slide 6: AI/ML Model

### How We Predict Landslides

**Model:** Random Forest + Gradient Boosting Ensemble (Soft Voting)

**15 Input Features:**

| Category | Features |
|----------|----------|
| Weather | Rainfall (1h, 24h, 7d, 3d cumulative) |
| Soil | Moisture, Temperature, Pore Water Pressure |
| Terrain | Slope Angle, Elevation, Vegetation Cover (NDVI) |
| Movement | Ground Displacement, Tilt (X/Y), Vibration |
| Temporal | Days Since Last Rain |

**Results:**
- Test Accuracy: **76.5%**
- Risk Score: **0-100** continuous scale
- 4 Risk Levels: Low (<25) → Moderate (25-50) → High (50-75) → Critical (>75)
- Time Window Prediction: Hours until probable event

---

## 📊 Slide 7: Live Demo Results

### What Our System Shows Right Now

| Metric | Value |
|--------|-------|
| Active Sensor Stations | **20** across 8 NER states |
| Historical Data Points | **67,200** readings |
| Risk Assessments | **960+** (48h hourly) |
| Active Alerts | **5** high-risk alerts |
| Monitored Roads | **8** (1 blocked, 2 partial) |
| Tracked Villages | **18** (6 high-risk) |
| Citizens at Risk | **31,977 people** |
| Citizen Reports | **15** submitted |

### Highest Risk Areas
1. Nagaland — Avg Risk: **76.1** ⚠️
2. Tripura — Avg Risk: **67.3** ⚠️
3. Sikkim — Avg Risk: **32.5** 🟡

---

## 🗺️ Slide 8: GIS Dashboard

### Real-Time Risk Monitoring Map

**Features:**
- Interactive Leaflet map with dark theme
- Color-coded risk markers (Green → Yellow → Orange → Red)
- Road status overlays (blocked roads highlighted)
- Village markers with population data
- Click any station → Full sensor readings + AI assessment

**8 NER States Covered:**
Sikkim • Assam • Manipur • Mizoram • Meghalaya • Nagaland • Tripura • Arunachal Pradesh

---

## 🚨 Slide 9: Early Warning System

### Alert Workflow

```
Sensor Reading → AI Risk Assessment → Risk Score → Alert Generation
                                                    ↓
                                    ┌─────────────────────────┐
                                    │  CRITICAL: EVACUATE     │
                                    │  HIGH: Pre-position     │
                                    │  MODERATE: Monitor      │
                                    │  LOW: Normal ops        │
                                    └─────────────────────────┘
                                                    ↓
                                    District Authority SMS
                                    Push Notifications
                                    Dashboard Alert
                                    Citizen App Notification
```

**Current Active Alerts:**
- Gangtok North Slope (Sikkim) — High Risk — 3,317 people
- Mangan Hill Monitor (Sikkim) — High Risk — 1,183 people
- Churachandpur Hills (Manipur) — High Risk — 1,423 people
- Aizawl Ridge Monitor (Mizoram) — High Risk — 1,173 people
- Ziro Valley Watch (Arunachal) — High Risk — 991 people

---

## 📝 Slide 10: Citizen Reporting

### Crowdsourced Ground Truth

**How it works:**
1. Citizen/field officer sees suspicious activity (cracks, slope movement, blocked roads)
2. Opens GeoShield app → Takes geo-tagged photo
3. Selects report type → Submits
4. Report appears on dashboard for verification
5. Verified reports feed back into AI model

**Multilingual Support:**
- English 🇬🇧
- Hindi 🇮🇳
- Bengali 🇧🇩
- Assamese 🇮🇳

---

## 🛰️ Slide 11: Data Sources

### Real-World Data Integration

| Source | Type | Status |
|--------|------|--------|
| NASA Global Landslide Catalog | Historical events | ✅ Integrated |
| Open-Meteo API | Live weather + soil moisture | ✅ Live |
| Kaggle IMD Rainfall | Historical rainfall | ✅ Integrated |
| USGS SRTM DEM | Terrain/elevation data | 📋 Ready to integrate |
| Copernicus Sentinel-2 | NDVI satellite imagery | 📋 Ready to integrate |
| IMD API | Official weather data | 📋 Ready to integrate |

**Free accounts** — No credit card required for Copernicus and USGS.

---

## 🏆 Slide 12: Why GeoShield Wins

### Impact & Innovation

| Criteria | Our Strength |
|----------|-------------|
| **Innovation** | AI ensemble model + real-time GIS + citizen crowdsourcing |
| **Impact** | 31,977 people protected, 20 stations, 8 states |
| **Scalability** | Cloud-ready architecture, adding stations is trivial |
| **Feasibility** | Working prototype with 67,200+ data points |
| **Sustainability** | Open-source, low-cost IoT sensors, government integration |
| **Uniqueness** | Only platform combining AI prediction + GIS + citizen reports for NER |

### What Makes Us Different
1. **Not just monitoring** — We **predict** landslides before they happen
2. **Not just data** — We **act** with automated alerts and citizen reports
3. **Not just a dashboard** — We **protect** with evacuation recommendations

---

## 📈 Slide 13: Technical Specifications

### Performance Metrics

| Metric | Value |
|--------|-------|
| API Response Time | < 200ms |
| AI Model Inference | < 50ms per station |
| Data Points Processed | 67,200+ hourly readings |
| Risk Assessment Refresh | Every 30 seconds |
| Alert Broadcast | Real-time WebSocket |
| Historical Data Retention | 7 days (expandable) |
| Supported Languages | 5 (EN, HI, BN, AS, OR) |
| Browser Support | Chrome, Firefox, Safari, Edge |

---

## 🚀 Slide 14: Future Roadmap

### Phase 2 Enhancements

1. **Real IoT Sensors** — Deploy physical sensor stations in high-risk zones
2. **Satellite Integration** — Real-time NDVI from Sentinel-2, DEM from SRTM
3. **IMD API Integration** — Official weather forecasts and warnings
4. **Mobile App** — Native Android/iOS app for field officers
5. **SMS Alerts** — Integration with telecom providers for SMS broadcasts
6. **Offline Mode** — Progressive Web App for low-network areas
7. **Multi-hazard** — Expand to floods, earthquakes, fire

---

## 🙏 Slide 15: Thank You

### Team GeoShield

**"Protecting Lives Through AI-Powered Early Warning"**

🔗 **GitHub:** github.com/officialarghya29/GeoShield
🌐 **Demo:** localhost:8000

**SIH 2026 | Problem Statement SIH26001 | MDoNER | Disaster Management**

---

*Built with ❤️ by Team GeoShield for Smart India Hackathon 2026*
