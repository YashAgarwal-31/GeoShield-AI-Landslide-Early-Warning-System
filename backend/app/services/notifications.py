"""Out-of-band alert delivery adapters for GeoShield.

Supported providers:
- SMS: Twilio REST API (configured entirely by environment variables)
- Push: ntfy-compatible HTTP push endpoint

The core alert pipeline never fails because of a notification-provider outage.
"""
from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str) -> list[str]:
    return [part.strip() for part in os.getenv(name, "").split(",") if part.strip()]


class NotificationDispatcher:
    def __init__(self) -> None:
        self.timeout = float(os.getenv("NOTIFICATION_TIMEOUT_SECONDS", "8"))

    @staticmethod
    def _message(alert: dict[str, Any]) -> str:
        title = str(alert.get("title") or "GeoShield alert")
        level = str(alert.get("risk_level") or "").upper()
        station = str(alert.get("station_id") or "")
        message = str(alert.get("message") or "")
        prefix = f"[GeoShield {level}] " if level else "[GeoShield] "
        body = f"{prefix}{title}"
        if station:
            body += f" | {station}"
        if message:
            body += f" | {message}"
        return body[:1400]

    async def send_sms(self, alert: dict[str, Any]) -> dict[str, Any]:
        if not _env_bool("SMS_NOTIFICATIONS_ENABLED", False):
            return {"enabled": False, "sent": 0, "provider": "twilio"}

        sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        from_number = os.getenv("TWILIO_FROM_NUMBER", "").strip()
        recipients = _csv_env("ALERT_SMS_RECIPIENTS")
        if not sid or not token or not from_number or not recipients:
            return {
                "enabled": True,
                "sent": 0,
                "provider": "twilio",
                "error": "twilio_configuration_incomplete",
            }

        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        sent = 0
        errors: list[str] = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for recipient in recipients:
                try:
                    response = await client.post(
                        url,
                        data={
                            "From": from_number,
                            "To": recipient,
                            "Body": self._message(alert),
                        },
                        auth=(sid, token),
                    )
                    response.raise_for_status()
                    sent += 1
                except Exception as exc:
                    errors.append(exc.__class__.__name__)
        return {
            "enabled": True,
            "sent": sent,
            "provider": "twilio",
            "errors": errors,
        }

    async def send_push(self, alert: dict[str, Any]) -> dict[str, Any]:
        if not _env_bool("PUSH_NOTIFICATIONS_ENABLED", False):
            return {"enabled": False, "sent": 0, "provider": "ntfy"}

        base_url = os.getenv("NTFY_BASE_URL", "https://ntfy.sh").rstrip("/")
        topic = os.getenv("NTFY_TOPIC", "").strip()
        if not topic:
            return {
                "enabled": True,
                "sent": 0,
                "provider": "ntfy",
                "error": "ntfy_topic_missing",
            }

        level = str(alert.get("risk_level") or "moderate").lower()
        priority = "5" if level == "critical" else "4" if level == "high" else "3"
        headers = {
            "Title": str(alert.get("title") or "GeoShield Alert")[:250],
            "Priority": priority,
            "Tags": "warning,earth_americas",
        }
        token = os.getenv("NTFY_ACCESS_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{base_url}/{topic}",
                    content=self._message(alert).encode("utf-8"),
                    headers=headers,
                )
                response.raise_for_status()
            return {"enabled": True, "sent": 1, "provider": "ntfy"}
        except Exception as exc:
            return {
                "enabled": True,
                "sent": 0,
                "provider": "ntfy",
                "error": f"push_failed:{exc.__class__.__name__}",
            }

    async def dispatch_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        if str(alert.get("risk_level") or "").lower() not in {"moderate", "high", "critical"}:
            return {"skipped": "risk_level_below_notification_threshold"}

        sms_result, push_result = await asyncio.gather(
            self.send_sms(alert),
            self.send_push(alert),
            return_exceptions=False,
        )
        return {"sms": sms_result, "push": push_result}


notification_dispatcher = NotificationDispatcher()
