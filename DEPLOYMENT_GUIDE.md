# GeoShield Deployment Guide

The Docker image is the preferred production-equivalent deployment path because
the same image is built and boot-smoke-tested in GitHub Actions.

> GeoShield remains a research/demo prototype, not a certified public-warning
> service.

## 1. Local/offline presentation

Windows:

```bat
prepare-demo.bat
start-offline.bat
```

Open `http://127.0.0.1:8000`.

Linux/macOS after installing dependencies and building the frontend:

```bash
./start.sh
```

The normal local launcher binds to localhost, enables keyless live weather with
automatic fallback, and keeps model retraining off. `start-offline.bat` disables
live weather for a deterministic no-network demonstration.

## 2. Docker

```bash
docker build -t geoshield .
```

Production profile:

```bash
docker run --rm -p 127.0.0.1:8000:8000 \
  -e APP_ENV=production \
  -e JWT_SECRET="<32+ random characters>" \
  -e ENABLE_DEMO_USERS=false \
  -e GEOSHIELD_ADMIN_EMAIL="admin@example.com" \
  -e GEOSHIELD_ADMIN_PASSWORD="<12+ character secret>" \
  geoshield
```

The CI pipeline verifies that the production container starts and that health,
dashboard, station, prediction, and configured-admin login flows respond.

## 3. Render

The repository includes `render.yaml` and uses the hardened Dockerfile.

1. Create a Render Blueprint from
   `YashAgarwal-31/GeoShield-AI-Landslide-Early-Warning-System`.
2. Render generates `JWT_SECRET`.
3. The Blueprint prompts for `GEOSHIELD_ADMIN_PASSWORD`; do not commit it.
4. `GEOSHIELD_ADMIN_EMAIL` defaults to `admin@geoshield.local` in the
   Blueprint and can be changed in the Render dashboard.
5. Wait for `/api/health` to become healthy.
6. Open the service URL and log in using the configured production admin.

Built-in demo credentials remain disabled on this production profile.

## 4. Railway

The repository's `railway.json` selects the root Dockerfile.

Create a project from the same GitHub repository and configure these variables in
Railway before exposing the service:

```text
APP_ENV=production
JWT_SECRET=<32+ random characters>
ENABLE_DEMO_USERS=false
GEOSHIELD_ADMIN_EMAIL=<your admin email>
GEOSHIELD_ADMIN_PASSWORD=<12+ character secret>
WEATHER_LIVE_ENABLED=true
MODEL_TRAINING_ENABLED=false
TRUST_PROXY_HEADERS=true
```

Railway should use the Dockerfile build defined by `railway.json`; do not use
the old Nixpacks/manual frontend build commands.

## Verification after deployment

Check:

```text
GET /api/health
GET /api/dashboard/stats
GET /api/sensors/stations
POST /api/predict
POST /api/auth/login
```

Then verify through the UI:

1. Production admin can log in.
2. Dashboard loads.
3. Map/prediction flow works.
4. Stations and alerts pages load.
5. No page presents cached/demo data as live sensor data.
6. Privileged simulator/admin actions require authorization.

## Security notes

- Never deploy with the repository's demo passwords on a public endpoint.
- Never commit `JWT_SECRET` or production administrator passwords.
- Leave `MODEL_TRAINING_ENABLED=false` during normal operation.
- Enable `TRUST_PROXY_HEADERS` only behind a trusted platform proxy.
- Keep external-data source/freshness labels visible to users.

## Recommended viva/demo setup

For an academic presentation, the offline local path is more deterministic than
depending on venue internet. Prepare once with `prepare-demo.bat`, test with
Wi-Fi disconnected, and keep public deployment only as an optional secondary
demo.
