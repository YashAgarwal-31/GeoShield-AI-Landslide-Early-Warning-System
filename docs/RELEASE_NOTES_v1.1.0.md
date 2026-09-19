# GeoShield v1.1.0 — Live Integrations & Platform Completion

GeoShield v1.1.0 completes the Phase 7 integration pass and turns previously
partial or missing capabilities into executable, source-labelled code paths.

## Added

- Live SRTM elevation and local-slope sampling with bounded cache/fallback.
- Recent Sentinel-2 L2A NDVI point sampling through STAC + COG assets.
- Official IMD current-weather and district-data adapters with resilient fallback.
- Live GloFAS river-discharge context in the flood module.
- Twilio SMS and ntfy push adapters plus opt-in browser notifications.
- Offline application shell, cached GET responses, and IndexedDB report queue/sync.
- District-admin operations portal with role-appropriate station controls.
- GeoJSON and CSV downloads in the GIS map.
- Live remote-sensing refresh controls in the Satellite page.
- Linux Electron packaging with bundled Python runtime.
- Capacitor iOS generation and unsigned iOS Simulator build verification.
- Phase 7 integration regression tests and updated provenance documentation.

## Verification

CI covers backend tests, frontend build/audit, Docker runtime smoke tests,
browser E2E, PostgreSQL persistence, disaster recovery, Android APK build,
Windows Electron runtime/installer, Linux Electron packaging, iOS Simulator
build, and dependency/static security audits.

## External activation requirements

These capabilities are implemented, but deployment-specific credentials or
hardware are intentionally not committed:

- Twilio SMS requires account credentials, a sender number, and recipients.
- ntfy push requires a topic and optionally an access token.
- Some IMD products may require the deployment public IP to be whitelisted.
- Physical IoT use requires a real sensor/gateway configured with the server URL
  and SENSOR_INGEST_API_KEY.
- A signed physical-device/App Store iOS build requires the maintainer's Apple
  Developer signing certificate and provisioning profile.

All third-party integrations fail soft so provider outages do not break the core
GeoShield runtime.
