"""India Meteorological Department (IMD) API adapter.

IMD documents public API endpoints but may require source-IP whitelisting for
some products. GeoShield therefore treats IMD as the preferred provider when
available and falls back cleanly when access is denied or the service is down.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
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


def _first(mapping: dict[str, Any], *names: str) -> Any:
    lowered = {str(k).strip().casefold(): v for k, v in mapping.items()}
    for name in names:
        if name.casefold() in lowered:
            return lowered[name.casefold()]
    return None


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


class IMDAdapter:
    CURRENT_URL = "https://mausam.imd.gov.in/api/current_wx_api.php"
    DISTRICT_RAIN_URL = "https://mausam.imd.gov.in/api/districtwise_rainfall_api.php"
    DISTRICT_WARNING_URL = "https://mausam.imd.gov.in/api/warnings_district_api.php"

    def __init__(self) -> None:
        self.enabled = _env_bool("IMD_LIVE_ENABLED", True)
        self.timeout = float(os.getenv("IMD_REQUEST_TIMEOUT_SECONDS", "7"))
        self.cache_ttl_seconds = int(os.getenv("IMD_CACHE_TTL_SECONDS", "900"))
        self._cache: dict[str, tuple[datetime, Any]] = {}
        self._lock = threading.Lock()

    def _get_json(self, key: str, url: str, params: dict[str, Any] | None = None) -> Any:
        now = datetime.now(timezone.utc)
        with self._lock:
            cached = self._cache.get(key)
        if cached and (now - cached[0]).total_seconds() <= self.cache_ttl_seconds:
            return cached[1]

        headers = {
            "Accept": "application/json",
            "User-Agent": "GeoShield/1.1 academic early-warning prototype",
        }
        with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=headers) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()
        with self._lock:
            self._cache[key] = (now, payload)
        return payload

    @staticmethod
    def _records(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if isinstance(payload, dict):
            for key in ("data", "records", "result", "results", "current", "weather"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [row for row in value if isinstance(row, dict)]
            # Some IMD APIs return an object keyed by station/district.
            nested = [v for v in payload.values() if isinstance(v, dict)]
            if nested:
                return nested
            return [payload]
        return []

    @staticmethod
    def _coords(row: dict[str, Any]) -> tuple[float | None, float | None]:
        lat = _float(_first(row, "Latitude", "lat", "latitude", "Lat"))
        lon = _float(_first(row, "Longitude", "lon", "lng", "longitude", "Long"))
        return lat, lon

    @staticmethod
    def _distance(lat: float, lon: float, other_lat: float, other_lon: float) -> float:
        # Haversine distance in kilometres.
        r = 6371.0
        p1 = math.radians(lat)
        p2 = math.radians(other_lat)
        dp = math.radians(other_lat - lat)
        dl = math.radians(other_lon - lon)
        a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))

    def current_nearest(self, lat: float, lon: float) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if not self.enabled:
            return None, source_metadata(
                mode="unavailable",
                provider="India Meteorological Department (IMD)",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="IMD live integration is disabled.",
                fallback_reason="imd_live_disabled",
                now=now,
            )

        try:
            payload = self._get_json("current-all", self.CURRENT_URL)
            records = self._records(payload)
            candidates: list[tuple[float, dict[str, Any]]] = []
            for row in records:
                rlat, rlon = self._coords(row)
                if rlat is not None and rlon is not None:
                    candidates.append((self._distance(lat, lon, rlat, rlon), row))
            if not candidates:
                raise ValueError("IMD response did not include geocoded station records")
            distance_km, row = min(candidates, key=lambda item: item[0])

            date_obs = _first(row, "Date of Observation", "date", "Date", "observation_date")
            time_obs = _first(row, "Time", "time", "observation_time")
            observed_at = None
            if date_obs:
                try:
                    text = f"{date_obs}T{str(time_obs or '00:00').strip()}"
                    observed_at = datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
                except ValueError:
                    observed_at = None

            data = {
                "station": _first(row, "Station", "station", "Station Name", "station_name"),
                "temperature": _float(_first(row, "Temperature", "temperature", "Temp")),
                "humidity": _float(_first(row, "Humidity", "humidity", "RH")),
                "rainfall_24h": _float(_first(row, "Last 24 hrs Rainfall", "rainfall_24h", "Rainfall")),
                "wind_speed": _float(_first(row, "Wind Speed", "wind_speed")),
                "wind_direction": _first(row, "Wind Direction", "wind_direction"),
                "pressure": _float(_first(row, "M.S.L.P", "MSLP", "pressure")),
                "weather_code": _first(row, "Weather Code", "weather_code"),
                "distance_km": round(distance_km, 1),
                "raw_station_id": _first(row, "Station Id", "Station ID", "id", "station_id"),
            }
            return data, source_metadata(
                mode="live",
                provider="India Meteorological Department (IMD) Current Weather API",
                observed_at=observed_at or now,
                max_age_seconds=self.cache_ttl_seconds,
                detail="Nearest geocoded IMD current-weather observation.",
                now=now,
            )
        except Exception as exc:
            return None, source_metadata(
                mode="unavailable",
                provider="India Meteorological Department (IMD)",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail=(
                    "IMD request failed. Some IMD products require source-IP whitelisting; "
                    "GeoShield will continue with the configured fallback provider."
                ),
                fallback_reason=f"imd_fetch_failed:{exc.__class__.__name__}",
                now=now,
            )

    def district_rainfall(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if not self.enabled:
            return [], source_metadata(
                mode="unavailable",
                provider="IMD District-wise Rainfall API",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="IMD live integration is disabled.",
                fallback_reason="imd_live_disabled",
                now=now,
            )
        try:
            payload = self._get_json("district-rainfall", self.DISTRICT_RAIN_URL)
            rows = self._records(payload)
            return rows, source_metadata(
                mode="live",
                provider="IMD District-wise Rainfall API",
                observed_at=now,
                max_age_seconds=self.cache_ttl_seconds,
                detail="District rainfall data fetched from the official IMD endpoint.",
                now=now,
            )
        except Exception as exc:
            return [], source_metadata(
                mode="unavailable",
                provider="IMD District-wise Rainfall API",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="IMD district-rainfall endpoint is unavailable to this deployment.",
                fallback_reason=f"imd_fetch_failed:{exc.__class__.__name__}",
                now=now,
            )

    def district_warnings(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if not self.enabled:
            return [], source_metadata(
                mode="unavailable",
                provider="IMD District Warning API",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="IMD live integration is disabled.",
                fallback_reason="imd_live_disabled",
                now=now,
            )
        try:
            payload = self._get_json("district-warnings", self.DISTRICT_WARNING_URL)
            rows = self._records(payload)
            return rows, source_metadata(
                mode="live",
                provider="IMD District Warning API",
                observed_at=now,
                max_age_seconds=self.cache_ttl_seconds,
                detail="District warnings fetched from the official IMD endpoint.",
                now=now,
            )
        except Exception as exc:
            return [], source_metadata(
                mode="unavailable",
                provider="IMD District Warning API",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="IMD district-warning endpoint is unavailable to this deployment.",
                fallback_reason=f"imd_fetch_failed:{exc.__class__.__name__}",
                now=now,
            )


imd_adapter = IMDAdapter()
