"""Live river-discharge integration using Open-Meteo's GloFAS flood API."""
from __future__ import annotations

from datetime import date, datetime, timezone
import os
import threading
from typing import Any

import httpx

from app.services.external_data import source_metadata


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class FloodForecastAdapter:
    def __init__(self) -> None:
        self.enabled = _env_bool("FLOOD_LIVE_ENABLED", True)
        self.url = os.getenv(
            "FLOOD_API_URL",
            "https://flood-api.open-meteo.com/v1/flood",
        )
        self.timeout = float(os.getenv("FLOOD_REQUEST_TIMEOUT_SECONDS", "8"))
        self.cache_ttl_seconds = int(os.getenv("FLOOD_CACHE_TTL_SECONDS", "1800"))
        self._cache: dict[str, tuple[datetime, list[dict[str, Any]]]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _summarize(payload: dict[str, Any]) -> dict[str, Any]:
        daily = payload.get("daily") or {}
        times = daily.get("time") or []
        values = daily.get("river_discharge") or []
        max_values = daily.get("river_discharge_max") or []
        pairs = [
            (str(t), float(v))
            for t, v in zip(times, values)
            if v is not None
        ]
        if not pairs:
            return {
                "river_discharge_today": None,
                "river_discharge_7d_max": None,
                "river_discharge_forecast_max": None,
                "river_discharge_unit": "m³/s",
            }

        today = date.today().isoformat()
        today_value = next((v for t, v in pairs if t == today), pairs[min(7, len(pairs) - 1)][1])
        past = [v for t, v in pairs if t <= today][-7:]
        future = [v for t, v in pairs if t >= today][:8]
        future_max_series = [
            float(v)
            for t, v in zip(times, max_values)
            if v is not None and str(t) >= today
        ][:8]
        return {
            "river_discharge_today": round(today_value, 2),
            "river_discharge_7d_max": round(max(past), 2) if past else None,
            "river_discharge_forecast_max": round(
                max(future_max_series or future),
                2,
            ) if future else None,
            "river_discharge_unit": (payload.get("daily_units") or {}).get(
                "river_discharge", "m³/s"
            ),
        }

    def batch(
        self,
        coordinates: list[tuple[float, float]],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if not coordinates:
            return [], source_metadata(
                mode="unavailable",
                provider="Open-Meteo GloFAS Flood API",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="No coordinates supplied for flood lookup.",
                fallback_reason="no_coordinates",
                now=now,
            )
        if not self.enabled:
            return [], source_metadata(
                mode="unavailable",
                provider="Open-Meteo GloFAS Flood API",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="Live flood integration is disabled.",
                fallback_reason="flood_live_disabled",
                now=now,
            )

        key = "|".join(f"{lat:.4f},{lon:.4f}" for lat, lon in coordinates)
        with self._lock:
            cached = self._cache.get(key)
        if cached and (now - cached[0]).total_seconds() <= self.cache_ttl_seconds:
            return cached[1], source_metadata(
                mode="cached",
                provider="Open-Meteo GloFAS Flood API",
                observed_at=cached[0],
                max_age_seconds=self.cache_ttl_seconds,
                detail="Cached GloFAS river-discharge response.",
                now=now,
            )

        params = {
            "latitude": ",".join(str(lat) for lat, _ in coordinates),
            "longitude": ",".join(str(lon) for _, lon in coordinates),
            "daily": "river_discharge,river_discharge_max",
            "past_days": 7,
            "forecast_days": 8,
            "cell_selection": "land",
        }
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(self.url, params=params)
                response.raise_for_status()
                payload = response.json()

            items = payload if isinstance(payload, list) else [payload]
            result = [self._summarize(item) for item in items]
            # Open-Meteo returns a single object for one coordinate and a list for many.
            if len(coordinates) == 1 and len(result) == 1:
                pass
            elif len(result) != len(coordinates):
                raise ValueError("Flood API returned an unexpected location count")

            with self._lock:
                self._cache[key] = (now, result)
            return result, source_metadata(
                mode="live",
                provider="Open-Meteo GloFAS v4 Flood API",
                observed_at=now,
                max_age_seconds=self.cache_ttl_seconds,
                detail="Live river-discharge guidance from GloFAS via Open-Meteo.",
                now=now,
            )
        except Exception as exc:
            return [], source_metadata(
                mode="unavailable",
                provider="Open-Meteo GloFAS Flood API",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="Live flood request failed; historical baseline remains available.",
                fallback_reason=f"flood_fetch_failed:{exc.__class__.__name__}",
                now=now,
            )


flood_forecast_adapter = FloodForecastAdapter()
