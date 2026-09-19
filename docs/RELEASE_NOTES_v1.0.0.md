# GeoShield v1.0.0

GeoShield v1.0.0 is the final-year major-project software freeze.

## Highlights

- persistent role-based authentication and administration;
- authenticated sensor/gateway telemetry ingestion with idempotency;
- ML risk inference, GIS monitoring and persistent alert workflows;
- citizen reporting with evidence and ownership isolation;
- real-time operational updates across dashboard/station/report views;
- PostgreSQL migrations and persistence verification;
- Docker and Windows offline operation;
- self-contained Electron Windows package + NSIS installer;
- Capacitor Android evaluation APK;
- integrity-checked database/evidence backup and destructive restore testing;
- browser E2E, security, PostgreSQL, Windows, Android, Electron and recovery CI gates.

## Release assets

- **Windows:** `GeoShield-v1.0.0-Setup.exe`
- **Android:** `GeoShield-v1.0.0-Android-Evaluation.apk`
- **Integrity:** `SHA256SUMS.txt`

## Important limitations

This is a research/academic software platform, not a certified field early
warning service. Real-world warning accuracy requires calibrated hardware,
prospective field data, independent validation and operational authority review.

The Windows installer is not commercially code-signed and the Android
evaluation APK is not Play Store production-signed.
