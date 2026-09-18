# GeoShield Phase 4 Guide

## Security, deployment, offline demo, presentation and viva

Phase 4 converts the Phase 3 research demonstrator into a safer, repeatable major-project build. GeoShield is still a **research/demo prototype**, not a certified operational public-warning system.

## 1. Security and configuration hardening

The runtime now distinguishes between local/demo use and production deployment.

### Demo profile

Use:

```text
APP_ENV=demo
WEATHER_LIVE_ENABLED=false
MODEL_TRAINING_ENABLED=false
TRUST_PROXY_HEADERS=false
```

This profile is intended for localhost presentation and testing.

### Production profile

Use:

```text
APP_ENV=production
JWT_SECRET=<random secret of at least 32 characters>
ENABLE_DEMO_USERS=false
WEATHER_LIVE_ENABLED=false
MODEL_TRAINING_ENABLED=false
```

Production startup fails closed if the JWT secret is missing or too short.

### Hardening completed

- Wildcard CORS was removed; allowed origins are explicit.
- Security headers are added to HTTP responses.
- Authentication responses use no-store caching.
- Forwarded client-IP headers are trusted only when explicitly enabled.
- Model retraining requires admin authorization and an explicit feature flag.
- Caller-supplied training files are constrained to the configured dataset directory.
- Citizen accounts cannot trigger simulation mutations.
- Simulator inputs and batch size are validated.
- Simulator alerts are clearly marked as simulation data.
- Simulator reset removes simulator-labelled alerts/assessments rather than wiping all alerts.
- Static-file containment uses a path-safe common-path check.
- CI verifies tests, dependency consistency, frontend audit/build and Docker build.

## 2. Deployment verification

### Docker

The Dockerfile uses a multi-stage build:

1. Node 22 builder installs frontend dependencies using `npm ci`.
2. The React/Vite production build is created.
3. Python 3.12 runtime installs backend dependencies.
4. Runtime files are owned by an unprivileged `geoshield` user.
5. The application runs as non-root.
6. A health check calls `/api/health`.

### Local Docker Compose

Run:

```bash
docker compose up --build
```

The service binds to:

```text
127.0.0.1:8000
```

so the demo server is not accidentally exposed to the local network.

### Render

The Render definition uses the hardened Docker image, production mode, an automatically generated JWT secret, demo users disabled, model retraining disabled and live weather disabled by default.

## 3. Repeatable offline demo

### One-time preparation

While internet is available, run:

```bat
prepare-demo.bat
```

It creates the Python environment, installs locked frontend dependencies, builds the frontend, runs the backend suite and checks required cached data.

### Presentation-day start

After preparation, internet is not required for the normal demonstration flow.

Run:

```bat
start-offline.bat
```

Then open:

```text
http://127.0.0.1:8000
```

The launcher disables live weather and model retraining and binds the server to localhost. Cached/fallback data remains visibly labelled by source/freshness in the application.

## 4. Recommended presentation flow

### Slide/demo 1 — Problem and scope

Explain that the North Eastern Region is landslide-prone and that GeoShield explores how multi-source monitoring, ML risk scoring, GIS visualization and warning workflows can be brought into one prototype.

State clearly:

> The current project is a software research demonstrator. It uses historical, cached, seeded and generated inputs; it is not connected to a certified live sensor network.

### Slide/demo 2 — Architecture

Explain the three layers:

- React + TypeScript presentation layer
- FastAPI business/API layer
- SQLite + datasets + optional external-data adapters

Then explain the ML layer: baseline ensemble risk predictor plus enhanced terrain-aware model.

### Slide/demo 3 — Dashboard

Show total stations, risk distribution, alert counts and rainfall/risk trends. Explain that the 20 stations are seeded NER monitoring profiles used to exercise the complete workflow.

### Slide/demo 4 — GIS risk map

Click/select a location and show the generated risk assessment. Explain:

- coordinates
- nearest terrain/station context
- slope/elevation/vegetation or moisture-related features
- risk score and risk level
- contributing factors

### Slide/demo 5 — Station detail and data provenance

Show a station page and point to source/freshness metadata. This is important because Phase 3 deliberately distinguishes live, cached, fallback, stale and unavailable data.

### Slide/demo 6 — Controlled simulation

Log in using the local demo account and trigger a high or critical scenario. Show:

1. sensor values change
2. predictor runs
3. risk assessment is stored
4. simulation-labelled alert is created

