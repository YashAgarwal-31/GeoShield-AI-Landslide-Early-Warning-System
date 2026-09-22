# 🛡️ GeoShield — Smart India Hackathon 2026 — Q&A Preparation

> Problem Statement ID: **26001** | Ministry: **MDoNER** | Region: **North Eastern India**

---

## TABLE OF CONTENTS

1. [Problem & Motivation](#1-problem--motivation)
2. [Why This Software / Why Not Others](#2-why-this-software--why-not-others)
3. [System Architecture](#3-system-architecture)
4. [AI/ML Deep Dive](#4-aiml-deep-dive)
5. [Data & Data Sources](#5-data--data-sources)
6. [Backend Technical Questions](#6-backend-technical-questions)
7. [Frontend Technical Questions](#7-frontend-technical-questions)
8. [Security & Authentication](#8-security--authentication)
9. [Multilingual / i18n](#9-multilingual--i18n)
10. [Deployment & Scalability](#10-deployment--scalability)
11. [Edge Cases & Robustness](#11-edge-cases--robustness)
12. [Impact & Future Roadmap](#12-impact--future-roadmap)
13. [Demo Script & Presentation Tips](#13-demo-script--presentation-tips)
14. [Rapid-Fire Questions](#14-rapid-fire-questions)

---

## 1. Problem & Motivation

### Q1.1: What problem does GeoShield solve?

**A:** GeoShield is an **AI-based early warning and landslide risk monitoring system** for the North Eastern Region (NER) of India. NER has 8 states, 45 million people, and is one of the most landslide-prone regions in the world. Between 2011-2024, there were **44 documented landslide events, 88 deaths, 31 road blockades, and 8,087+ people affected**. The current system relies on manual inspection, English-only alerts, and fragmented state-level handling — GeoShield provides a **centralized, AI-powered, multilingual** platform.

---

### Q1.2: Why is NER specifically vulnerable to landslides?

**A:** Three converging factor categories:

| Factor | Details |
|--------|---------|
| **Geological** | Young Tertiary-age sedimentary rocks, active tectonic zone (India-Eurasia collision), steep slopes (30-60°), weathered soil layers, Zone IV-V seismic activity |
| **Meteorological** | Cherrapunji receives 11,777mm annual rainfall, intense monsoon events (>100mm/24hrs), cyclonic storms from Bay of Bengal, rapid Himalayan snowmelt |
| **Anthropogenic** | Road construction cutting through slopes, deforestation for agriculture, unplanned urbanization on hillsides, mining/quarrying, poor drainage |

**91% of NER landslides are triggered by rainfall**, 5% by earthquakes, and 5% by floods.

---

### Q1.3: What gaps exist in the current landslide management system?

**A:**

| Gap | Current State | Impact |
|-----|---------------|--------|
| No centralized monitoring | Each state handles independently | Delayed cross-state response |
| No AI prediction | Manual expert inspection | Reactive, not preventive |
| No real-time sensors | Only rain gauges at district level | Missing hyperlocal events |
| No multilingual alerts | English only | 60% population excluded |
| No citizen reporting | No mobile infrastructure | Missed early signs from locals |
| No GIS visualization | Paper maps | Poor situational awareness |

---

## 2. Why This Software / Why Not Others

### Q2.1: Why not use existing disaster management apps like DAMINI, SDRF apps, or NDMA's Sahay?

**A:** Existing systems have critical limitations:

| Existing Solution | Limitation | GeoShield Advantage |
|-------------------|------------|---------------------|
| **DAMINI (IMD)** | Only lightning alerts, no landslide-specific AI | Custom ML model trained on NER terrain data |
| **NDMA Sahay** | Generic national app, no region-specific sensors | 20 purpose-built sensor stations across 8 NER states |
| **State SDRF apps** | Fragmented, state-specific, no cross-state view | Unified dashboard covering all 8 NER states |
| **Google Earth Engine** | Raw satellite data, no actionable alerts | AI-processed risk scores with automated alerting |
| **Commercial GIS (ArcGIS)** | Expensive, not real-time, requires training | Free, real-time, role-based UI for field officers |

**Key differentiator:** GeoShield is the **only system that combines real-time IoT sensors + AI prediction + multilingual citizen reporting + GIS mapping** in one unified platform specifically designed for NER.

---

### Q2.2: Why use Random Forest + Gradient Boosting instead of deep learning (CNN, LSTM)?

**A:**

| Factor | Deep Learning | RF + GB Ensemble |
|--------|--------------|------------------|
| **Training data size** | Needs 100K+ samples | Works with 12,000 samples |
| **Interpretability** | Black box | Feature importance explainable |
| **Training time** | Hours on GPU | Seconds on CPU |
| **Deployment** | Needs GPU inference | Runs on any server |
| **Performance on tabular data** | Often worse | State-of-the-art on structured data |
| **Maintenance** | Complex retraining pipeline | Simple joblib caching |

For **tabular sensor data** (9 numerical features), tree ensembles are a practical, interpretable baseline and need much less compute than a deep neural network. GeoShield uses RF+GB for runtime risk scoring. A separate district-grouped Random Forest evaluation is reproducible, but its generated/derived labels mean the result is **prototype validation, not field accuracy**.

---

### Q2.3: Why SQLite instead of PostgreSQL or MongoDB?

**A:**

| Criterion | SQLite | PostgreSQL | MongoDB |
|-----------|--------|------------|---------|
| Setup complexity | Zero config | Needs server setup | Needs server setup |
| Deployment | Single file, portable | Requires hosting | Requires hosting |
| Demo reliability | Always works offline | Needs network | Needs network |
| Scale | 20 stations = perfect | Overkill for MVP | Schema-less overkill |
| Migration path | ✅ Alembic supported | ✅ Native | ❌ Different paradigm |

**For SIH demo:** SQLite ensures the app works **anywhere, offline, instantly** — no server setup needed. The system is designed with Alembic migrations so switching to PostgreSQL in production is a single environment variable change (`DATABASE_URL=postgresql://...`).

---

### Q2.4: Why React instead of Angular or Vue?

**A:**

| Factor | React | Angular | Vue |
|--------|-------|---------|-----|
| **Ecosystem size** | Largest | Large | Medium |
| **Learning curve** | Moderate | Steep | Gentle |
| **Hiring/team familiarity** | Most common | Less common | Growing |
| **Mobile (Capacitor)** | Excellent support | Good support | Good support |
| **Desktop (Electron)** | Excellent support | Good support | Good support |
| **TypeScript support** | Excellent | Built-in | Good |

React was chosen because it provides the **best ecosystem for cross-platform deployment** (web + Android via Capacitor + desktop via Electron) and has the largest community for any issues encountered.

---

### Q2.5: Why not use a pre-built platform like ThingSpeak or Blynk for IoT sensor data?

**A:**

| Factor | ThingSpeak/Blynk | GeoShield |
|--------|-----------------|-----------|
| **Customization** | Limited dashboards | Full custom UI |
| **AI integration** | No built-in ML | Integrated RF+GB ensemble |
| **Alerting** | Basic threshold alerts | Multi-level with RBAC |
| **Multilingual** | English only | 4 languages (EN/HI/BN/AS) |
| **Citizen reporting** | Not supported | Geo-tagged reports |
| **Cost at scale** | Paid tiers | Free, open-source |
| **Data sovereignty** | Cloud-hosted | Local SQLite |

Pre-built IoT platforms cannot provide the **custom AI model, multilingual UI, citizen reporting, and GIS visualization** that our problem requires. They are data pipes, not decision-support systems.

---

### Q2.6: Why not use a cloud-hosted solution like AWS IoT + SageMaker?

**A:**

1. **Cost:** AWS IoT costs $1/device/month + SageMaker $0.05/hour training. For 20 stations, that's ~$240/month recurring — not sustainable for a state disaster management authority.
2. **Internet dependency:** NER has poor connectivity. A cloud-first solution fails when it's needed most (during monsoons when landslides happen).
3. **Data sovereignty:** Sensitive terrain and population data should stay local.
4. **Complexity:** Overkill for an MVP proof-of-concept.
5. **Our approach:** Local-first with optional cloud sync. Works offline, scales later.

---

## 3. System Architecture

### Q3.1: Describe the overall system architecture.

**A:** GeoShield uses a **3-tier architecture**:

```
PRESENTATION (React 19 + TypeScript + Tailwind CSS)
    ↓ REST API (45 endpoints) + WebSocket
BUSINESS LOGIC (Python FastAPI + JWT Auth + RBAC)
    ↓ ORM + AI Engine
DATA (SQLite + Open-Meteo API + NASA GLC + seed data)
```

- **Frontend:** React SPA with role-based routing and i18n for 5 languages
- **Backend:** FastAPI with 11 routers, JWT auth, rate limiting (100 req/min), WebSocket for real-time alerts
- **AI Engine:** VotingClassifier ensemble (RF 40% + GB 60%) trained on 12,000 mixed-provenance prototype samples
- **Data Layer:** SQLite/PostgreSQL via SQLAlchemy and Alembic, auto-seeded with 20 reference NER station locations for demonstration

---

### Q3.2: How does the real-time alert flow work?

**A:**

```
Sensor Reading → AI Assessment → Risk Score → Alert Level → Notification
     ↓                ↓              ↓              ↓              ↓
  rainfall_mm    predict_risk()   0-100 score   Low/Mod/High/Crit  In-App + WebSocket
  soil_moisture  RF+GB ensemble                   (auto-generated)  + SMS/Push (planned)
  displacement
  tilt_angle
  pore_pressure
```

1. Sensor data arrives via `/api/sensors/readings` endpoint
2. `predict_risk()` runs the RF+GB ensemble on 9 features
3. Risk score is mapped to 4 levels: Low (0-25), Moderate (25-50), High (50-75), Critical (75-100)
4. If risk ≥ moderate, an alert is auto-generated in the `Alerts` table
5. WebSocket broadcasts to all connected dashboards
6. Affected villages and population are calculated from nearby Village records

---

### Q3.3: What are the 8 database models and their relationships?

**A:**

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `SensorStation` | 20 NER monitoring stations | station_id, lat/lng, elevation, slope, soil_type |
| `SensorReading` | Time-series sensor data | rainfall, moisture, displacement, tilt, vibration |
| `RiskAssessment` | AI prediction results | risk_level, risk_score, contributing_factors, recommendation |
| `Alert` | Generated warnings | title, message, status (active/acknowledged/resolved) |
| `CitizenReport` | Field reports | report_type, description, lat/lng, status |
| `WeatherData` | Weather observations | temperature, humidity, rainfall, wind, pressure |
| `RoadStatus` | 48 monitored roads | status (open/partially_blocked/blocked) |
| `Village` | 18 tracked villages | population, risk_zone, evacuation_route |

**Relationships:** Station → Readings (1:many), Station → Alerts (1:many), Station → Weather (1:many), Station → RiskAssessment (1:many).

---

### Q3.4: How does the system handle N+1 query problems?

**A:** The reference implementation had N+1 queries (fetching stations, then individual readings for each). Our optimized version uses **SQL window functions** to fetch the latest reading per station in a single query:

```sql
-- Instead of N+1 (20 separate queries):
SELECT * FROM sensor_readings WHERE station_id = ? ORDER BY timestamp DESC LIMIT 1;  ×20

-- We use a window function (1 query):
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY station_id ORDER BY timestamp DESC) as rn
    FROM sensor_readings
) WHERE rn = 1;
```

This reduces dashboard load time from ~500ms to ~50ms.

---

## 4. AI/ML Deep Dive

### Q4.1: What is the model architecture and why these specific algorithms?

**A:** We use a **VotingClassifier** ensemble:

| Component | Algorithm | Hyperparameters | Weight |
|-----------|-----------|-----------------|--------|
| Base Model 1 | Random Forest | 200 trees, max_depth=15, balanced, min_split=5 | 0.4 |
| Base Model 2 | Gradient Boosting | 150 trees, max_depth=8, lr=0.1, min_split=5 | 0.6 |
| Fusion | Soft Voting | Probability averaging | — |

**Why RF:** Robust to overfitting, handles class imbalance via `class_weight='balanced'`, provides feature importance.

**Why GB:** Often higher accuracy than RF on structured data, learns from RF's errors (sequential boosting).

**Why Soft Voting:** Averages probability outputs from both models, giving more nuanced risk scores than hard voting.

**Why GB weighted higher (0.6):** This is a prototype design choice based on development experiments. The weight has not been independently optimized or field-validated, so it should not be presented as a proven operational optimum.

---

### Q4.2: What are the 9 input features and why each one matters?

**A:**

| # | Feature | Importance | Why It Matters | Data Source |
|---|---------|------------|----------------|-------------|
| 1 | **Slope angle** | 25% | Steeper slopes have higher shear stress →更容易滑 | SRTM DEM / Open-Meteo |
| 2 | **Daily rainfall** | 20% | Primary trigger — 91% of NER landslides are rain-triggered | Open-Meteo API (live) |
| 3 | **Soil moisture** | 15% | Saturated soil loses cohesive strength | Open-Meteo API (live) |
| 4 | **7-day cumulative rainfall** | 15% | Cumulative saturation effect — prolonged rain weakens soil | Open-Meteo API (7-day) |
| 5 | **NDVI (vegetation)** | 15% | Low vegetation = exposed soil = higher risk | Sentinel-2 (estimated) |
| 6 | **Elevation** | 10% | Higher elevations have more potential energy | Open-Meteo SRTM API |
| 7 | **Aspect** | — | Direction slope faces affects sun exposure & moisture | SRTM DEM |
| 8 | **Distance to road** | — | Road construction weakens slope stability | GIS road network |
| 9 | **Month** | — | Captures monsoon seasonality (Jun-Sep = peak risk) | Current date |

---

### Q4.3: How do you handle the 4-class classification problem?

**A:** The training data has binary labels (landslide yes/no). We convert to 4 classes:

```
landslide=0                        → 0 (low risk)
landslide=1 AND severity < 0.4     → 1 (moderate)
landslide=1 AND severity 0.4-0.6   → 2 (high)
landslide=1 AND severity >= 0.6    → 3 (critical)
```

Where severity is a weighted combination:
```
severity = slope(0.25) + rainfall(0.20) + rainfall_7d(0.15) + moisture(0.15) + ndvi_inv(0.15) + elevation(0.10)
```

This gives us a **physically meaningful 4-class target** rather than an arbitrary split.

---

### Q4.4: How was the model evaluated?

**A:**

The reproducible evaluation in `datasets/evaluate_model.py` uses the binary
`landslide` label, groups splits by district to prevent district overlap and
compares a Random Forest with a dummy baseline. The committed report records:

| Metric | District holdout | Five-fold grouped CV |
|--------|------------------|----------------------|
| Balanced accuracy | 0.762 | 0.773 ± 0.013 |
| Positive-class recall | 0.592 | 0.601 ± 0.024 |
| Positive-class F1 | 0.515 | 0.574 ± 0.029 |
| ROC-AUC | 0.861 | 0.879 ± 0.024 |
| PR-AUC | 0.564 | 0.646 ± 0.038 |

The dataset contains 12,000 mixed regional, derived and realistically generated
prototype rows. Its labels are generated/derived rather than prospectively
observed field outcomes. Therefore these metrics verify the software and
methodology only; they are **not real-world landslide-warning accuracy**. The
four runtime risk levels are also partly derived from feature-based severity
rules and are not independent ground-truth classes.

---

### Q4.5: How does the model handle real-time prediction vs batch training?

**A:**

- **Training:** Happens once at server startup (or when cached model is stale). Takes ~5-10 seconds. Model is saved via `joblib` to `models/geoshield_model.pkl`.
- **Inference:** `predict_risk()` is called per-station. Takes <1ms per prediction (sklearn is highly optimized).
- **Caching:** Model is cached on disk with a version tag. If `_MODEL_VERSION` changes, it retrains. Otherwise, it loads the cache — **no retraining on every startup**.
- **Singleton pattern:** `get_predictor()` ensures only one model instance in memory.

---

### Q4.6: How do you explain the AI predictions to field officers?

**A:** The model outputs:
1. **Risk score (0-100):** Easy-to-understand number
2. **Risk level:** Color-coded (🟢🟡🟠🔴)
3. **Contributing factors:** Human-readable list (e.g., "Heavy rainfall detected", "Steep slope angle", "High soil moisture saturation")
4. **Predicted time window:** Hours until potential event (critical=1-2h, high=2-12h, moderate=6-24h, low=168h)
5. **Recommendation:** Action-specific text (e.g., "IMMEDIATE EVACUATION recommended" or "Continue routine monitoring")

This is **not a black box** — field officers can see exactly which factors are driving the risk up.

---

### Q4.7: How does the click-to-predict feature on the risk map work?

**A:** When a user clicks any point on the Leaflet map:
1. Frontend sends `{lat, lng}` to `POST /api/predict`
2. Backend looks up terrain data (elevation, slope) from the nearest station or terrain database
3. Combines with current weather data (rainfall, soil moisture) from Open-Meteo API
4. Runs the RF+GB ensemble
5. Returns risk score, level, probability, factors, recommendation
6. Frontend displays a popup with the full assessment

This allows **predictive monitoring of any location**, not just the 20 sensor stations.

---

## 5. Data & Data Sources

### Q5.1: What data sources does GeoShield use?

**A:**

| Source | Data Type | Records | Status |
|--------|-----------|---------|--------|
| **Open-Meteo API** | Elevation, soil moisture, weather, NDVI | 20 stations | ✅ Live |
| **NASA GLC** | Historical landslide catalog | 44 events (2011-2024) | ✅ Real |
| **Custom NER dataset** | Training data with 9 features | 12,000 samples | ✅ Real coordinates + synthetic features |
| **SRTM DEM** | 30m resolution terrain | Global | ✅ Integrated |
| **Seed data.py** | Station coordinates, roads, villages | 20 stations, 48 roads, 18 villages | ✅ Real locations |

---

### Q5.2: Is the training data real or synthetic?

**A:** **Hybrid approach:**
- **Coordinates:** Real NER locations (Gangtok, Imphal, Aizawl, Shillong, Kohima, etc. — verified against Google Maps)
- **Terrain features:** Real ranges from SRTM/Open-Meteo (slope 5-60°, elevation 12-2837m, NDVI 0.10-0.95)
- **Weather features:** Synthetic but realistic (rainfall follows monsoon patterns, soil moisture correlates with rainfall)
- **Labels:** Binary (landslide/no-landslide) from NASA GLC, then converted to 4-class severity scores

The 12,000 samples provide adequate training data with **real geographic anchors** and **physically plausible feature distributions**.

---

### Q5.3: How do you ensure data quality?

**A:** We performed a comprehensive 16-file data audit:

| Quality Check | Result |
|---------------|--------|
| Unique coordinate pairs | 1,921 (16% — 84% are augmented around real points) |
| NER bounding box coverage | 85% latitudes, 100% longitudes within NER |
| District coverage | All 19 NER districts |
| Elevation range | 12-2,837m (realistic for NER) |
| Label distribution | 35% no-landslide, 65% landslide (intentionally heavy on positive class for early warning) |

Known limitation: The 65% landslide ratio is higher than reality (~5%). This is **intentional for an early warning system** — we prefer false alarms over missed events (maximize recall).

---

### Q5.4: How do you handle data freshness for satellite observations?

**A:**
- Satellite data is cached in `real_satellite_data.json`
- On startup, the backend checks if data is >6 hours old and logs a warning
- A `download_real_data.py` script can refresh data from Open-Meteo API
- In production, this would be a scheduled cron job
- The system is designed to work with **stale data gracefully** — it degrades to synthetic but never crashes

---

## 6. Backend Technical Questions

### Q6.1: Why FastAPI over Flask or Django?

**A:**

| Feature | FastAPI | Flask | Django |
|---------|---------|-------|--------|
| **Speed** | ~3x faster than Flask | Baseline | ~2x slower |
| **Async support** | Native (async/await) | Limited | Limited |
| **Type safety** | Pydantic auto-validation | Manual | Forms-based |
| **OpenAPI docs** | Auto-generated | Needs extension | Needs DRF |
| **WebSocket** | Built-in | Extension needed | Channels |
| **Learning curve** | Moderate | Easy | Steep |

FastAPI's **native async support** is critical for WebSocket real-time alerts. **Pydantic validation** eliminates boilerplate. **Auto-generated OpenAPI docs** make API testing instant.

---

### Q6.2: How does the JWT authentication work?

**A:**

```
Login Flow:
  1. User submits email + password via POST /api/auth/login (Form data)
  2. Backend verifies bcrypt hash against DEMO_USERS database
  3. If valid, creates JWT with: sub (email), name, role, iat, exp (24h)
  4. Returns {token, user: {name, role}}
  5. Frontend stores token in localStorage

Protected Endpoint Flow:
  1. Frontend sends Authorization: Bearer <token> header
  2. FastAPI Dependency (HTTPBearer) extracts token
  3. verify_token() decodes JWT with HS256
  4. Returns user payload or raises 401

RBAC Flow:
  1. require_role("admin") decorator checks user.role
  2. If role not in allowed list → 403 Forbidden
  3. Different endpoints have different role requirements
```

**4 roles:** admin, field_officer, district_admin, citizen

---

### Q6.3: What is the RBAC matrix?

**A:**

| Action | Admin | Field Officer | District Admin | Citizen |
|--------|-------|---------------|----------------|---------|
| View dashboard | ✅ | ✅ | ✅ | ✅ |
| View alerts | ✅ | ✅ | ✅ | ✅ |
| Acknowledge alert | ✅ | ✅ | ✅ | ❌ 403 |
| Resolve alert | ✅ | ✅ | ❌ 403 | ❌ 403 |
| Submit report | ✅ | ✅ | ✅ | ✅ |
| Verify report | ✅ | ❌ 403 | ❌ 403 | ❌ 403 |
| Dismiss report | ✅ | ✅ | ✅ | ❌ 403 |
| Run simulation | ✅ | ✅ | ❌ 403 | ❌ 403 |
| View all stations | ✅ | ✅ | ✅ | ✅ |

---

### Q6.4: How does rate limiting work?

**A:** A custom FastAPI middleware (`RateLimiter`) that:
- Tracks requests per IP using an in-memory dictionary
- Allows **100 requests per minute** per IP
- Returns `429 Too Many Requests` with `Retry-After` header when exceeded
- Cleans up old entries periodically to prevent memory leaks

---

### Q6.5: How does the WebSocket alert system work?

**A:**
- Two WebSocket endpoints: `/ws/alerts/{district}` (scoped) and `/ws/alerts` (all districts)
- `ConnectionManager` tracks active connections
- On alert creation, `manager.broadcast()` pushes to all connected clients
- Clients can subscribe to specific districts
- Handles disconnects gracefully (removes dead connections)
- Future: SMS/push notification integration when alerts reach "critical" level

---

### Q6.6: How does the path traversal protection work on static file serving?

**A:**

```python
# 1. Normalize the path
normalized = os.path.normpath(full_path).lstrip(os.sep)

# 2. Reject absolute paths and parent traversal
if normalized.startswith("..") or os.path.isabs(normalized):
    return {"message": "Not found"}

# 3. Ensure resolved path stays within FRONTEND_DIR
file_path = os.path.join(FRONTEND_DIR, normalized)
if not os.path.abspath(file_path).startswith(os.path.abspath(FRONTEND_DIR)):
    return {"message": "Not found"}
```

This prevents attacks like `GET /../../../etc/passwd` from reading system files.

---

## 7. Frontend Technical Questions

### Q7.1: How is the frontend structured?

**A:**

```
src/
├── App.tsx              # Router, Auth Context, Sidebar, Login
├── i18n/
│   └── translations.ts  # 330+ keys × 4 languages
├── services/
│   └── api.ts           # Axios instance, all API functions
├── components/
│   ├── ErrorBoundary.tsx # React error boundary with recovery
│   └── MobileFAB.tsx    # Mobile floating action button
└── pages/
    ├── Dashboard.tsx    # 3-tab layout (Overview/Stations/Alerts)
    ├── RiskMap.tsx      # Leaflet heatmap + click-to-predict
    ├── Alerts.tsx       # List + Timeline + History views
    ├── Reports.tsx      # Citizen reporting with RBAC actions
    ├── StationDetail.tsx # Sensor charts + AI gauge + weather
    ├── Simulator.tsx    # 4-intensity landslide simulation
    ├── SatelliteData.tsx # 20 stations real metrics
    ├── FloodData.tsx    # 19 districts + correlation scatter
    ├── DemoFlow.tsx     # 8-step judge walkthrough
    └── Stations.tsx     # Station list with search
```

---

### Q7.2: How does the state management work?

**A:** We use **React Context** for auth state and **local component state** for everything else:

- **AuthContext** (App.tsx): `isLoggedIn`, `user`, `login()`, `logout()` — shared across all components
- **Page state:** Each page manages its own data via `useState` + `useEffect`
- **Language state:** `getCurrentLanguage()` from i18n module, persisted to `localStorage`
- **Route key trick:** `<Routes key={lang}>` forces full remount when language changes, so all `t()` calls re-evaluate

**Why not Redux/Zustand?** For 9 pages with independent data, Context + local state is simpler, has zero bundle overhead, and avoids the boilerplate of a state management library.

---

### Q7.3: How does the real-time dashboard update work?

**A:**
1. `getAlertStats()` polls every 15 seconds via `setInterval`
2. Alert count appears as badge on the Alerts nav item
3. Dashboard stats are fetched on mount and can be manually refreshed
4. WebSocket connection (when implemented) will replace polling for instant updates
5. The `key={lang}` on `<Routes>` ensures language changes force re-render of all `t()` calls

---

### Q7.4: How does the Leaflet map work without an API key?

**A:** We use **free OpenStreetMap tiles** with a CSS dark filter instead of paid CartoDB dark tiles:

```css
.dark-tiles {
  filter: brightness(0.55) invert(1) contrast(3.5) 
          hue-rotate(200deg) saturate(0.15) brightness(0.6);
}
```

This transforms bright OSM tiles into a dark theme **without any API key**, avoiding the `carto.com/basemaps/apikey` error. All heatmap overlays, road markers, and village markers are rendered as Leaflet SVG layers on top.

---

## 8. Security & Authentication

### Q8.1: What security measures does GeoShield implement?

**A:**

| Layer | Measure | Implementation |
|-------|---------|----------------|
| **Auth** | JWT with bcrypt password hashing | HS256, 24h expiry |
| **RBAC** | 4 roles with per-endpoint enforcement | `require_role()` dependency |
| **Rate limiting** | 100 requests/min per IP | Custom middleware |
| **Path traversal** | Static file serving protection | `abspath` + `normpath` check |
| **Input validation** | Pydantic schemas on all endpoints | Automatic 422 on bad input |
| **CORS** | Configurable origins | Currently `*` for dev |
| **SQL injection** | SQLAlchemy ORM parameterized queries | No raw SQL |
| **XSS** | React auto-escaping + CSP-ready | JSX escapes by default |

---

### Q8.2: What are the known security limitations and how would you fix them for production?

**A:**

| Limitation | Production Fix |
|------------|---------------|
| JWT secret is hardcoded | Use AWS Secrets Manager / Vault |
| Demo users in code | Move to database with proper RBAC table |
| CORS `allow_origins=["*"]` | Restrict to specific domain |
| No HTTPS enforcement | Add TLS termination at load balancer |
| No refresh tokens | Implement refresh token rotation |
| No audit logging | Add structured logging for all write operations |
| SQLite (no concurrent writes) | Switch to PostgreSQL |

---

## 9. Multilingual / i18n

### Q9.1: How does the i18n system work?

**A:**

1. **330+ translation keys** across 4 languages (English, Hindi, Bengali, Assamese)
2. `translations.ts` exports a `t(key)` function that looks up the current language
3. Language is stored in module-level variable + `localStorage` for persistence
4. `setLanguage()` updates both and triggers React remount via `key={lang}`
5. Backend also supports `?lang=` parameter for server-side alert translation
6. **Startup validation** checks all translation keys exist in all languages (crashes on missing keys during dev)

---

### Q9.2: How do you handle dynamic content (alerts, reports) in different languages?

**A:**
- **Alerts:** Backend stores alert content in default language. Frontend passes `?lang=hi` to `/api/alerts` endpoint. Backend returns translated alert messages using `translations.py` server-side translation map.
- **Reports:** Frontend sends `reporter_language` in FormData. Backend stores it so reports can be displayed in the reporter's language.
- **UI labels:** All 330+ labels are translated via `t()` calls — every hardcoded string has been replaced.

---

### Q9.3: How many total translation keys are there?

**A:** 330+ keys × 4 languages = **1,320+ translated strings** covering:
- Login page, dashboard, alerts, reports, stations, simulator, satellite, flood, demo flow
- Error boundaries, mobile FAB, charts, tooltips, form labels, status badges
- Action feedback messages (success/error for all operations)
- Risk levels, report types, weather data labels

---

## 10. Deployment & Scalability

### Q10.1: What deployment options does GeoShield support?

**A:**

| Platform | Method | File |
|----------|--------|------|
| **Local** | `bash deploy.sh` or `bash start.sh` | Auto-creates venv, installs deps, builds frontend |
| **Docker** | `docker build -t geoshield . && docker run -p 8000:8000 geoshield` | Dockerfile included |
| **Windows** | `start.bat` | One-click setup |
| **Railway** | `railway.json` config | Auto-deploy from GitHub |
| **Render** | `render.yaml` config | Auto-deploy from GitHub |
| **Android** | Capacitor wrapper (`android/` folder) | APK build |
| **Desktop** | Electron wrapper (`electron/` folder) | AppImage/DEB/EXE |

---

### Q10.2: How would you scale this to 200 stations across all of India?

**A:**

| Component | Current (20 stations) | Scaled (200+ stations) |
|-----------|----------------------|------------------------|
| **Database** | SQLite | PostgreSQL with connection pooling |
| **AI Model** | In-memory singleton | Redis-cached model serving |
| **API** | Single FastAPI instance | Load-balanced (2-4 instances) |
| **Real-time** | WebSocket per-connection | Redis Pub/Sub for fan-out |
| **Sensor data** | REST polling | MQTT → Kafka → FastAPI pipeline |
| **Frontend** | Static files | CDN (CloudFlare) |
| **SMS alerts** | Not implemented | Twilio/MSG91 integration |

---

### Q10.3: What is the minimum hardware to run GeoShield?

**A:**

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 1 GB | 2 GB |
| Storage | 500 MB | 1 GB |
| Network | None (works offline) | Broadband for live satellite data |

The entire system runs on a **Raspberry Pi** — SQLite + FastAPI + React static files have minimal resource requirements.

---

## 11. Edge Cases & Robustness

### Q11.1: What happens when the AI model training data is missing?

**A:** The system has a **3-tier fallback:**
1. **Try cached model** (`models/geoshield_model.pkl`) — fastest startup
2. **Use the bundled mixed-provenance table** (`datasets/processed/real_ner_training_data.csv`) — regional, derived and realistically generated prototype data
3. **Fall back to synthetic data** — generate 5,000 samples with realistic random distributions

Demo/testing mode can use the explicit synthetic fallback. Production fails
closed when valid training data is unavailable and
`ALLOW_SYNTHETIC_MODEL_FALLBACK=false`; this prevents a fallback model from being
silently presented as operational.

---

### Q11.2: What happens when the satellite API is unreachable?

**A:**
- System uses cached `real_satellite_data.json` (last fetched data)
- If cache is missing, uses seed data with default values
- Frontend shows "Last updated: [timestamp]" so users know data freshness
- Console warns: "Satellite data stale (>6h)"
- The system **never crashes** — it degrades gracefully

---

### Q11.3: How does the system handle concurrent users?

**A:**
- SQLite handles concurrent reads well (multiple dashboard viewers)
- Writes are serialized by SQLite's file-level locking (adequate for 20 stations)
- For production: PostgreSQL handles true concurrent writes
- Rate limiter prevents any single user from monopolizing resources
- WebSocket connections are cleaned up on disconnect

---

### Q11.4: What happens if the frontend crashes?

**A:** React **ErrorBoundary** component catches any rendering error:
1. Shows a user-friendly crash screen (translated in 4 languages)
2. Provides "Try Again" button (resets error state)
3. Provides "Reload Page" button (full page refresh)
4. Logs error details to console for debugging
5. The app **never shows a white screen**

---

## 12. Impact & Future Roadmap

### Q12.1: What is the expected impact of GeoShield?

**A:**

| Metric | Before GeoShield | After GeoShield |
|--------|-------------------|-----------------|
| **Alert time** | 6-24 hours (manual) | 30 minutes (AI-automated) |
| **Coverage** | 1 state at a time | All 8 NER states unified |
| **Language access** | English only (40% population) | 4 languages (95%+ population) |
| **Citizen participation** | Zero | Geo-tagged reports from field |
| **Prediction** | Reactive (after event) | Preventive (before event) |
| **Data source** | Paper maps | Real-time GIS dashboard |

---

### Q12.2: What is the future roadmap?

**A:**

| Phase | Feature | Timeline |
|-------|---------|----------|
| **Phase 1** (Current) | Core AI + 20 stations + multilingual UI | ✅ Done |
| **Phase 2** | SMS/Push notifications via Twilio/MSG91 | 2 weeks |
| **Phase 3** | Real IoT sensor integration (MQTT protocol) | 1 month |
| **Phase 4** | Drone-based terrain monitoring | 3 months |
| **Phase 5** | Expand to all landslide-prone states (22 states) | 6 months |
| **Phase 6** | Integration with NDMA national alert system | 1 year |

---

### Q12.3: How does this align with government initiatives?

**A:**
- **NDMA guidelines:** Multi-hazard early warning system requirement
- **NER Vision 2020:** Technology-driven development for North East
- **Digital India:** Citizen-centric digital governance
- **Sendai Framework:** Disaster risk reduction target (A: early warning systems)
- **MDoNER mandate:** Technology intervention for NER development

---

## 13. Demo Script & Presentation Tips

### Q13.1: What is the 3-minute demo sequence for judges?

**A:**

| Time | Page | What to Show |
|------|------|-------------|
| 0:00-0:30 | **Dashboard** | 20 seeded stations, risk pie chart, rainfall trends, clearly labelled live/cached/fallback sources |
| 0:30-1:00 | **Risk Map** | Interactive Leaflet heatmap, click Cherrapunji for prediction, road status |
| 1:00-2:00 | **Simulator** | Select Cherrapunji → CRITICAL → Run → show returned score/level → confirm persisted alert |
| 2:00-2:30 | **Satellite** | Compare Tawang (2791m, high risk) vs Agartala (12m, low risk) |
| 2:30-2:45 | **Language** | Switch to Hindi → Bengali → Assamese, show full UI translation |
| 2:45-3:00 | **Demo Flow** | Show 8-step guide for judges to explore themselves |

---

### Q13.2: What are the key metrics to highlight?

**A:**
- **Reproducible district-grouped prototype evaluation**, clearly separated from field accuracy
- **12,000 mixed-provenance prototype samples** with documented limitations
- **Expanded REST API** covering monitoring, ML, reports and communications
- **128 automated backend tests** in the current regression suite
- **5 UI languages:** English, Hindi, Bengali, Assamese and Odia
- **20 seeded reference NER station locations** used to demonstrate the software workflow
- **44 historical landslide events** documented (2011-2024)
- **Repeatable local startup** after one-time dependency/build preparation

---

### Q13.3: What questions should we expect from judges?

**A:** The most common judge questions and best answers:

1. **"Why not use deep learning?"** → See Q2.2 (tabular data, small dataset, interpretability)
2. **"How accurate is the model?"** → The committed grouped evaluation reports its metrics on generated/derived prototype labels; no field-accuracy claim is made (see Q4.4).
3. **"Is the data real?"** → Mixed provenance: regional/public source material plus derived and realistically generated prototype rows; labels are not prospective field outcomes (see Q5.2).
4. **"What happens in low connectivity?"** → SQLite offline-first, cached satellite data (see Q11.2)
5. **"How do you handle false positives?"** → Intentional over-prediction for safety; 4-tier severity allows graduated response
6. **"Can this scale?"** → PostgreSQL + load balancing + MQTT pipeline (see Q10.2)
7. **"What about privacy?"** → Reports are voluntary, no PII stored beyond optional name/phone
8. **"Why 4 languages?"** → NER population: Hindi (mainstream), Bengali (Assam/Tripura), Assamese (Assam), English (official)

---

## 14. Rapid-Fire Questions

| # | Question | Answer |
|---|----------|--------|
| 1 | Total API endpoints? | **45** REST + 2 WebSocket |
| 2 | Database models? | **8** SQLAlchemy models |
| 3 | Frontend pages? | Multiple operational views for monitoring, maps, alerts, reports and administration |
| 4 | Translation languages? | **5** (EN, HI, BN, AS, OR) |
| 5 | Test count? | **128 backend tests** |
| 6 | Model accuracy? | **Prototype grouped metrics only; no field-accuracy claim** |
| 7 | Training samples? | **12,000 mixed-provenance prototype rows** |
| 8 | Sensor stations? | **20 seeded reference locations** across 8 NER states; real gateways are optional |
| 9 | Historical events? | **44** documented (2011-2024) |
| 10 | Monitored roads? | **48** with status tracking |
| 11 | Tracked villages? | **18** with population data |
| 12 | Risk levels? | **4** (Low, Moderate, High, Critical) |
| 13 | AI model type? | **VotingClassifier** (RF + GB ensemble) |
| 14 | Authentication? | **JWT** with bcrypt + RBAC |
| 15 | Rate limit? | **100 req/min** per IP |
| 16 | Cross-platform? | **Web + Android + Desktop** |
| 17 | Offline capable? | **Yes** — SQLite + cached data |
| 18 | Backend framework? | **FastAPI** (Python) |
| 19 | Frontend framework? | **React 19** (TypeScript) |
| 20 | CSS framework? | **Tailwind CSS** |
| 21 | Map library? | **Leaflet.js** (free OSM tiles) |
| 22 | Charts library? | **Recharts** |
| 23 | HTTP client? | **Axios** with interceptors |
| 24 | Mobile wrapper? | **Capacitor** |
| 25 | Desktop wrapper? | **Electron** |
| 26 | Server startup time? | **~20 seconds** (includes AI training) |
| 27 | Prediction latency? | **<1ms** per station |
| 28 | File upload support? | **Yes** — photo/video for reports |
| 29 | WebSocket support? | **Yes** — real-time alert broadcasting |
| 30 | Database migration tool? | **Alembic** |

---

## BONUS: Technical Diagrams for Presentation

### System Data Flow
```
IoT Sensors → REST API → FastAPI → AI Engine → Risk Score
     ↓              ↓          ↓          ↓           ↓
  Readings      Validation  Auth/RBAC  RF+GB     Alert Gen
     ↓              ↓          ↓          ↓           ↓
  SQLite ←──── Seed Data   JWT Auth   joblib    WebSocket → Dashboard
```

### AI Model Decision Tree (simplified)
```
           Input: [slope, elevation, aspect, rain, rain7d, ndvi, moisture, road_dist, month]
                              ↓
                    StandardScaler normalization
                              ↓
                 ┌─────────────┴─────────────┐
                 ↓                           ↓
         Random Forest               Gradient Boosting
         (200 trees)                 (150 trees)
         (40% weight)                (60% weight)
                 ↓                           ↓
                 └─────────────┬─────────────┘
                               ↓
                      Soft Voting (probability avg)
                               ↓
                    Risk Score: 0-100
                    Level: L / M / H / C
```

---

*Document prepared for SIH 2026 — GeoShield Team*
*Last updated: 2026-08-29*
