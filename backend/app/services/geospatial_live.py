"""Live geospatial adapters used by GeoShield.

The adapters fail soft: if a public upstream is unavailable the caller can keep
using the repository snapshot / station defaults. Successful responses include
source and freshness metadata so the UI can distinguish live data from fallback.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import gzip
import math
import os
import threading
from typing import Any

import httpx
import numpy as np

from app.services.external_data import source_metadata


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class TerrainSample:
    elevation: float | None
    slope: float | None
    ndvi: float | None
    srtm_source: dict[str, Any]
    sentinel_source: dict[str, Any]


class SRTMAdapter:
    """On-demand SRTM elevation/slope sampling from the AWS Open Data Skadi tiles."""

    def __init__(self) -> None:
        self.enabled = _env_bool("SRTM_LIVE_ENABLED", True)
        self.base_url = os.getenv(
            "SRTM_BASE_URL",
            "https://s3.amazonaws.com/elevation-tiles-prod/skadi",
        ).rstrip("/")
        self.timeout = float(os.getenv("SRTM_REQUEST_TIMEOUT_SECONDS", "10"))
        self.max_age_seconds = int(os.getenv("SRTM_CACHE_MAX_AGE_SECONDS", "86400"))
        self._cache: dict[str, tuple[datetime, np.ndarray]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _tile(lat: float, lon: float) -> tuple[str, str, int, int]:
        lat0 = math.floor(lat)
        lon0 = math.floor(lon)
        lat_prefix = ("N" if lat0 >= 0 else "S") + f"{abs(lat0):02d}"
        lon_prefix = ("E" if lon0 >= 0 else "W") + f"{abs(lon0):03d}"
        tile = f"{lat_prefix}{lon_prefix}"
        return lat_prefix, tile, lat0, lon0

    def _load(self, lat: float, lon: float) -> tuple[np.ndarray, str]:
        lat_prefix, tile, _, _ = self._tile(lat, lon)
        now = datetime.now(timezone.utc)
        with self._lock:
            cached = self._cache.get(tile)
            if cached and (now - cached[0]).total_seconds() <= self.max_age_seconds:
                return cached[1], tile

        url = f"{self.base_url}/{lat_prefix}/{tile}.hgt.gz"
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
        raw = gzip.decompress(response.content)
        count = len(raw) // 2
        size = int(math.isqrt(count))
        if size * size != count or size < 1000:
            raise ValueError(f"Unexpected SRTM tile shape for {tile}")
        data = np.frombuffer(raw, dtype=">i2").reshape((size, size)).astype(np.float32)
        data[data <= -32768] = np.nan
        with self._lock:
            self._cache[tile] = (now, data)
        return data, tile

    @staticmethod
    def _bilinear(data: np.ndarray, row: float, col: float) -> float:
        rows, cols = data.shape
        r0 = max(0, min(rows - 1, int(math.floor(row))))
        c0 = max(0, min(cols - 1, int(math.floor(col))))
        r1 = max(0, min(rows - 1, r0 + 1))
        c1 = max(0, min(cols - 1, c0 + 1))
        fr = row - r0
        fc = col - c0
        vals = np.array(
            [data[r0, c0], data[r0, c1], data[r1, c0], data[r1, c1]],
            dtype=np.float64,
        )
        if np.isnan(vals).all():
            raise ValueError("SRTM cell is void")
        if np.isnan(vals).any():
            return float(np.nanmean(vals))
        top = vals[0] * (1 - fc) + vals[1] * fc
        bottom = vals[2] * (1 - fc) + vals[3] * fc
        return float(top * (1 - fr) + bottom * fr)

    def sample(self, lat: float, lon: float) -> tuple[dict[str, float] | None, dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if not self.enabled:
            return None, source_metadata(
                mode="unavailable",
                provider="NASA SRTM / AWS Open Data",
                observed_at=None,
                max_age_seconds=self.max_age_seconds,
                detail="Live SRTM sampling is disabled.",
                fallback_reason="srtm_live_disabled",
                now=now,
            )

        try:
            data, tile = self._load(lat, lon)
            _, _, lat0, lon0 = self._tile(lat, lon)
            size = data.shape[0]
            # HGT row zero is the north edge of the 1-degree tile.
            row = (lat0 + 1 - lat) * (size - 1)
            col = (lon - lon0) * (size - 1)
            elevation = self._bilinear(data, row, col)

            r = max(1, min(size - 2, int(round(row))))
            c = max(1, min(size - 2, int(round(col))))
            dz_ns = float(data[r - 1, c] - data[r + 1, c])
            dz_ew = float(data[r, c + 1] - data[r, c - 1])
            arc_m_ns = 111_320.0 / (size - 1)
            arc_m_ew = arc_m_ns * max(0.2, math.cos(math.radians(lat)))
            grad_ns = dz_ns / max(1.0, 2 * arc_m_ns)
            grad_ew = dz_ew / max(1.0, 2 * arc_m_ew)
            slope = math.degrees(math.atan(math.sqrt(grad_ns**2 + grad_ew**2)))
            return {
                "elevation": round(elevation, 2),
                "slope": round(slope, 2),
                "tile": tile,
            }, source_metadata(
                mode="live",
                provider="NASA SRTM / AWS Open Data Skadi",
                observed_at=now,
                max_age_seconds=self.max_age_seconds,
                detail=f"Elevation and local slope sampled from {tile}.hgt.",
                now=now,
            )
        except Exception as exc:
            return None, source_metadata(
                mode="unavailable",
                provider="NASA SRTM / AWS Open Data",
                observed_at=None,
                max_age_seconds=self.max_age_seconds,
                detail="SRTM tile could not be sampled; caller should use fallback terrain.",
                fallback_reason=f"srtm_fetch_failed:{exc.__class__.__name__}",
                now=now,
            )


class Sentinel2NDVIAdapter:
    """Recent Sentinel-2 L2A point NDVI using Element 84 Earth Search COG assets."""

    def __init__(self) -> None:
        self.enabled = _env_bool("SENTINEL2_LIVE_ENABLED", True)
        self.stac_url = os.getenv(
            "SENTINEL2_STAC_URL",
            "https://earth-search.aws.element84.com/v1/search",
        )
        self.timeout = float(os.getenv("SENTINEL2_REQUEST_TIMEOUT_SECONDS", "12"))
        self.lookback_days = int(os.getenv("SENTINEL2_LOOKBACK_DAYS", "60"))
        self.max_cloud = float(os.getenv("SENTINEL2_MAX_CLOUD_PERCENT", "35"))
        self.cache_ttl_seconds = int(os.getenv("SENTINEL2_CACHE_TTL_SECONDS", "21600"))
        self._cache: dict[str, tuple[datetime, dict[str, Any]]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _cache_key(lat: float, lon: float) -> str:
        return f"{lat:.4f},{lon:.4f}"

    @staticmethod
    def _asset_value(asset: dict[str, Any], value: float) -> float:
        bands = asset.get("raster:bands") or []
        band = bands[0] if bands else {}
        scale = float(band.get("scale", 1.0) or 1.0)
        offset = float(band.get("offset", 0.0) or 0.0)
        return value * scale + offset

    def _sample_asset(self, asset: dict[str, Any], lat: float, lon: float) -> float:
        try:
            import rasterio
            from rasterio.warp import transform
        except ImportError as exc:
            raise RuntimeError("rasterio is required for Sentinel-2 COG sampling") from exc

        href = asset.get("href")
        if not href:
            raise ValueError("Sentinel-2 asset is missing href")

        with rasterio.Env(AWS_NO_SIGN_REQUEST="YES", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
            with rasterio.open(href) as dataset:
                xs, ys = transform("EPSG:4326", dataset.crs, [lon], [lat])
                sample = next(dataset.sample([(xs[0], ys[0])], indexes=1, masked=True))
                value = sample[0]
                if np.ma.is_masked(value):
                    raise ValueError("Sentinel-2 point is nodata")
                return self._asset_value(asset, float(value))

    def sample(self, lat: float, lon: float) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        now = datetime.now(timezone.utc)
        if not self.enabled:
            return None, source_metadata(
                mode="unavailable",
                provider="Sentinel-2 L2A via Element 84 Earth Search",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="Live Sentinel-2 sampling is disabled.",
                fallback_reason="sentinel2_live_disabled",
                now=now,
            )

        key = self._cache_key(lat, lon)
        with self._lock:
            cached = self._cache.get(key)
        if cached and (now - cached[0]).total_seconds() <= self.cache_ttl_seconds:
            payload = dict(cached[1])
            observed_at = payload.get("observed_at")
            return payload, source_metadata(
                mode="cached",
                provider="Sentinel-2 L2A via Element 84 Earth Search",
                observed_at=observed_at,
                max_age_seconds=self.cache_ttl_seconds,
                detail="Cached result of a successful Sentinel-2 point sample.",
                now=now,
            )

        start = (now - timedelta(days=self.lookback_days)).date().isoformat()
        end = now.date().isoformat()
        search_payload = {
            "collections": ["sentinel-2-l2a"],
            "bbox": [lon - 0.001, lat - 0.001, lon + 0.001, lat + 0.001],
            "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z",
            "query": {"eo:cloud_cover": {"lt": self.max_cloud}},
            "sortby": [{"field": "properties.datetime", "direction": "desc"}],
            "limit": 5,
        }
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.post(self.stac_url, json=search_payload)
                response.raise_for_status()
                features = response.json().get("features") or []
            item = next(
                (
                    candidate
                    for candidate in features
                    if (candidate.get("assets") or {}).get("red")
                    and (candidate.get("assets") or {}).get("nir")
                ),
                None,
            )
            if item is None:
                raise ValueError("No recent Sentinel-2 scene with red/nir assets")

            assets = item["assets"]
            red = self._sample_asset(assets["red"], lat, lon)
            nir = self._sample_asset(assets["nir"], lat, lon)
            denom = nir + red
            if abs(denom) < 1e-12:
                raise ValueError("Sentinel-2 NDVI denominator is zero")
            ndvi = max(-1.0, min(1.0, (nir - red) / denom))
            observed_at = item.get("properties", {}).get("datetime")
            payload = {
                "ndvi": round(float(ndvi), 4),
                "scene_id": item.get("id"),
                "observed_at": observed_at,
                "cloud_cover": item.get("properties", {}).get("eo:cloud_cover"),
            }
            with self._lock:
                self._cache[key] = (now, payload)
            return payload, source_metadata(
                mode="live",
                provider="Sentinel-2 L2A via Element 84 Earth Search",
                observed_at=observed_at,
                max_age_seconds=self.cache_ttl_seconds,
                detail="NDVI computed from recent Sentinel-2 red and NIR COG pixels.",
                now=now,
            )
        except Exception as exc:
            return None, source_metadata(
                mode="unavailable",
                provider="Sentinel-2 L2A via Element 84 Earth Search",
                observed_at=None,
                max_age_seconds=self.cache_ttl_seconds,
                detail="Sentinel-2 sampling failed; caller should use cached/estimated NDVI.",
                fallback_reason=f"sentinel2_fetch_failed:{exc.__class__.__name__}",
                now=now,
            )


srtm_adapter = SRTMAdapter()
sentinel2_adapter = Sentinel2NDVIAdapter()


def get_live_terrain(lat: float, lon: float) -> TerrainSample:
    srtm, srtm_source = srtm_adapter.sample(lat, lon)
    sentinel, sentinel_source = sentinel2_adapter.sample(lat, lon)
    return TerrainSample(
        elevation=(srtm or {}).get("elevation"),
        slope=(srtm or {}).get("slope"),
        ndvi=(sentinel or {}).get("ndvi"),
        srtm_source=srtm_source,
        sentinel_source=sentinel_source,
    )
