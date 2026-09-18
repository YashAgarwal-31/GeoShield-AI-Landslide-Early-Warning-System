"""Phase 4 security/config regression tests."""
import os
import subprocess
import sys
import uuid

from fastapi.testclient import TestClient

from app.auth import create_token
from app.database import SessionLocal
from app.main import app
from app.models import Alert


client = TestClient(app)


def _token_for(role: str) -> str:
    return create_token(
        {
            "email": f"{role}@phase4.test",
            "name": f"Phase4 {role}",
            "role": role,
        }
    )


def test_citizen_cannot_run_simulator():
    token = _token_for("citizen")
    response = client.post(
        "/api/simulate/landslide",
        json={"station_id": "NER-001", "intensity": "high"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_model_training_requires_authentication():
    response = client.post("/api/ml/train")
    assert response.status_code == 401


def test_model_training_disabled_by_default_even_for_admin(monkeypatch):
    monkeypatch.delenv("MODEL_TRAINING_ENABLED", raising=False)
    token = _token_for("admin")
    response = client.post(
        "/api/ml/train",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_reset_preserves_non_simulation_alert():
    marker = f"phase4-preserve-{uuid.uuid4()}"
    db = SessionLocal()
    try:
        alert = Alert(
            station_id="NER-001",
            risk_level="low",
            title=marker,
            message="Non-simulation alert used by the Phase 4 regression test.",
            status="active",
            affected_population=0,
            nearby_villages="[]",
            latitude=27.0,
            longitude=91.0,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        alert_id = alert.id
    finally:
        db.close()

    token = _token_for("admin")
    response = client.post(
        "/api/simulate/reset",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    db = SessionLocal()
    try:
        preserved = db.query(Alert).filter(Alert.id == alert_id).first()
        assert preserved is not None
        db.delete(preserved)
        db.commit()
    finally:
        db.close()


def test_security_headers_present():
    response = client.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"


def test_untrusted_origin_not_echoed():
    response = client.options(
        "/api/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") != "https://untrusted.example"


def test_production_start_rejects_missing_jwt_secret():
    env = os.environ.copy()
    env["APP_ENV"] = "production"
    env.pop("JWT_SECRET", None)
    result = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode != 0
    assert "JWT_SECRET" in (result.stdout + result.stderr)
