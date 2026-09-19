"""GeoShield emergency communication control plane.

Provides authenticated browser/PWA Web Push subscription management plus
operator diagnostics for SMS and push channels without exposing provider
secrets.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import NotificationDelivery, PushSubscription
from app.services.notifications import notification_dispatcher
from app.services.vapid import get_vapid_config


router = APIRouter(prefix="/api/communications", tags=["communications"])


def _enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _webpush_configured() -> bool:
    return bool(get_vapid_config().get("configured"))


class PushKeys(BaseModel):
    p256dh: str = Field(min_length=20, max_length=1000)
    auth: str = Field(min_length=8, max_length=500)


class PushSubscriptionRequest(BaseModel):
    endpoint: str = Field(min_length=20, max_length=4096)
    keys: PushKeys
    district: str = Field(default="all", min_length=1, max_length=100)


class PushUnsubscribeRequest(BaseModel):
    endpoint: str = Field(min_length=20, max_length=4096)


class CommunicationTestRequest(BaseModel):
    risk_level: Literal["moderate", "high", "critical"] = "high"
    title: str = Field(default="GeoShield communication test", max_length=250)
    message: str = Field(
        default="Emergency communication path test from GeoShield.",
        max_length=1000,
    )
    station_id: str = Field(default="TEST-001", max_length=100)
    district: str = Field(default="all", max_length=100)


@router.get("/status")
def communication_status(
    user: dict = Depends(require_role("admin", "district_admin", "field_officer")),
    db: Session = Depends(get_db),
):
    active_push = (
        db.query(PushSubscription)
        .filter(PushSubscription.is_active == True)
        .count()
    )
    successful_24 = (
        db.query(NotificationDelivery)
        .filter(NotificationDelivery.status == "sent")
        .count()
    )
    return {
        "sms": {
            "enabled": _enabled("SMS_NOTIFICATIONS_ENABLED", False),
            "configured": bool(
                os.getenv("TWILIO_ACCOUNT_SID")
                and os.getenv("TWILIO_AUTH_TOKEN")
                and os.getenv("TWILIO_FROM_NUMBER")
                and (
                    os.getenv("ALERT_SMS_RECIPIENTS")
                    or any(
                        key.startswith("ALERT_SMS_RECIPIENTS_")
                        for key in os.environ
                    )
                )
            ),
            "provider": "Twilio",
        },
        "topic_push": {
            "enabled": _enabled("PUSH_NOTIFICATIONS_ENABLED", False),
            "configured": bool(os.getenv("NTFY_TOPIC")),
            "provider": "ntfy",
        },
        "web_push": {
            "enabled": bool(get_vapid_config().get("enabled")),
            "configured": _webpush_configured(),
            "provider": "Web Push / VAPID",
            "key_source": get_vapid_config().get("source"),
            "active_subscriptions": active_push,
        },
        "delivery_records": successful_24,
    }


@router.get("/webpush/public-key")
def webpush_public_key(user: dict = Depends(get_current_user)):
    config = get_vapid_config()
    if not config.get("enabled") or not config.get("configured") or not config.get("public_key"):
        raise HTTPException(
            status_code=503,
            detail="Web Push is not configured on this GeoShield server.",
        )
    return {
        "public_key": config["public_key"],
        "provider": "Web Push / VAPID",
        "key_source": config["source"],
    }


@router.post("/webpush/subscribe")
def subscribe_webpush(
    payload: PushSubscriptionRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    district = payload.district.strip() or "all"
    email = str(user.get("sub") or "").strip().lower()
    subscription = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == payload.endpoint)
        .first()
    )
    if subscription is None:
        subscription = PushSubscription(
            user_email=email,
            endpoint=payload.endpoint,
            p256dh=payload.keys.p256dh,
            auth=payload.keys.auth,
            district=district,
            is_active=True,
        )
        db.add(subscription)
    else:
        subscription.user_email = email
        subscription.p256dh = payload.keys.p256dh
        subscription.auth = payload.keys.auth
        subscription.district = district
        subscription.is_active = True
        subscription.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(subscription)
    return {
        "status": "subscribed",
        "id": subscription.id,
        "district": subscription.district,
    }


@router.delete("/webpush/subscribe")
def unsubscribe_webpush(
    payload: PushUnsubscribeRequest,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    email = str(user.get("sub") or "").strip().lower()
    subscription = (
        db.query(PushSubscription)
        .filter(
            PushSubscription.endpoint == payload.endpoint,
            PushSubscription.user_email == email,
        )
        .first()
    )
    if subscription is None:
        return {"status": "not_found"}
    subscription.is_active = False
    subscription.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "unsubscribed"}


@router.get("/deliveries")
def communication_deliveries(
    limit: int = Query(50, ge=1, le=200),
    channel: Literal["sms", "push"] | None = None,
    user: dict = Depends(require_role("admin", "district_admin", "field_officer")),
    db: Session = Depends(get_db),
):
    query = db.query(NotificationDelivery)
    if channel:
        query = query.filter(NotificationDelivery.channel == channel)
    rows = query.order_by(desc(NotificationDelivery.created_at)).limit(limit).all()
    return [
        {
            "id": row.id,
            "alert_id": row.alert_id,
            "channel": row.channel,
            "provider": row.provider,
            "recipient": row.recipient,
            "district": row.district,
            "status": row.status,
            "detail": row.detail,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


def _test_alert(payload: CommunicationTestRequest) -> dict:
    return {
        "id": None,
        "risk_level": payload.risk_level,
        "title": payload.title,
        "message": payload.message,
        "station_id": payload.station_id,
        "district": payload.district,
    }


@router.post("/test/sms")
async def test_sms(
    payload: CommunicationTestRequest,
    user: dict = Depends(require_role("admin", "district_admin")),
):
    result = await notification_dispatcher.send_sms(_test_alert(payload))
    return {"status": "completed", "channel": "sms", "delivery": result}


@router.post("/test/push")
async def test_push(
    payload: CommunicationTestRequest,
    user: dict = Depends(require_role("admin", "district_admin")),
):
    result = await notification_dispatcher.send_push(_test_alert(payload))
    return {"status": "completed", "channel": "push", "delivery": result}
