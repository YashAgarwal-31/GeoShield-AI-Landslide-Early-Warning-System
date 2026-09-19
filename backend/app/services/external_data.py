"""Resilient weather and satellite-snapshot adapters.

Live weather is enabled by default and can be disabled explicitly with
``WEATHER_LIVE_ENABLED=false`` for a fully deterministic offline demo. Every
result carries machine-readable source and freshness metadata, and upstream
failures are converted into an offline fallback instead of an API error.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
from typing import Any

import httpx


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: str | datetime | None) -> datetime | None:
    """Parse an ISO timestamp and normalize it to aware UTC."""
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    normalized = parse_timestamp(value)
    return normalized.isoformat().replace("+00:00", "Z") if normalized else None


def source_metadata(
    *,
    mode: str,
    provider: str,
    observed_at: str | datetime | None,
    max_age_seconds: int,
    detail: str,
    fallback_reason: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build consistent provenance and freshness metadata."""
    served_at = parse_timestamp(now or utc_now())
    observed = parse_timestamp(observed_at)
    age_seconds = None
    if observed and served_at:
        age_seconds = max(0, int((served_at - observed).total_seconds()))
    is_stale = age_seconds is None or age_seconds > max_age_seconds
    return {
        "mode": mode,
        "provider": provider,
        "observed_at": iso_utc(observed),
        "served_at": iso_utc(served_at),
        "age_seconds": age_seconds,
        "max_age_seconds": max_age_seconds,
        "is_stale": is_stale,
        "fallback_reason": fallback_reason,
        "detail": detail,
    }


@dataclass
class WeatherResult:
    data: dict[str, Any]
    forecast: list[dict[str, Any]]
    source: dict[str, Any]


class OpenMeteoWeatherAdapter:
    """Optional live adapter with bounded timeout and in-memory TTL cache."""

    def __init__(
        self,
        *,
        enabled: bool | None = None,
        timeout_seconds: float | None = None,
        cache_ttl_seconds: int | None = None,
        client: Any | None = None,
    ) -> None:
        self.enabled = enabled if enabled is not None else os.getenv(
            "WEATHER_LIVE_ENABLED", "true"
        ).lower() in {"1", "true", "yes", "on"}
        self.timeout_seconds = timeout_seconds or float(
            os.getenv("WEATHER_REQUEST_TIMEOUT_SECONDS", "5")
        )
        self.cache_ttl_seconds = cache_ttl_seconds or int(
            os.getenv("WEATHER_CACHE_TTL_SECONDS", "900")
        )
        self.client = client
        self._cache: dict[str, tuple[datetime, WeatherResult]] = {}
        self._lock = threading.Lock()

    def get(
        self,
        station_id: str,
        latitude: float,
        longitude: float,
        *,
        forecast_hours: int = 48,
    ) -> tuple[WeatherResult | None, str | None]:
        if not self.enabled:
            return None, "live_fetch_disabled"

        now = utc_now()
        with self._lock:
            cached = self._cache.get(station_id)
        if cached and (now - cached[0]).total_seconds() <= self.cache_ttl_seconds:
            result = cached[1]
            return WeatherResult(
                data=result.data,
                forecast=result.forecast[:forecast_hours],
                source=source_metadata(
                    mode="cached",
                    provider="Open-Meteo forecast API",
                    observed_at=result.source.get("observed_at"),
                    max_age_seconds=self.cache_ttl_seconds,
                    detail="In-memory cache of a successful live weather response.",
                    now=now,
                ),
            ), None

        try:
            result = self._fetch(latitude, longitude, forecast_hours, now)
            with self._lock:
                self._cache[station_id] = (now, result)
            return result, None
        # A live data source must never make the operational API unavailable.
        # Besides HTTP/protocol errors, client construction itself can fail
        # (for example, a configured SOCKS proxy without its optional runtime
        # dependency). Convert every ordinary adapter failure to provenance-
        # labelled fallback data; process-control exceptions still propagate.
        except Exception as exc:
            reason = f"live_fetch_failed:{exc.__class__.__name__}"
            if cached:
                stale = cached[1]
                return WeatherResult(
                    data=stale.data,
                    forecast=stale.forecast[:forecast_hours],
                    source=source_metadata(
                        mode="cached",
                        provider="Open-Meteo forecast API",
                        observed_at=stale.source.get("observed_at"),
                        max_age_seconds=self.cache_ttl_seconds,
                        detail="Stale in-memory weather cache served after a live request failed.",
                        fallback_reason=reason,
                        now=now,
                    ),
                ), reason
            return None, reason

    def _fetch(
        self,
        latitude: float,
        longitude: float,
        forecast_hours: int,
        now: datetime,
    ) -> WeatherResult:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,precipitation,"
                "wind_speed_10m,wind_direction_10m,surface_pressure,visibility"
            ),
            "hourly": "temperature_2m,relative_humidity_2m,precipitation",
            "past_hours": 168,
            "forecast_hours": max(1, min(forecast_hours, 168)),
            "timezone": "UTC",
        }
        if self.client is None:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.get(OPEN_METEO_FORECAST_URL, params=params)
        else:
            response = self.client.get(
                OPEN_METEO_FORECAST_URL,
                params=params,
                timeout=self.timeout_seconds,
            )
        response.raise_for_status()
        payload = response.json()
        current = payload["current"]
        current_time = parse_timestamp(current["time"])
        if current_time is None:
            raise ValueError("Open-Meteo response has an invalid current timestamp")

        hourly = payload["hourly"]
        rows = []
        for timestamp, temperature, humidity, precipitation in zip(
            hourly["time"],
            hourly["temperature_2m"],
            hourly["relative_humidity_2m"],
            hourly["precipitation"],
        ):
            parsed = parse_timestamp(timestamp)
            if parsed is None:
                continue
            rows.append(
                {
                    "timestamp": iso_utc(parsed),
                    "_parsed": parsed,
                    "temperature": temperature,
                    "humidity": humidity,
                    "rainfall_1h": precipitation or 0,
                }
            )

        history = [row for row in rows if row["_parsed"] <= current_time]
        future = [row for row in rows if row["_parsed"] > current_time][
            :forecast_hours
        ]
        rainfall_24h = sum(row["rainfall_1h"] for row in history[-24:])
        rainfall_7d = sum(row["rainfall_1h"] for row in history[-168:])
        forecast_24h = sum(row["rainfall_1h"] for row in future[:24])
        forecast_48h = sum(row["rainfall_1h"] for row in future[:48])
        clean_forecast = [
            {key: value for key, value in row.items() if key != "_parsed"}
            for row in future
        ]

        data = {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "rainfall_1h": current.get("precipitation", 0),
            "rainfall_24h": round(rainfall_24h, 2),
            "rainfall_7d": round(rainfall_7d, 2),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "pressure": current.get("surface_pressure"),
            "visibility": current.get("visibility"),
            "forecast_rainfall_24h": round(forecast_24h, 2),
            "forecast_rainfall_48h": round(forecast_48h, 2),
            "timestamp": iso_utc(current_time),
        }
        source = source_metadata(
            mode="live",
            provider="Open-Meteo forecast API",
            observed_at=current_time,
            max_age_seconds=self.cache_ttl_seconds,
            detail="Live model-derived weather response fetched for this request.",
            now=now,
        )
        return WeatherResult(data=data, forecast=clean_forecast, source=source)


