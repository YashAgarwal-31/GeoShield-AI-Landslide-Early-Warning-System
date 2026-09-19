# GeoShield Build & Verification Guide

This guide reflects GeoShield v1.2.0. The FastAPI + React runtime, Docker,
Android, Windows Electron, Linux Electron, and unsigned iOS Simulator build are
covered by CI verification gates.

## Prerequisites

| Tool | Recommended | Purpose |
|---|---:|---|
| Python | 3.12 | Backend, ML, tests |
| Node.js | 22 | Frontend and Electron tooling |
| npm | bundled with Node | Locked JS installs |
| Git | current | Source control |
| Docker | current | Production-equivalent verification |

## Windows presentation workflow

Run once while internet is available:

```bat
prepare-demo.bat
```

This creates `backend\venv`, installs Python dependencies, performs a locked
frontend install with `npm ci`, builds the production frontend, runs the full
backend suite, and checks the cached data required for the demo.

On presentation day:

```bat
start-offline.bat
```

Open `http://127.0.0.1:8000`. The launcher binds only to localhost, disables
live weather and model retraining, and uses cached/fallback data for the core
flow.

## Linux/macOS local setup

```bash
python3 -m venv backend/venv
backend/venv/bin/python -m pip install --upgrade pip
backend/venv/bin/python -m pip install -r backend/requirements.txt pytest

cd frontend
npm ci
npm run build
cd ..

./start.sh
```

The safe default address is `http://127.0.0.1:8000`.

## Manual development mode

Backend:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt pytest
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend in another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Vite runs on `http://localhost:5173` and proxies API requests to the local
backend.

## Full verification

```bash
cd backend
python -m pytest tests -q
```

GitHub Actions runs the complete backend suite and additionally checks:

- `pip check` and Python compilation
- root Electron lockfile installation and JS syntax
- root and frontend npm security audits
- TypeScript + Vite production build
- all backend tests
- Docker image build
- production-mode container startup
- health, dashboard, station, prediction, and production-login smoke requests
- browser end-to-end report workflow
- PostgreSQL persistence and disaster recovery
- Android Gradle APK build
- Windows Electron installer/runtime smoke tests
- Linux Electron AppImage packaging
- iOS Simulator native build

## Docker

Local demo:

```bash
docker compose up --build
```

Docker Compose binds the service to `127.0.0.1:8000`.

For a production-profile container, provide a strong JWT secret and a
secret-managed administrator:

```bash
docker build -t geoshield .

docker run --rm -p 127.0.0.1:8000:8000 \
  -e APP_ENV=production \
  -e JWT_SECRET="<32+ random characters>" \
  -e ENABLE_DEMO_USERS=false \
  -e GEOSHIELD_ADMIN_EMAIL="admin@example.com" \
  -e GEOSHIELD_ADMIN_PASSWORD="<12+ character secret>" \
  geoshield
```

Do not commit production passwords or JWT secrets.

## Runtime configuration

Important variables are documented in `.env.example`.

| Variable | Purpose |
|---|---|
| `APP_ENV` | `demo` or `production` |
| `JWT_SECRET` | JWT signing key; mandatory and >=32 chars in production |
| `ENABLE_DEMO_USERS` | Enables built-in local demo accounts |
| `GEOSHIELD_ADMIN_EMAIL` | Secret-managed production admin login |
| `GEOSHIELD_ADMIN_PASSWORD` | Production admin password; >=12 chars |
| `DATABASE_URL` | SQLite by default; can point to another SQLAlchemy DB |
| `WEATHER_LIVE_ENABLED` | Open-Meteo weather fallback adapter |
| `IMD_LIVE_ENABLED` | Prefer official IMD observations when reachable |
| `SRTM_LIVE_ENABLED` | On-demand SRTM elevation/slope |
| `SENTINEL2_LIVE_ENABLED` | On-demand Sentinel-2 L2A NDVI |
| `FLOOD_LIVE_ENABLED` | Live GloFAS river discharge |
| `SMS_NOTIFICATIONS_ENABLED` | Twilio SMS switch; requires credentials/recipients |
| `PUSH_NOTIFICATIONS_ENABLED` | ntfy push switch; requires a topic |
| `WEB_PUSH_ENABLED` | Standards-based VAPID browser/PWA push switch |
| `VAPID_PUBLIC_KEY` | Base64URL P-256 application server public key |
| `VAPID_PRIVATE_KEY` | Secret Base64URL 32-byte P-256 private scalar; never commit |
| `VAPID_SUBJECT` | VAPID contact identity, normally `mailto:...` |
| `MODEL_TRAINING_ENABLED` | Explicit admin maintenance switch |
| `TRUST_PROXY_HEADERS` | Trust forwarded client IP only behind a trusted proxy |
| `MODEL_CACHE_DIR` | Writable model cache location for packaged runtimes |

## Android wrapper

The Android wrapper uses the bundled frontend. It **does not bundle the Python
backend**; configure a reachable backend URL from the login/settings screen.

Because generated Android platform files are intentionally not committed, a
fresh checkout should run:

```bash
cd frontend
npm ci
npm run build
npx cap add android
npx cap sync android
cd android
./gradlew assembleDebug
```

Android Studio, the Android SDK, and a compatible JDK are required for local native development. CI generates the Capacitor Android project and builds/verifies the debug APK.

## iOS wrapper

The iOS client uses Capacitor and the same frontend/backend API contract. CI
generates the native project and performs an unsigned iOS Simulator build.
Physical-device/App Store builds require the maintainer's Apple Developer
signing certificate and provisioning profile; those credentials stay outside
the repository.

## Electron desktop wrapper

Build configuration and JavaScript syntax are CI-checked, and packaged resource
paths use writable user-data locations for SQLite/model caches.

```bash
npm ci
cd frontend && npm ci && npm run build && cd ..
npm run build:linux
# or on Windows:
npm run build:win
```

Windows release builds bundle the Python backend runtime. Linux AppImage builds prepare and bundle a Python runtime under `resources/runtime/python`. Developer mode can still fall back to the system Python interpreter.

## Local demo accounts

Built-in credentials are enabled only when `ENABLE_DEMO_USERS=true`.

| Email | Password | Role |
|---|---|---|
| admin@geoshield.gov.in | admin123 | Admin |
| field@geoshield.gov.in | field123 | Field Officer |
| district@geoshield.gov.in | district123 | District Admin |
| citizen@geoshield.gov.in | demo123 | Citizen |

Do not expose these demo credentials on a public production deployment.

---

See [PHASE4_GUIDE.md](PHASE4_GUIDE.md) for the presentation sequence and viva
preparation.


## ACT emergency communication setup

Demo/development mode auto-generates a persistent local VAPID keypair on first
use, making browser Web Push immediately testable on localhost.

For production, generate a Web Push VAPID key pair locally:

```bash
cd backend
python ../tools/generate_vapid_keys.py
```

Copy the generated values into your deployment secrets, set a real
`VAPID_SUBJECT`, and enable `WEB_PUSH_ENABLED=true`. After login, use
**Enable Emergency Push** in the GeoShield settings panel to register the device.

For SMS, configure `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`,
`TWILIO_FROM_NUMBER`, and `ALERT_SMS_RECIPIENTS`, then set
`SMS_NOTIFICATIONS_ENABLED=true`. District-specific routing is supported with
variables such as `ALERT_SMS_RECIPIENTS_EAST_KHASI_HILLS`.

Admin and district-admin users can validate both channels from the
**Emergency Communication Center**. See [docs/COMMUNICATIONS.md](docs/COMMUNICATIONS.md).
