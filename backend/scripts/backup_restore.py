#!/usr/bin/env python3
"""Create and restore integrity-checked GeoShield operational backups.

The command is intended to run while the application is stopped for restore.
Backups include the configured database plus citizen-report evidence files.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import zipfile

from sqlalchemy.engine import make_url


FORMAT_VERSION = 1


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite:///./geoshield.db").strip()


def _upload_dir() -> Path:
    configured = os.getenv("REPORT_UPLOAD_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(__file__).resolve().parents[1] / "app" / "uploads" / "reports").resolve()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"Command failed ({completed.returncode}): {' '.join(command[:2])}")


def _db_kind(url: str) -> str:
    driver = make_url(url).drivername
    if driver.startswith("sqlite"):
        return "sqlite"
    if driver.startswith("postgresql"):
        return "postgresql"
    raise SystemExit(f"Unsupported database backend for recovery: {driver}")


def _postgres_cli_url(url: str) -> str:
    parsed = make_url(url)
    return parsed.set(drivername="postgresql").render_as_string(hide_password=False)


def _sqlite_path(url: str) -> Path:
    parsed = make_url(url)
    if not parsed.database:
        raise SystemExit("SQLite DATABASE_URL does not contain a database path.")
    path = Path(parsed.database)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def _copy_uploads(destination: Path) -> None:
    source = _upload_dir()
    if source.exists():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        destination.mkdir(parents=True, exist_ok=True)


def backup(output: Path) -> None:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    db_url = _database_url()
    db_kind = _db_kind(db_url)

    with tempfile.TemporaryDirectory(prefix="geoshield-backup-") as tmp:
        root = Path(tmp)
        payload = root / "payload"
        payload.mkdir()

        if db_kind == "sqlite":
            source = _sqlite_path(db_url)
            if not source.exists():
                raise SystemExit(f"SQLite database does not exist: {source}")
            target = payload / "database.sqlite3"
            source_conn = sqlite3.connect(str(source))
            try:
                target_conn = sqlite3.connect(str(target))
                try:
                    source_conn.backup(target_conn)
                finally:
                    target_conn.close()
            finally:
                source_conn.close()
        else:
            target = payload / "database.dump"
            _run([
                "pg_dump",
                "--format=custom",
                "--no-owner",
                "--no-privileges",
                "--file",
                str(target),
                "--dbname",
                _postgres_cli_url(db_url),
            ])

        _copy_uploads(payload / "reports")

        checksums = {}
        for path in sorted(payload.rglob("*")):
            if path.is_file():
                checksums[path.relative_to(root).as_posix()] = _sha256(path)

        manifest = {
            "format_version": FORMAT_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database_kind": db_kind,
            "files": checksums,
        }
        (root / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(root / "manifest.json", "manifest.json")
            for path in sorted(payload.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root).as_posix())

    print(f"GeoShield backup created: {output}")


def _safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if root != target and root not in target.parents:
            raise SystemExit(f"Unsafe backup member path: {member.filename}")
    archive.extractall(destination)


def _validate(root: Path) -> dict:
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit("Backup manifest is missing.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format_version") != FORMAT_VERSION:
        raise SystemExit("Unsupported GeoShield backup format version.")

    files = manifest.get("files") or {}
    for relative, expected in files.items():
        path = (root / relative).resolve()
        if not path.is_file():
            raise SystemExit(f"Backup payload is missing: {relative}")
        actual = _sha256(path)
        if actual != expected:
            raise SystemExit(f"Backup integrity check failed: {relative}")
    return manifest


def restore(archive_path: Path, force: bool) -> None:
    if not force:
        raise SystemExit("Restore is destructive. Re-run with --force after stopping GeoShield.")

    archive_path = archive_path.expanduser().resolve()
    if not archive_path.is_file():
        raise SystemExit(f"Backup archive does not exist: {archive_path}")

    db_url = _database_url()
    current_kind = _db_kind(db_url)

    with tempfile.TemporaryDirectory(prefix="geoshield-restore-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(archive_path, "r") as archive:
            _safe_extract(archive, root)
        manifest = _validate(root)

        if manifest.get("database_kind") != current_kind:
            raise SystemExit(
                f"Backup database kind {manifest.get('database_kind')} does not match "
                f"configured database kind {current_kind}."
            )

        payload = root / "payload"
        if current_kind == "sqlite":
            source = payload / "database.sqlite3"
            destination = _sqlite_path(db_url)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + ".restore")
            shutil.copy2(source, temporary)
            temporary.replace(destination)
        else:
            _run([
                "pg_restore",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
                "--dbname",
                _postgres_cli_url(db_url),
                str(payload / "database.dump"),
            ])

        uploads = _upload_dir()
        restored_uploads = payload / "reports"
        if uploads.exists():
            shutil.rmtree(uploads)
        uploads.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(restored_uploads, uploads, dirs_exist_ok=True)

    print(f"GeoShield restore completed from: {archive_path}")


def inspect(archive_path: Path) -> None:
    archive_path = archive_path.expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="geoshield-inspect-") as tmp:
        root = Path(tmp)
        with zipfile.ZipFile(archive_path, "r") as archive:
            _safe_extract(archive, root)
        manifest = _validate(root)
    print(json.dumps(manifest, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="GeoShield backup and disaster recovery")
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser("backup", help="Create an integrity-checked backup")
    backup_parser.add_argument("output", type=Path)

    restore_parser = subparsers.add_parser("restore", help="Restore a backup")
    restore_parser.add_argument("archive", type=Path)
    restore_parser.add_argument("--force", action="store_true")

    inspect_parser = subparsers.add_parser("inspect", help="Validate and inspect a backup")
    inspect_parser.add_argument("archive", type=Path)

    args = parser.parse_args()
    if args.command == "backup":
        backup(args.output)
    elif args.command == "restore":
        restore(args.archive, args.force)
    else:
        inspect(args.archive)


if __name__ == "__main__":
    main()