Emphasize that this is a **controlled simulation**, not a real emergency event.

### Slide/demo 7 — Alerts and workflow

Show the alert. Explain RBAC:

- operational roles can run controlled simulations
- staff can acknowledge alerts
- admin can resolve alerts
- citizen cannot perform privileged mutation actions

### Slide/demo 8 — Offline reliability and security

Disconnect internet before the demo if desired. Show that the app still loads using the prebuilt frontend and cached/fallback datasets.

Mention:

- localhost-only demo launcher
- live weather disabled
- production JWT requirement
- explicit CORS
- non-root Docker runtime
- CI regression tests

## 5. 90-second project pitch

GeoShield is an AI-based landslide risk monitoring and early-warning research prototype for India's North Eastern Region. The system combines terrain and environmental features, seeded monitoring-station data, historical/cached datasets and optional weather adapters to estimate landslide risk. A FastAPI backend exposes prediction, monitoring, alert, GIS and reporting workflows, while a React interface visualizes risk geographically and operationally. The ML layer includes an ensemble risk predictor and an enhanced terrain-aware model. The main engineering focus of the later development phases was not only adding features but making the project scientifically and operationally more defensible: data provenance is visible, grouped model evaluation is reproducible, external data gracefully falls back to cached sources, unsafe production defaults are removed, privileged mutations use role controls, CI verifies the build, and an offline presentation mode makes the demo repeatable. The current system is a software demonstrator rather than a certified warning platform; real field deployment would require calibrated physical sensors, prospective validation, operational thresholds and authority integration.

## 6. Viva questions and answers

### Q1. What is the main objective of GeoShield?

To demonstrate an integrated software platform that estimates landslide risk from terrain/environmental inputs, visualizes risk on GIS maps, manages warning workflows and supports decision-making in a landslide-prone region.

### Q2. Why did you select the North Eastern Region?

The region combines steep terrain, high monsoon rainfall, geological instability and difficult connectivity. These characteristics make landslide-risk monitoring a meaningful communication-and-AI problem.

### Q3. Is your system actually connected to physical sensors?

No. The current major-project build is software-based. It uses seeded station profiles, historical/cached information and generated/simulated readings. Physical IoT sensors are a future deployment step.

### Q4. Then why do you call it an early-warning system?

The prototype implements the software pipeline required for an early-warning workflow: ingest observations, estimate risk, classify severity, create alerts and visualize affected areas. Operational early warning would require field sensors and validation before real-world use.

### Q5. What ML algorithms are used?

The project contains a baseline ensemble using Random Forest and Gradient Boosting through soft voting, plus an enhanced terrain-aware prediction path using XGBoost when the trained model is available.

### Q6. Why use an ensemble?

Different tree-based models capture different nonlinear relationships. Combining them can reduce reliance on a single estimator and provide a stronger experimental baseline, but performance must still be evaluated on independent groups/data.

### Q7. What are important landslide features?

Typical project features include rainfall, soil moisture, slope, elevation, vegetation/NDVI, ground displacement, tilt and pore-water-pressure-related measurements.

### Q8. Why is rainfall important?

Prolonged or intense rainfall raises soil saturation and pore-water pressure and can reduce effective soil strength, increasing slope-instability risk.

### Q9. Why is slope important?

Steeper slopes increase the downslope component of gravitational force. Slope is therefore an important susceptibility feature, although it is not sufficient by itself.

### Q10. What is the difference between susceptibility and real-time risk?

Susceptibility describes how inherently prone an area is based on relatively static conditions such as slope and terrain. Real-time or dynamic risk incorporates changing triggers such as rainfall, moisture and displacement.

### Q11. How did you avoid data leakage in evaluation?

Phase 2 added grouped evaluation so related samples from the same geographic grouping are kept together rather than being randomly split across training and test sets. This gives a more realistic estimate than a naive row-level random split.

### Q12. Why is accuracy alone not sufficient?

For imbalanced hazard data, a model can report high accuracy while missing rare dangerous cases. Precision, recall, F1, confusion matrices and class-wise behavior are more informative.

### Q13. What does the source-status badge mean?

It tells the user whether external information is live, cached, fallback, stale or unavailable. This prevents the UI from presenting old or generated data as live observations.

### Q14. How does the system work without internet?

The React frontend is built beforehand, FastAPI serves it locally, weather live mode is disabled, and cached/fallback datasets are used. The presentation launcher binds to localhost and does not require network calls for the core flow.

### Q15. What happens if the external weather API fails?

