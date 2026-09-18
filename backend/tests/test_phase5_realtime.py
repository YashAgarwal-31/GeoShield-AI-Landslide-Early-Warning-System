"""Phase 5 regression tests for authenticated operational live updates."""
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.auth import create_token
from app.database import SessionLocal
from app.main import app
from app.models import Alert, RiskAssessment, SensorReading


client = TestClient(app)


def _token(role: str = "admin") -> str:
    return create_token(
        {
            "email": f"{role}-phase5@test.invalid",
            "name": f"Phase 5 {role}",
            "role": role,
        }
    )


def test_websocket_requires_authentication():
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/alerts/all") as websocket:
            websocket.receive_json()
    assert exc.value.code == 4401


def test_authenticated_websocket_subscribes_and_receives_simulator_alert():
    token = _token("admin")

    with client.websocket_connect(f"/ws/alerts/all?token={token}") as websocket:
        connected = websocket.receive_json()
        assert connected["type"] == "connected"
        assert connected["district"] == "all"

        websocket.send_text("subscribe:East Khasi Hills")
        subscribed = websocket.receive_json()
        assert subscribed == {
            "type": "subscribed",
            "district": "East Khasi Hills",
        }

        response = client.post(
            "/api/simulate/landslide",
            json={"station_id": "NER-011", "intensity": "critical"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["alert"] is not None

        event = websocket.receive_json()
        assert event["type"] == "alert.created"
        assert event["district"] == "East Khasi Hills"
        assert event["alert"]["risk_level"] == "critical"
        assert event["alert"]["title"].startswith("[SIMULATION]")

    client.post(
        "/api/simulate/reset",
        headers={"Authorization": f"Bearer {token}"},
    )


def test_sensor_gateway_emits_realtime_reading_event(monkeypatch):
    monkeypatch.setenv("SENSOR_INGEST_ENABLED", "true")
    monkeypatch.setenv("SENSOR_INGEST_API_KEY", "phase5-sensor-secret")
    token = _token("citizen")
    external_id = f"phase5-{uuid.uuid4().hex}"

    payload = {
        "external_id": external_id,
        "rainfall_mm": 12,
        "soil_moisture": 45,
        "soil_temperature": 24,
        "ground_displacement": 0.2,
        "tilt_angle_x": 0.1,
        "tilt_angle_y": 0.1,
        "pore_water_pressure": 10,
        "vibration_level": 1,
    }

    with client.websocket_connect(f"/ws/alerts/all?token={token}") as websocket:
        assert websocket.receive_json()["type"] == "connected"

        response = client.post(
            "/api/sensors/stations/NER-001/readings",
            json=payload,
            headers={"X-GeoShield-Sensor-Key": "phase5-sensor-secret"},
        )
        assert response.status_code == 201, response.text

        seen_reading = None
        for _ in range(2):
            event = websocket.receive_json()
            if event["type"] == "sensor.reading":
                seen_reading = event
                break

        assert seen_reading is not None
        assert seen_reading["station_id"] == "NER-001"
        assert seen_reading["reading"]["external_id"] == external_id
        assert 0 <= seen_reading["risk_assessment"]["risk_score"] <= 100

    db = SessionLocal()
    try:
        reading = db.query(SensorReading).filter(SensorReading.external_id == external_id).first()
        if reading is not None:
            timestamp = reading.timestamp
            db.query(Alert).filter(
                Alert.station_id == "NER-001",
                Alert.title.like("[SENSOR]%"),
                Alert.created_at >= timestamp,
            ).delete(synchronize_session=False)
            db.query(RiskAssessment).filter(
                RiskAssessment.station_id == "NER-001",
                RiskAssessment.model_version == "v2.1-sensor-ingest",
                RiskAssessment.timestamp == timestamp,
            ).delete(synchronize_session=False)
            db.delete(reading)
            db.commit()
    finally:
        db.close()
