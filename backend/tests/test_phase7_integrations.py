import asyncio
import os

import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.services.flood_live import FloodForecastAdapter
from app.services.geospatial_live import SRTMAdapter
from app.services.imd import IMDAdapter
from app.services.notifications import NotificationDispatcher


client = TestClient(app)


def test_srtm_sample_calculates_elevation_and_slope(monkeypatch):
    adapter = SRTMAdapter()
    adapter.enabled = True
    # North-to-south and west-to-east gradient, enough to verify the local slope path.
    data = np.array(
        [
            [120, 125, 130, 135, 140],
            [115, 120, 125, 130, 135],
            [110, 115, 120, 125, 130],
            [105, 110, 115, 120, 125],
            [100, 105, 110, 115, 120],
        ],
        dtype=np.float32,
    )
    monkeypatch.setattr(adapter, "_load", lambda lat, lon: (data, "N25E091"))

    sample, source = adapter.sample(25.5, 91.5)

    assert sample is not None
    assert sample["tile"] == "N25E091"
    assert 100 <= sample["elevation"] <= 140
    assert sample["slope"] > 0
    assert source["mode"] == "live"


def test_imd_adapter_selects_nearest_geocoded_station(monkeypatch):
    adapter = IMDAdapter()
    adapter.enabled = True
    monkeypatch.setattr(
        adapter,
        "_get_json",
        lambda *args, **kwargs: [
            {
                "Station": "Far Station",
                "Latitude": "28.0",
                "Longitude": "95.0",
                "Temperature": "19.0",
                "Humidity": "80",
            },
            {
                "Station": "Shillong",
                "Latitude": "25.57",
                "Longitude": "91.88",
                "Temperature": "21.5",
                "Humidity": "75",
                "Last 24 hrs Rainfall": "12.4",
            },
        ],
    )

    data, source = adapter.current_nearest(25.58, 91.89)

    assert data is not None
    assert data["station"] == "Shillong"
    assert data["temperature"] == 21.5
    assert data["rainfall_24h"] == 12.4
    assert data["distance_km"] < 5
    assert source["mode"] == "live"


def test_flood_summary_extracts_live_discharge_series():
    payload = {
        "daily_units": {"river_discharge": "m³/s"},
        "daily": {
            "time": ["2026-09-18", "2026-09-19", "2026-09-20"],
            "river_discharge": [100.0, 120.0, 150.0],
            "river_discharge_max": [110.0, 140.0, 180.0],
        },
    }
    result = FloodForecastAdapter._summarize(payload)
    assert result["river_discharge_unit"] == "m³/s"
    assert result["river_discharge_forecast_max"] is not None


def test_notification_dispatch_is_safe_when_external_delivery_disabled(monkeypatch):
    monkeypatch.setenv("SMS_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("PUSH_NOTIFICATIONS_ENABLED", "false")
    dispatcher = NotificationDispatcher()
    result = asyncio.run(
        dispatcher.dispatch_alert(
            {
                "risk_level": "critical",
                "title": "Critical landslide risk",
                "message": "Test alert",
                "station_id": "NER-001",
            }
        )
    )
    assert result["sms"]["enabled"] is False
    assert result["push"]["enabled"] is False


def test_integrations_status_does_not_expose_secrets():
    response = client.get("/api/integrations/status")
    assert response.status_code == 200
    data = response.json()
    assert {"srtm", "sentinel2", "imd", "sms", "push", "iot_gateway"} <= set(data)
    serialized = response.text.lower()
    assert "auth_token" not in serialized
    assert "api_key" not in serialized
