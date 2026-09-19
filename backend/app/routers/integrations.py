"""Operational integration endpoints for live GeoShield data providers."""
from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.auth import require_role
from app.services.geospatial_live import get_live_terrain
from app.services.imd import imd_adapter
from app.services.notifications import notification_dispatcher


router = APIRouter(prefix="/api/integrations", tags=["integrations"])


def _enabled(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@router.get("/status")
def integration_status():
    return {
        "srtm": {
            "enabled": _enabled("SRTM_LIVE_ENABLED", True),
            "provider": "NASA SRTM / AWS Open Data Skadi",
        },
        "sentinel2": {
            "enabled": _enabled("SENTINEL2_LIVE_ENABLED", True),
            "provider": "Sentinel-2 L2A / Element 84 Earth Search",
        },
        "imd": {
            "enabled": _enabled("IMD_LIVE_ENABLED", True),
            "provider": "India Meteorological Department",
            "note": "Some IMD endpoints require deployment-IP whitelisting.",
        },
        "sms": {
            "enabled": _enabled("SMS_NOTIFICATIONS_ENABLED", False),
            "configured": bool(
                os.getenv("TWILIO_ACCOUNT_SID")
                and os.getenv("TWILIO_AUTH_TOKEN")
                and os.getenv("TWILIO_FROM_NUMBER")
                and os.getenv("ALERT_SMS_RECIPIENTS")
            ),
            "provider": "Twilio",
        },
        "push": {
            "enabled": _enabled("PUSH_NOTIFICATIONS_ENABLED", False),
            "configured": bool(os.getenv("NTFY_TOPIC")),
            "provider": "ntfy",
        },
        "web_push": {
            "enabled": _enabled("WEB_PUSH_ENABLED", False),
            "configured": bool(
                os.getenv("VAPID_PUBLIC_KEY")
                and os.getenv("VAPID_PRIVATE_KEY")
                and os.getenv("VAPID_SUBJECT")
            ),
            "provider": "Web Push / VAPID",
        },
        "iot_gateway": {
            "enabled": _enabled("SENSOR_INGEST_ENABLED", False),
            "configured": bool(os.getenv("SENSOR_INGEST_API_KEY")),
            "transport": "HTTPS sensor gateway",
        },
    }


@router.get("/terrain")
def live_terrain(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    sample = get_live_terrain(latitude, longitude)
    return {
        "latitude": latitude,
        "longitude": longitude,
        "elevation": sample.elevation,
        "slope": sample.slope,
        "ndvi": sample.ndvi,
        "sources": {
            "srtm": sample.srtm_source,
            "sentinel2": sample.sentinel_source,
        },
    }


@router.get("/imd/current")
def imd_current(
    latitude: float = Query(..., ge=6, le=38),
    longitude: float = Query(..., ge=68, le=98),
):
    data, source = imd_adapter.current_nearest(latitude, longitude)
    return {"data": data, "source": source}


@router.get("/imd/rainfall")
def imd_rainfall():
    data, source = imd_adapter.district_rainfall()
    return {"data": data, "source": source}


@router.get("/imd/warnings")
def imd_warnings():
    data, source = imd_adapter.district_warnings()
    return {"data": data, "source": source}


class NotificationTestRequest(BaseModel):
    risk_level: Literal["moderate", "high", "critical"] = "high"
    title: str = Field(default="GeoShield notification test", max_length=250)
    message: str = Field(default="Notification delivery test from GeoShield.", max_length=1000)
    station_id: str = Field(default="TEST-001", max_length=100)


@router.post("/notifications/test")
async def test_notifications(
    payload: NotificationTestRequest,
    user: dict = Depends(require_role("admin")),
):
    result = await notification_dispatcher.dispatch_alert(
        {
            "risk_level": payload.risk_level,
            "title": payload.title,
            "message": payload.message,
            "station_id": payload.station_id,
        }
    )
    return {"status": "completed", "delivery": result}
