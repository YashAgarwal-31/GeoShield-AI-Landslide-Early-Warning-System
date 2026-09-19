# GeoShield Implementation Status

**Release target:** v1.0.0  
**Status:** final-year major-project software baseline frozen after end-to-end
operational verification.

## Current implementation

| Layer | Implementation | Status |
|---|---|---|
| Web UI | React, TypeScript, Vite, Tailwind, Leaflet, Recharts | Verified |
| API | FastAPI + Uvicorn | Verified |
| Persistence | SQLAlchemy, SQLite, PostgreSQL, Alembic | Verified |
| Authentication | JWT RBAC + persistent users + revocation | Verified |
| Sensor ingestion | API-key authenticated gateway endpoint + idempotency | Verified |
| ML | Terrain/rainfall/sensor risk inference and evaluation tooling | Functional research prototype |
| Real-time | Authenticated WebSockets + polling fallbacks | Verified |
| Citizen reports | Ownership scoping + evidence + staff workflow | Verified |
| Desktop | Electron + bundled Python backend + NSIS installer | Verified on Windows CI |
| Android | Capacitor debug/evaluation APK | Verified build + transport policy |
| Docker | Production-style image/runtime smoke | Verified |
| Backup/recovery | DB + evidence archive with SHA-256 validation | Verified destructive restore drill |
| Security gates | pip-audit, Bandit, npm audits, RBAC regressions | Passing at freeze |

## Final CI gates

The frozen project requires all of these jobs to remain green:

1. `verify`
2. `postgres-integration`
3. `browser-e2e`
4. `security`
5. `windows-verification`
6. `android-build`
7. `electron-windows`
8. `disaster-recovery`

## Field-validation boundary

The software platform is operational, but the following claims are deliberately
not made:

- certified landslide prediction accuracy;
- guaranteed warnings in field conditions;
- government production approval;
- calibrated hardware performance;
- independent prospective validation.

Physical deployment would require sensor calibration, field trials, operational
SOPs, disaster-management review and independent model validation.

## Freeze policy

v1.0.0 is the academic baseline. New functionality should not be added to the
frozen release solely for presentation value. Future work belongs on a later
version/branch and should preserve the v1.0.0 tag as the reproducible baseline.
