"""Post-Phase-4 stabilization regression tests."""
from datetime import datetime

from fastapi.testclient import TestClient

from app.auth import create_token
from app.database import SessionLocal
from app.main import app
from app.models import RiskAssessment
import app.routers.predict as predict_router
import app.routers.simulator as simulator_router


client = TestClient(app)


def _token(role: str = "admin") -> str:
    return create_token({
        "email": f"{role}@stabilization.test",
        "name": f"Stabilization {role}",
        "role": role,
    })


class _VeryHighPredictor:
    def predict(self, lat, lng, features=None):
        return {
            "risk_score": 65.0,
            "risk_level": "very_high",
            "confidence": 0.91,
            "source": "stabilization_fake",
            "feature_importance": None,
            "terrain_data": {
                "slope": 35.0,
                "elevation": 1000.0,
                "ndvi": 0.4,
                "soil_moisture": 0.6,
                "distance_to_road": 1000.0,
                "source": "test",
            },
            "latitude": lat,
            "longitude": lng,
        }


def test_dashboard_counts_only_latest_risk_per_station():
    db = SessionLocal()
    extra = RiskAssessment(
        station_id="NER-001",
        risk_level="critical",
        risk_score=99.0,
        landslide_probability=0.99,
        contributing_factors="[]",
        predicted_time_window=1,
        recommendation="test only",
        model_version="stabilization-test",
        timestamp=datetime.utcnow(),
    )
    try:
        db.add(extra)
        db.commit()
        db.refresh(extra)
        extra_id = extra.id
    finally:
        db.close()

    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    current_total = sum(data["risk_distribution"].values())
    assert current_total <= data["total_stations"]
    assert 0 <= data["average_risk_score"] <= 100

    db = SessionLocal()
    try:
        row = db.query(RiskAssessment).filter(RiskAssessment.id == extra_id).first()
        if row:
            db.delete(row)
            db.commit()
    finally:
        db.close()


def test_core_predict_normalizes_very_high(monkeypatch):
    monkeypatch.setattr(predict_router, "get_enhanced_predictor", lambda: _VeryHighPredictor())
    response = client.post("/api/predict", json={
        "latitude": 25.58,
        "longitude": 91.89,
    })
    assert response.status_code == 200
    assessment = response.json()["risk_assessment"]
    assert assessment["risk_level"] == "high"
    assert "continue monitoring" not in assessment["recommendation"].lower()


def test_simulator_normalizes_very_high_and_creates_alert(monkeypatch):
    monkeypatch.setattr(simulator_router, "get_enhanced_predictor", lambda: _VeryHighPredictor())
    token = _token("admin")
    response = client.post(
        "/api/simulate/landslide",
        json={"station_id": "NER-001", "intensity": "moderate"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["risk_assessment"]["risk_level"] == "high"
    assert data["alert"] is not None
    assert data["alert"]["title"].startswith("[SIMULATION]")

    client.post(
        "/api/simulate/reset",
        headers={"Authorization": f"Bearer {token}"},
    )
