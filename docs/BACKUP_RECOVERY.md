# GeoShield Backup & Disaster Recovery

GeoShield backups cover the operational database and citizen-report evidence files.
The archive contains a versioned manifest and SHA-256 checksum for every payload file.

## Create and validate a backup

Run from the `backend` directory with the same `DATABASE_URL` and
`REPORT_UPLOAD_DIR` used by the application:

```bash
python scripts/backup_restore.py backup ../backups/geoshield-backup.zip
python scripts/backup_restore.py inspect ../backups/geoshield-backup.zip
```

SQLite is copied using SQLite's online backup API. PostgreSQL uses a custom
`pg_dump` archive, so PostgreSQL client tools must be installed.

## Restore

Stop GeoShield before restore. Restore is intentionally destructive and requires
an explicit flag:

```bash
python scripts/backup_restore.py restore ../backups/geoshield-backup.zip --force
```

For PostgreSQL, `pg_restore --clean --if-exists` recreates the backed-up
database objects. Evidence uploads are replaced from the verified archive.
After restore, start GeoShield and check `/api/health/ready`, authentication,
station inventory, citizen reports, and evidence retrieval.

## Recovery policy

Keep at least one backup outside the application host, protect backup files as
sensitive operational data, periodically test restoration, and never treat a
backup as valid solely because archive creation succeeded. CI performs a
destructive recovery drill against a temporary PostgreSQL database.
