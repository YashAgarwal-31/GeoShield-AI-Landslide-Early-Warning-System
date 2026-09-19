"""Authenticated real-time alert delivery for GeoShield.

The hub is intentionally process-local. The production container currently runs a
single Uvicorn worker, so this gives deterministic live updates without adding an
external broker. Multi-worker deployments should replace the in-memory hub with
Redis pub/sub or an equivalent shared message bus.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket


@dataclass
class _Connection:
    websocket: WebSocket
    district: str
    user_email: str
    user_role: str


class AlertConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, _Connection] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _normalize_district(district: str | None) -> str:
        value = (district or "all").strip()
        if not value:
            value = "all"
        return value[:100]

    async def connect(self, websocket: WebSocket, district: str, user: dict[str, Any]) -> None:
        await websocket.accept()
        connection = _Connection(
            websocket=websocket,
            district=self._normalize_district(district),
            user_email=str(user.get("sub") or ""),
            user_role=str(user.get("role") or ""),
        )
        async with self._lock:
            self._connections[id(websocket)] = connection

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.pop(id(websocket), None)

    async def subscribe(self, websocket: WebSocket, district: str) -> str:
        normalized = self._normalize_district(district)
        async with self._lock:
            connection = self._connections.get(id(websocket))
            if connection is not None:
                connection.district = normalized
        return normalized

    async def broadcast(self, message: dict[str, Any], district: str | None = None) -> int:
        target = self._normalize_district(district) if district else None
        async with self._lock:
            connections = list(self._connections.values())

        delivered = 0
        stale: list[WebSocket] = []
        for connection in connections:
            subscription = connection.district.casefold()
            if target is not None and subscription not in {"all", target.casefold()}:
                continue
            try:
                await connection.websocket.send_json(message)
                delivered += 1
            except Exception:
                stale.append(connection.websocket)

        for websocket in stale:
            await self.disconnect(websocket)
        return delivered

    async def publish_alert(
        self,
        *,
        event_type: str,
        alert: Any,
        district: str | None = None,
    ) -> int:
        payload = {
            "type": event_type,
            "alert": {
                "id": alert.id,
                "station_id": alert.station_id,
                "risk_level": alert.risk_level,
                "title": alert.title,
                "message": alert.message,
                "status": alert.status,
                "affected_population": alert.affected_population,
                "latitude": alert.latitude,
                "longitude": alert.longitude,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            },
            "district": district,
        }
        delivered = await self.broadcast(payload, district=district)
        if event_type == "alert.created":
            # Out-of-band delivery is best-effort and must never delay WebSocket updates.
            try:
                from app.services.notifications import notification_dispatcher
                notification_payload = dict(payload["alert"])
                notification_payload["district"] = district
                asyncio.create_task(notification_dispatcher.dispatch_alert(notification_payload))
            except Exception:
                pass
        return delivered


alert_manager = AlertConnectionManager()
