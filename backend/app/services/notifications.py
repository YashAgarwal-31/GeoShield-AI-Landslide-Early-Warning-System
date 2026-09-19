"""Multi-channel emergency alert delivery for GeoShield.

Channels:
- SMS through Twilio
- Topic push through ntfy
- Standards-based Web Push (VAPID) to subscribed browsers/PWA clients

All channels are fail-soft. Provider outages are recorded but never break the
core alert pipeline or WebSocket delivery.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

import httpx

from app.database import SessionLocal
from app.models import NotificationDelivery, PushSubscription


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv_env(name: str) -> list[str]:
    return [part.strip() for part in os.getenv(name, "").split(",") if part.strip()]


def _district_env_suffix(district: str | None) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", (district or "").upper()).strip("_")


class NotificationDispatcher:
    def __init__(self) -> None:
        self.timeout = float(os.getenv("NOTIFICATION_TIMEOUT_SECONDS", "8"))

    @staticmethod
    def _message(alert: dict[str, Any]) -> str:
        title = str(alert.get("title") or "GeoShield alert")
        level = str(alert.get("risk_level") or "").upper()
        station = str(alert.get("station_id") or "")
        district = str(alert.get("district") or "")
        message = str(alert.get("message") or "")
        prefix = f"[GeoShield {level}] " if level else "[GeoShield] "
        body = f"{prefix}{title}"
        if station:
            body += f" | {station}"
        if district:
            body += f" | {district}"
        if message:
            body += f" | {message}"
        return body[:1400]

    @staticmethod
    def _record(
        *,
        alert: dict[str, Any],
        channel: str,
        provider: str,
        recipient: str | None,
        status: str,
        detail: str | None = None,
    ) -> None:
        db = SessionLocal()
        try:
            db.add(
                NotificationDelivery(
                    alert_id=alert.get("id"),
                    channel=channel,
                    provider=provider,
                    recipient=recipient,
                    district=alert.get("district"),
                    status=status,
                    detail=(detail or "")[:2000] or None,
                )
            )
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def _sms_recipients(alert: dict[str, Any]) -> list[str]:
        recipients = list(_csv_env("ALERT_SMS_RECIPIENTS"))
        suffix = _district_env_suffix(str(alert.get("district") or ""))
        if suffix:
            recipients.extend(_csv_env(f"ALERT_SMS_RECIPIENTS_{suffix}"))
        # Preserve order while removing duplicates.
        return list(dict.fromkeys(recipients))

    async def send_sms(self, alert: dict[str, Any]) -> dict[str, Any]:
        if not _env_bool("SMS_NOTIFICATIONS_ENABLED", False):
            return {"enabled": False, "configured": False, "sent": 0, "provider": "twilio"}

        sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        from_number = os.getenv("TWILIO_FROM_NUMBER", "").strip()
        recipients = self._sms_recipients(alert)
        configured = bool(sid and token and from_number and recipients)
        if not configured:
            return {
                "enabled": True,
                "configured": False,
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
                    provider_id = None
                    try:
                        provider_id = response.json().get("sid")
                    except Exception:
                        pass
                    sent += 1
                    self._record(
                        alert=alert,
                        channel="sms",
                        provider="twilio",
                        recipient=recipient,
                        status="sent",
                        detail=provider_id,
                    )
                except Exception as exc:
                    error_name = exc.__class__.__name__
                    errors.append(error_name)
                    self._record(
                        alert=alert,
                        channel="sms",
                        provider="twilio",
                        recipient=recipient,
                        status="failed",
                        detail=error_name,
                    )
        return {
            "enabled": True,
            "configured": True,
            "sent": sent,
            "attempted": len(recipients),
            "provider": "twilio",
            "errors": errors,
        }

    async def send_ntfy(self, alert: dict[str, Any]) -> dict[str, Any]:
        if not _env_bool("PUSH_NOTIFICATIONS_ENABLED", False):
            return {"enabled": False, "configured": False, "sent": 0, "provider": "ntfy"}

        base_url = os.getenv("NTFY_BASE_URL", "https://ntfy.sh").rstrip("/")
        topic = os.getenv("NTFY_TOPIC", "").strip()
        if not topic:
            return {
                "enabled": True,
                "configured": False,
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
            self._record(
                alert=alert,
                channel="push",
                provider="ntfy",
                recipient=topic,
                status="sent",
            )
            return {"enabled": True, "configured": True, "sent": 1, "provider": "ntfy"}
        except Exception as exc:
            error_name = exc.__class__.__name__
            self._record(
                alert=alert,
                channel="push",
                provider="ntfy",
                recipient=topic,
                status="failed",
                detail=error_name,
            )
            return {
                "enabled": True,
                "configured": True,
                "sent": 0,
                "provider": "ntfy",
                "error": f"push_failed:{error_name}",
            }

    @staticmethod
    def _webpush_config() -> tuple[bool, str, str, str]:
        enabled = _env_bool("WEB_PUSH_ENABLED", False)
        public_key = os.getenv("VAPID_PUBLIC_KEY", "").strip()
        private_key = os.getenv("VAPID_PRIVATE_KEY", "").strip()
        subject = os.getenv("VAPID_SUBJECT", "mailto:admin@geoshield.local").strip()
        return enabled, public_key, private_key, subject

    async def send_web_push(self, alert: dict[str, Any]) -> dict[str, Any]:
        enabled, public_key, private_key, subject = self._webpush_config()
        if not enabled:
            return {"enabled": False, "configured": False, "sent": 0, "provider": "webpush"}
        if not public_key or not private_key or not subject:
            return {
                "enabled": True,
                "configured": False,
                "sent": 0,
                "provider": "webpush",
                "error": "vapid_configuration_incomplete",
            }

        try:
            from pywebpush import WebPushException, webpush
        except Exception:
            return {
                "enabled": True,
                "configured": False,
                "sent": 0,
                "provider": "webpush",
                "error": "pywebpush_unavailable",
            }

        district = str(alert.get("district") or "").strip()
        db = SessionLocal()
        try:
            query = db.query(PushSubscription).filter(PushSubscription.is_active == True)
            subscriptions = query.all()
        finally:
            db.close()

        targets = [
            item
            for item in subscriptions
            if not district
            or item.district.casefold() in {"all", district.casefold()}
        ]
        payload = json.dumps(
            {
                "title": str(alert.get("title") or "GeoShield Alert"),
                "body": self._message(alert),
                "tag": f"geoshield-alert-{alert.get('id') or 'event'}",
                "url": "/#/alerts",
                "risk_level": alert.get("risk_level"),
                "district": district or None,
            }
        )

        sent = 0
        errors: list[str] = []
        stale_ids: list[int] = []
        for subscription in targets:
            try:
                await asyncio.to_thread(
                    webpush,
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh,
                            "auth": subscription.auth,
                        },
                    },
                    data=payload,
                    vapid_private_key=private_key,
                    vapid_claims={"sub": subject},
                    ttl=300,
                )
                sent += 1
                self._record(
                    alert=alert,
                    channel="push",
                    provider="webpush",
                    recipient=subscription.user_email,
                    status="sent",
                )
            except WebPushException as exc:
                status_code = getattr(getattr(exc, "response", None), "status_code", None)
                if status_code in {404, 410}:
                    stale_ids.append(subscription.id)
                error = f"WebPushException:{status_code or 'unknown'}"
                errors.append(error)
                self._record(
                    alert=alert,
                    channel="push",
                    provider="webpush",
                    recipient=subscription.user_email,
                    status="failed",
                    detail=error,
                )
            except Exception as exc:
                error = exc.__class__.__name__
                errors.append(error)
                self._record(
                    alert=alert,
                    channel="push",
                    provider="webpush",
                    recipient=subscription.user_email,
                    status="failed",
                    detail=error,
                )

        if stale_ids:
            db = SessionLocal()
            try:
                db.query(PushSubscription).filter(
                    PushSubscription.id.in_(stale_ids)
                ).update({"is_active": False}, synchronize_session=False)
                db.commit()
            finally:
                db.close()

        return {
            "enabled": True,
            "configured": True,
            "sent": sent,
            "attempted": len(targets),
            "provider": "webpush",
            "errors": errors,
        }

    async def send_push(self, alert: dict[str, Any]) -> dict[str, Any]:
        ntfy_result, web_result = await asyncio.gather(
            self.send_ntfy(alert),
            self.send_web_push(alert),
        )
        return {
            "enabled": bool(ntfy_result.get("enabled") or web_result.get("enabled")),
            "configured": bool(ntfy_result.get("configured") or web_result.get("configured")),
            "sent": int(ntfy_result.get("sent", 0)) + int(web_result.get("sent", 0)),
            "providers": {
                "ntfy": ntfy_result,
                "webpush": web_result,
            },
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