The adapter has timeout/cache/fallback behavior. The application continues with the available cached or demonstration source and exposes the source state rather than silently pretending the data is live.

### Q16. What authentication is used?

JWT bearer authentication. Local demo identities are provided for presentation. In production mode, a strong environment-provided JWT secret is mandatory and demo users are disabled by default.

### Q17. What is RBAC?

Role-Based Access Control. It restricts actions according to roles such as admin, field officer, district admin and citizen.

### Q18. What security issues were hardened in Phase 4?

Production secret enforcement, explicit CORS, safer proxy handling, security headers, restricted model retraining, simulation authorization, safer simulator reset behavior, validated inputs, path containment and non-root container execution.

### Q19. Why restrict model retraining?

Retraining changes a security- and safety-relevant system artifact and can consume significant resources. It should be a controlled administrative maintenance action, not an anonymous API operation.

### Q20. What was wrong with trusting X-Forwarded-For automatically?

A direct client can spoof that header unless a trusted proxy overwrites it. Trusting it blindly can undermine per-IP rate limiting.

### Q21. Why is Docker useful here?

It creates a repeatable runtime with explicit Python/Node versions, dependencies, application files and health checks, reducing "works on my machine" differences.

### Q22. Why run the container as non-root?

If the application is compromised, a non-root process has fewer privileges inside the container, reducing potential impact.

### Q23. Why use SQLite?

For a single-machine research/demo application SQLite offers zero-configuration persistence and is easy to reproduce. A production multi-instance deployment would typically move to a managed relational database such as PostgreSQL.

### Q24. Why FastAPI?

It provides strong request validation through Pydantic, automatic OpenAPI documentation, async-capable APIs and concise Python integration with the ML layer.

### Q25. Why React?

It supports an interactive single-page interface for maps, charts, alert workflows and reusable components.

### Q26. What does the simulator prove?

It proves the end-to-end software workflow under controlled conditions: input spike, model evaluation, database persistence and alert creation. It does not prove real-world forecasting accuracy.

### Q27. What is the biggest current limitation?

The lack of prospectively collected, calibrated live field-sensor data and external independent validation. This limits claims about operational prediction accuracy and warning lead time.

### Q28. What would you do next?

Deploy calibrated rainfall, soil-moisture, inclinometer/displacement and pore-pressure sensors; add robust communication such as LoRaWAN/cellular gateways; collect prospective data; calibrate thresholds; validate geographically; integrate official GIS/weather feeds; and conduct pilot testing with disaster-management stakeholders.

### Q29. Where is the communication-engineering component?

It appears in the monitoring/alert architecture and future sensor-to-gateway communication design. A field version can combine low-power local sensor links, gateway aggregation and cellular/Internet backhaul, with edge buffering when connectivity is intermittent.

### Q30. How would you handle network failure in a real deployment?

Use local buffering at the gateway, store-and-forward transmission, retry/backoff, timestamped measurements, local threshold alarms for critical cases and multiple communication paths where feasible.

### Q31. Can the model directly order evacuation?

No. The prototype produces decision-support risk indicators and workflow alerts. Evacuation decisions should remain with authorized disaster-management authorities operating validated procedures.

### Q32. How do you distinguish your contribution from existing/open-source material?

The repository retains required provenance/attribution documentation. The major-project development phases add auditing, corrected claims, reproducible evaluation, resilient data adapters, security/deployment hardening, regression tests and a repeatable offline demo.

## 7. Faculty-safe claims

Good claims:

- "The backend/frontend workflow is automated and tested."
- "The model evaluation is reproducible on the included project dataset."
- "External-data states are exposed transparently."
- "The demonstration can run offline after one-time preparation."
- "The simulator validates the end-to-end software workflow."

Avoid claims such as:

- "This system predicts every landslide."
- "The model is field-proven."
- "The application protects a specific number of people."
- "The application guarantees a fixed warning lead time."
- "The seeded station readings are live physical sensors."

## 8. Final presentation checklist

Before leaving for the viva:

- Run `prepare-demo.bat` with internet.
- Confirm the test suite finishes successfully.
- Run `start-offline.bat`.
- Open all main pages once.
- Trigger one high/critical simulation.
- Confirm a simulation-labelled alert appears.
- Restart the app and confirm it still launches.
- Disconnect Wi-Fi and repeat the core demo.
- Keep the repository and this guide locally available.
- Do not change dependencies or retrain the model immediately before presentation.
