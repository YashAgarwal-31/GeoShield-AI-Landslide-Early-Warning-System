# GeoShield Build & Verification Guide

This guide reflects the post-Phase-4 stabilized repository. The **core verified
runtime** is the FastAPI + React web application, including Docker and the
repeatable offline presentation flow.

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

The stabilized suite contains **100 test functions**. GitHub Actions additionally
checks:

- `pip check` and Python compilation
- root Electron lockfile installation and JS syntax
- root and frontend npm security audits
- TypeScript + Vite production build
- all backend tests
- Docker image build
- production-mode container startup
- health, dashboard, station, prediction, and production-login smoke requests

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
| `WEATHER_LIVE_ENABLED` | Optional live weather adapter |
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

Android Studio, the Android SDK, and a compatible JDK are required. The normal
CI validates the shared TypeScript/Vite frontend, not a full APK build.

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

The current Electron wrapper starts the bundled backend source using a compatible
**system Python environment with GeoShield backend dependencies installed**.
It is therefore an optional wrapper, not a self-contained Python runtime. For
the most reproducible major-project demonstration, use `start-offline.bat` or
Docker.

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
