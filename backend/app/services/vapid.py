"""VAPID key management for GeoShield Web Push.

Production deployments should provide VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY as
secrets. Demo/development mode can generate a persistent local keypair on first
use so Web Push works without a third-party account.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric import ec


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _runtime_file() -> Path:
    configured = os.getenv("VAPID_KEY_FILE", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()

    state_root = (
        os.getenv("MODEL_CACHE_DIR", "").strip()
        or os.getenv("GEOSHIELD_STATE_DIR", "").strip()
    )
    if state_root:
        return Path(state_root).expanduser().resolve() / "vapid-keys.json"

    return (Path.cwd() / ".geoshield-runtime" / "vapid-keys.json").resolve()


def _generate_pair() -> tuple[str, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_raw = private_key.private_numbers().private_value.to_bytes(32, "big")
    public_numbers = private_key.public_key().public_numbers()
    public_raw = (
        b"\x04"
        + public_numbers.x.to_bytes(32, "big")
        + public_numbers.y.to_bytes(32, "big")
    )
    return _b64url(public_raw), _b64url(private_raw)


def get_vapid_config() -> dict[str, Any]:
    app_env = os.getenv("APP_ENV", "demo").strip().lower()
    production = app_env in {"prod", "production"}

    public_key = os.getenv("VAPID_PUBLIC_KEY", "").strip()
    private_key = os.getenv("VAPID_PRIVATE_KEY", "").strip()
    subject = os.getenv(
        "VAPID_SUBJECT",
        "mailto:admin@geoshield.local" if not production else "",
    ).strip()

    # If deployment secrets are provided, the explicit enable switch defaults
    # to true. If no secrets exist, only demo/development may auto-provision.
    if public_key and private_key and subject:
        enabled = _env_bool("WEB_PUSH_ENABLED", True)
        return {
            "enabled": enabled,
            "configured": enabled,
            "public_key": public_key,
            "private_key": private_key,
            "subject": subject,
            "source": "environment",
        }

    if production:
        return {
            "enabled": _env_bool("WEB_PUSH_ENABLED", False),
            "configured": False,
            "public_key": public_key,
            "private_key": private_key,
            "subject": subject,
            "source": "missing_production_secrets",
        }

    if not _env_bool("WEB_PUSH_ENABLED", True):
        return {
            "enabled": False,
            "configured": False,
            "public_key": "",
            "private_key": "",
            "subject": subject,
            "source": "disabled",
        }

    key_file = _runtime_file()
    try:
        if key_file.is_file():
            saved = json.loads(key_file.read_text(encoding="utf-8"))
            saved_public = str(saved.get("public_key") or "").strip()
            saved_private = str(saved.get("private_key") or "").strip()
            if saved_public and saved_private:
                return {
                    "enabled": True,
                    "configured": True,
                    "public_key": saved_public,
                    "private_key": saved_private,
                    "subject": subject,
                    "source": "generated_local",
                }

        public_key, private_key = _generate_pair()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(
            json.dumps(
                {"public_key": public_key, "private_key": private_key},
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        try:
            key_file.chmod(0o600)
        except OSError:
            pass
        return {
            "enabled": True,
            "configured": True,
            "public_key": public_key,
            "private_key": private_key,
            "subject": subject,
            "source": "generated_local",
        }
    except Exception as exc:
        return {
            "enabled": True,
            "configured": False,
            "public_key": "",
            "private_key": "",
            "subject": subject,
            "source": f"generation_failed:{exc.__class__.__name__}",
        }
