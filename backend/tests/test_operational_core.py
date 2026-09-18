"""Operational-core tests for persistent auth, readiness, and sensor ingestion."""
import os
import uuid

# Rate limiting is independently configured and is not the subject of this
# integration module. Disable it here so prior auth calls from the full suite
# cannot make these tests order-dependent.
os.environ["RATE_LIMIT_ENABLED"] = "false"

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Alert, RiskAssessment, SensorReading, SensorStation, UserAccount


client = TestClient(app)


def _admin_headers() -> dict:
    if os.getenv("APP_ENV", "demo").strip().lower() in {"prod", "production"}:
        email = os.environ["GEOSHIELD_ADMIN_EMAIL"]
        password = os.environ["GEOSHIELD_ADMIN_PASSWORD"]
    else:
        email = "admin@geoshield.gov.in"
        password = "admin123"

    response = client.post(
        "/api/auth/login",
        data={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_readiness_checks_database():
    response = client.get("/api/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_persistent_user_can_be_created_and_authenticated():
    suffix = uuid.uuid4().hex[:10]
    email = f"field-{suffix}@test.invalid"
    password = "StrongPass123!"

    create_response = client.post(
        "/api/users",
        json={
            "email": email,
            "name": "Field Test User",
            "password": password,
            "role": "field_officer",
        },
        headers=_admin_headers(),
    )
    assert create_response.status_code == 201, create_response.text
    user_id = create_response.json()["id"]

    login_response = client.post(
        "/api/auth/login",
        data={"email": email, "password": password},
    )
    assert login_response.status_code == 200, login_response.text
    assert login_response.json()["user"]["role"] == "field_officer"

    new_password = "StrongerPass456!"
    reset_response = client.put(
        f"/api/users/{user_id}/password",
        json={"password": new_password},
        headers=_admin_headers(),
    )
    assert reset_response.status_code == 200, reset_response.text

    old_password_login = client.post(
        "/api/auth/login",
        data={"email": email, "password": password},
    )
    assert old_password_login.status_code == 401

    new_password_login = client.post(
        "/api/auth/login",
        data={"email": email, "password": new_password},
    )
    assert new_password_login.status_code == 200, new_password_login.text
    issued_token = new_password_login.json()["token"]

    disable_response = client.put(
        f"/api/users/{user_id}/status",
        json={"is_active": False},
        headers=_admin_headers(),
    )
    assert disable_response.status_code == 200

    disabled_login = client.post(
        "/api/auth/login",
        data={"email": email, "password": password},
    )
    assert disabled_login.status_code == 401

    # A token issued before deactivation must also stop working immediately.
    disabled_existing_session = client.get(
        "/api/reports",
        headers={"Authorization": f"Bearer {issued_token}"},
    )
    assert disabled_existing_session.status_code == 401
    assert disabled_existing_session.json()["detail"] == "Account is disabled"

    db = SessionLocal()
    try:
        account = db.query(UserAccount).filter(UserAccount.id == user_id).first()
        if account:
            db.delete(account)
            db.commit()
    finally:
        db.close()




def test_admin_can_provision_and_update_station():
    station_id = "NER-901"
    db = SessionLocal()
    try:
        existing = db.query(SensorStation).filter(SensorStation.station_id == station_id).first()
        if existing:
            db.delete(existing)
            db.commit()
    finally:
        db.close()

    created = client.post(
        "/api/sensors/stations",
        json={
            "station_id": station_id,
            "name": "Operational Test Station",
            "latitude": 25.6,
            "longitude": 91.9,
            "state": "Meghalaya",
            "district": "East Khasi Hills",
            "village": "Test Village",
            "elevation": 1200,
            "slope_angle": 32,
            "soil_type": "loamy",
            "vegetation_cover": 55,
        },
        headers=_admin_headers(),
    )
    assert created.status_code == 201, created.text
    assert created.json()["station_id"] == station_id

    updated = client.put(
        f"/api/sensors/stations/{station_id}",
        json={"slope_angle": 36, "is_active": False},
        headers=_admin_headers(),
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["is_active"] is False

    managed = client.get(
        "/api/sensors/stations/manage",
        headers=_admin_headers(),
    )
    assert managed.status_code == 200, managed.text
    managed_station = next(
        row for row in managed.json() if row["station_id"] == station_id
    )
    assert managed_station["is_active"] is False
    assert managed_station["slope_angle"] == 36

    public_stations = client.get("/api/sensors/stations")
    assert public_stations.status_code == 200
    assert station_id not in {row["station_id"] for row in public_stations.json()}

    reactivated = client.put(
        f"/api/sensors/stations/{station_id}",
        json={"is_active": True, "name": "Operational Test Station Updated"},
        headers=_admin_headers(),
    )
    assert reactivated.status_code == 200, reactivated.text
    assert reactivated.json()["is_active"] is True
    assert reactivated.json()["name"] == "Operational Test Station Updated"

    db = SessionLocal()
    try:
        station = db.query(SensorStation).filter(SensorStation.station_id == station_id).first()
        assert station is not None
        assert station.slope_angle == 36
        db.delete(station)
        db.commit()
    finally:
        db.close()


def test_sensor_ingestion_requires_valid_gateway_key(monkeypatch):
    monkeypatch.setenv("SENSOR_INGEST_ENABLED", "true")
    monkeypatch.setenv("SENSOR_INGEST_API_KEY", "operational-test-sensor-secret")

    response = client.post(
        "/api/sensors/stations/NER-001/readings",
        json={"rainfall_mm": 10, "soil_moisture": 40},
        headers={"X-GeoShield-Sensor-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_sensor_ingestion_persists_runs_ml_and_is_idempotent(monkeypatch):
    monkeypatch.setenv("SENSOR_INGEST_ENABLED", "true")
    monkeypatch.setenv("SENSOR_INGEST_API_KEY", "operational-test-sensor-secret")

    external_id = f"gateway-{uuid.uuid4().hex}"
    payload = {
        "external_id": external_id,
        "rainfall_mm": 110,
        "soil_moisture": 88,
        "soil_temperature": 24,
        "ground_displacement": 9,
        "tilt_angle_x": 3.0,
        "tilt_angle_y": 2.5,
        "pore_water_pressure": 75,
        "vibration_level": 20,
    }

    response = client.post(
        "/api/sensors/stations/NER-001/readings",
        json=payload,
        headers={"X-GeoShield-Sensor-Key": "operational-test-sensor-secret"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["status"] == "accepted"
    assert data["reading"]["source"] == "sensor_gateway"
    assert data["reading"]["external_id"] == external_id
    assert 0 <= data["risk_assessment"]["risk_score"] <= 100

    duplicate = client.post(
        "/api/sensors/stations/NER-001/readings",
        json=payload,
        headers={"X-GeoShield-Sensor-Key": "operational-test-sensor-secret"},
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["status"] == "duplicate"

    db = SessionLocal()
    try:
        reading = (
            db.query(SensorReading)
            .filter(SensorReading.external_id == external_id)
            .first()
        )
        assert reading is not None
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
