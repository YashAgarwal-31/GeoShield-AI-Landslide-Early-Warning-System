"""
GeoShield API Test Suite
Automated tests for all 33+ API endpoints.
Run: cd backend && python -m pytest tests/test_api.py -v
"""
import pytest
import sys
import os

# Add parent to path so we can import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient

# Import app (this triggers database init)
from app.main import app

client = TestClient(app)


# ── Health & Auth ──────────────────────────────────────────────
class TestHealthAndAuth:
    def test_health_check(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"

    def test_login_valid(self):
        r = client.post("/api/auth/login", data={"email": "admin@geoshield.gov.in", "password": "admin123"})
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"

    def test_login_invalid(self):
        r = client.post("/api/auth/login", data={"email": "bad@email.com", "password": "wrong"})
        assert r.status_code == 401

    def test_login_missing_fields(self):
        r = client.post("/api/auth/login", data={"email": "admin@geoshield.gov.in"})
        assert r.status_code == 422  # Validation error


# ── Dashboard ──────────────────────────────────────────────────
class TestDashboard:
    def test_stats(self):
        r = client.get("/api/dashboard/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_stations"] == 20
        assert "active_alerts" in data
        assert "average_risk_score" in data

    def test_risk_heatmap(self):
        r = client.get("/api/dashboard/risk-heatmap")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 20
        assert all("lat" in p and "lng" in p and "risk_score" in p for p in data)

    def test_rainfall_trend(self):
        r = client.get("/api/dashboard/rainfall-trend")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 24  # At least 24 hourly points
        assert all("timestamp" in p and "avg_rainfall" in p for p in data)

    def test_risk_trend(self):
        r = client.get("/api/dashboard/risk-trend")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 24

    def test_state_summary(self):
        r = client.get("/api/dashboard/state-summary")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 8  # 8 NER states
        assert all("state" in s and "avg_risk_score" in s for s in data)


# ── Sensors ────────────────────────────────────────────────────
class TestSensors:
    def test_stations_list(self):
        r = client.get("/api/sensors/stations")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 20
        assert all("station_id" in s and "risk" in s for s in data)

    def test_station_detail(self):
        r = client.get("/api/sensors/stations/NER-001")
        assert r.status_code == 200
        data = r.json()
        assert "station" in data
        assert "readings" in data
        assert "risk_assessment" in data
        assert len(data["readings"]) > 0

    def test_station_not_found(self):
        r = client.get("/api/sensors/stations/NER-999")
        assert r.status_code == 404

    def test_station_history(self):
        r = client.get("/api/sensors/stations/NER-001/history?hours=24")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_latest_readings(self):
        r = client.get("/api/sensors/readings/latest")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 20


# ── Alerts ─────────────────────────────────────────────────────
class TestAlerts:
    def test_alerts_list(self):
        r = client.get("/api/alerts")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_alerts_active(self):
        r = client.get("/api/alerts/active")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_alerts_stats(self):
        r = client.get("/api/alerts/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total" in data and "active" in data

    def test_alerts_timeline(self):
        r = client.get("/api/alerts/timeline")
        assert r.status_code == 200
        data = r.json()
        assert "timeline" in data
        assert "summary" in data

    def test_alerts_history(self):
        r = client.get("/api/alerts/history?days=30")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least one day of history


# ── Predict ────────────────────────────────────────────────────
class TestPredict:
    def test_predict_valid(self):
        r = client.post("/api/predict", json={
            "latitude": 27.35, "longitude": 88.62, "slope": 45
        })
        assert r.status_code == 200
        data = r.json()
        assert "risk_assessment" in data
        assert 0 <= data["risk_assessment"]["risk_score"] <= 100
        assert data["risk_assessment"]["risk_level"] in ["low", "moderate", "high", "critical"]

    def test_predict_risk_level_consistent(self):
        """Risk level must match risk score range."""
        r = client.post("/api/predict", json={
            "latitude": 27.35, "longitude": 88.62, "slope": 55
        })
        data = r.json()
        score = data["risk_assessment"]["risk_score"]
        level = data["risk_assessment"]["risk_level"]
        if score < 25:
            assert level == "low"
        elif score < 50:
            assert level == "moderate"
        elif score < 75:
            assert level == "high"
        else:
            assert level == "critical"

    def test_predict_recommendation_matches_final_risk_level(self):
        """Enhanced risk level and operational guidance must never conflict."""
        r = client.post("/api/predict", json={
            "latitude": 27.35, "longitude": 88.62, "slope": 55
        })
        assert r.status_code == 200
        assessment = r.json()["risk_assessment"]
        recommendation = assessment["recommendation"].lower()

        if assessment["risk_level"] in {"high", "critical"}:
            assert "normal operations" not in recommendation
            assert "no immediate action required" not in recommendation

    def test_predict_invalid_coords(self):
        r = client.post("/api/predict", json={"latitude": 999, "longitude": 88})
        assert r.status_code == 422  # Validation error


# ── Simulate ───────────────────────────────────────────────────
class TestSimulate:
    def _get_token(self):
        r = client.post("/api/auth/login", data={"email": "admin@geoshield.gov.in", "password": "admin123"})
        return r.json()["token"]

    def test_simulate_with_auth(self):
        token = self._get_token()
        r = client.post("/api/simulate/landslide", json={
            "station_id": "NER-012", "intensity": "critical"
        }, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        assert data["risk_assessment"]["risk_score"] >= 75  # Critical should be high
        assert data["risk_assessment"]["risk_level"] == "critical"


# ── Export ─────────────────────────────────────────────────────
class TestExport:
    def test_geojson(self):
        r = client.get("/api/export/geojson")
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 20

    def test_csv(self):
        r = client.get("/api/export/csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

    def test_risk_zones(self):
        r = client.get("/api/export/risk-zones")
        assert r.status_code == 200
        data = r.json()
        assert "features" in data


# ── Weather ────────────────────────────────────────────────────
class TestWeather:
    def test_weather_data(self):
        r = client.get("/api/weather/NER-001")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "temperature" in data["data"]
        assert data["source"]["mode"] in {"live", "cached", "fallback"}
        assert isinstance(data["source"]["is_stale"], bool)

    def test_weather_forecast(self):
        r = client.get("/api/weather/NER-001/forecast?hours=48")
        assert r.status_code == 200
        data = r.json()
        assert data["series_kind"] in {"forecast", "demo_history"}
        assert len(data["forecast"]) > 0
        assert "source" in data


# ── Satellite ──────────────────────────────────────────────────
class TestSatellite:
    def test_satellite_data(self):
        r = client.get("/api/satellite/data")
        assert r.status_code == 200
        data = r.json()
        assert data["total_stations"] == 20
        assert data["source"]["mode"] == "cached"
        assert isinstance(data["source"]["age_seconds"], int)

    def test_satellite_summary(self):
        r = client.get("/api/satellite/summary")
        assert r.status_code == 200
        data = r.json()
        assert "elevation" in data
        assert "source" in data

    def test_satellite_risk_zones(self):
        r = client.get("/api/satellite/risk-zones")
        assert r.status_code == 200
        data = r.json()
        assert len(data["risk_zones"]) == 20
        assert data["source"]["mode"] == "cached"


# ── Roads & Villages ───────────────────────────────────────────
class TestInfrastructure:
    def test_roads(self):
        r = client.get("/api/roads")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 8

    def test_villages(self):
        r = client.get("/api/villages")
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 18


# ── Frontend ───────────────────────────────────────────────────
import os
dist_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
_has_dist = os.path.isdir(dist_path)

@pytest.mark.skipif(not _has_dist, reason="frontend/dist/ not built")
class TestFrontend:
    def test_serves_index(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_spa_routes(self):
        for route in ["/map", "/alerts", "/simulator", "/satellite", "/flood", "/demo"]:
            r = client.get(route)
            assert r.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
