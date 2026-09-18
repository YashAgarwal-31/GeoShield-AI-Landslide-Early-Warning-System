"""Regression tests for source freshness, live cache, and snapshot fallback."""

from datetime import datetime, timezone
import json

from app.services.external_data import (
    OpenMeteoWeatherAdapter,
    SatelliteSnapshotAdapter,
    source_metadata,
)


def test_source_metadata_marks_old_observation_stale():
    metadata = source_metadata(
        mode="cached",
        provider="test",
        observed_at="2026-01-01T00:00:00Z",
        max_age_seconds=3600,
        detail="test snapshot",
        now=datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc),
    )

    assert metadata["age_seconds"] == 7200
    assert metadata["is_stale"] is True
    assert metadata["observed_at"].endswith("Z")


def test_satellite_adapter_reports_cached_snapshot_age(tmp_path):
    path = tmp_path / "satellite.json"
    path.write_text(
        json.dumps([{"id": "NER-001", "last_updated": "2026-01-01T00:00:00Z"}]),
        encoding="utf-8",
    )
    adapter = SatelliteSnapshotAdapter(path, max_age_seconds=1)

    data, source = adapter.load()

    assert data[0]["id"] == "NER-001"
    assert source["mode"] == "cached"
    assert source["is_stale"] is True


class _FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "current": {
                "time": "2026-01-01T02:00",
                "temperature_2m": 21.0,
                "relative_humidity_2m": 80,
                "precipitation": 1.0,
                "wind_speed_10m": 5.0,
                "wind_direction_10m": 120,
                "surface_pressure": 900,
                "visibility": 10000,
            },
            "hourly": {
                "time": [
                    "2026-01-01T00:00",
                    "2026-01-01T01:00",
                    "2026-01-01T02:00",
                    "2026-01-01T03:00",
                    "2026-01-01T04:00",
                ],
                "temperature_2m": [19, 20, 21, 22, 23],
                "relative_humidity_2m": [85, 82, 80, 78, 75],
                "precipitation": [0, 1, 1, 2, 0],
            },
        }


class _FakeClient:
    def __init__(self):
        self.calls = 0

    def get(self, *_args, **_kwargs):
        self.calls += 1
        return _FakeResponse()


def test_live_weather_adapter_caches_successful_response():
    client = _FakeClient()
    adapter = OpenMeteoWeatherAdapter(
        enabled=True,
        cache_ttl_seconds=900,
        client=client,
    )

    live, live_error = adapter.get("NER-001", 27.3, 88.6, forecast_hours=2)
    cached, cached_error = adapter.get("NER-001", 27.3, 88.6, forecast_hours=2)

    assert live_error is None and cached_error is None
    assert live is not None and cached is not None
    assert live.source["mode"] == "live"
    assert cached.source["mode"] == "cached"
    assert live.data["rainfall_24h"] == 2
    assert len(live.forecast) == 2
    assert client.calls == 1