class SatelliteSnapshotAdapter:
    """File-backed satellite snapshot with mtime-aware cache and provenance."""

    def __init__(self, path: str | Path, *, max_age_seconds: int | None = None):
        self.path = Path(path)
        self.max_age_seconds = max_age_seconds or int(
            os.getenv("SATELLITE_MAX_AGE_SECONDS", "21600")
        )
        self._mtime_ns: int | None = None
        self._data: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def load(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        now = utc_now()
        try:
            mtime_ns = self.path.stat().st_mtime_ns
            with self._lock:
                if self._mtime_ns != mtime_ns:
                    loaded = json.loads(self.path.read_text(encoding="utf-8"))
                    if not isinstance(loaded, list):
                        raise ValueError("satellite snapshot must contain a list")
                    self._data = loaded
                    self._mtime_ns = mtime_ns
                data = list(self._data)
        except (FileNotFoundError, OSError, json.JSONDecodeError, ValueError) as exc:
            return [], source_metadata(
                mode="unavailable",
                provider="Open-Meteo-derived repository snapshot",
                observed_at=None,
                max_age_seconds=self.max_age_seconds,
                detail="Satellite snapshot could not be loaded.",
                fallback_reason=f"snapshot_load_failed:{exc.__class__.__name__}",
                now=now,
            )

        observed_values = [
            parse_timestamp(item.get("last_updated")) for item in data
        ]
        observed_values = [value for value in observed_values if value is not None]
        observed_at = min(observed_values) if observed_values else datetime.fromtimestamp(
            self.path.stat().st_mtime, tz=timezone.utc
        )
        return data, source_metadata(
            mode="cached",
            provider="Open-Meteo-derived repository snapshot",
            observed_at=observed_at,
            max_age_seconds=self.max_age_seconds,
            detail=(
                "Cached station snapshot; elevation/weather fields are API-derived "
                "and NDVI is estimated."
            ),
            now=now,
        )


weather_adapter = OpenMeteoWeatherAdapter()
