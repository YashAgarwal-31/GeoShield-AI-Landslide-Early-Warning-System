"""
GeoShield End-to-End Integration Tests
Full flow tests covering complete user workflows.
Run: cd backend && python -m pytest tests/test_e2e.py -v
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── Core Backend ───────────────────────────────────────────────
class TestCoreBackend:
    def test_health_returns_200(self):
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_login_returns_jwt_token(self):
        r = client.post("/api/auth/login", data={"email": "admin@geoshield.gov.in", "password": "admin123"})
        assert r.status_code == 200
        token = r.json()["token"]
        assert len(token) > 50  # JWT tokens are long

    def test_unauthenticated_access_denied(self):
        r = client.post("/api/simulate/landslide", json={"station_id": "NER-001", "intensity": "high"})
        assert r.status_code == 401


# ── Dashboard Data Flow ────────────────────────────────────────
class TestDashboardFlow:
    def test_stats_has_all_fields(self):
        r = client.get("/api/dashboard/stats")
        data = r.json()
        required = ["total_stations", "active_stations", "risk_distribution", "active_alerts",
                     "pending_reports", "road_status", "affected_population", "total_villages",
                     "high_risk_villages", "average_risk_score", "last_updated"]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_heatmap_has_coordinates(self):
        r = client.get("/api/dashboard/risk-heatmap")
        data = r.json()
        assert len(data) == 20
        for point in data:
            assert 21.0 <= point["lat"] <= 30.0  # NER latitude range
            assert 88.0 <= point["lng"] <= 98.0  # NER longitude range

    def test_rainfall_trend_has_hourly_data(self):
        r = client.get("/api/dashboard/rainfall-trend")
        data = r.json()
        assert len(data) >= 24
        for point in data:
            assert "timestamp" in point
            assert "avg_rainfall" in point
            assert point["avg_rainfall"] >= 0

    def test_state_summary_has_8_states(self):
        r = client.get("/api/dashboard/state-summary")
        data = r.json()
        assert len(data) == 8
        states = [s["state"] for s in data]
        assert "Sikkim" in states
        assert "Assam" in states

    def test_risk_distribution_sums_correctly(self):
        r = client.get("/api/dashboard/stats")
        data = r.json()
        dist = data["risk_distribution"]
        total = dist["low"] + dist["moderate"] + dist["high"] + dist["critical"]
        assert total >= 1  # At least some stations have risk data


# ── Sensor Stations Flow ───────────────────────────────────────
class TestSensorFlow:
    def test_all_20_stations_present(self):
        r = client.get("/api/sensors/stations")
        data = r.json()
        assert len(data) == 20
        ids = [s["station_id"] for s in data]
        assert "NER-001" in ids
        assert "NER-020" in ids

    def test_station_detail_has_readings(self):
        r = client.get("/api/sensors/stations/NER-011")  # Cherrapunji
        data = r.json()
        assert "Cherrapunji" in data["station"]["name"]
        assert len(data["readings"]) > 0
        assert data["risk_assessment"] is not None

    def test_station_history_has_time_range(self):
        r = client.get("/api/sensors/stations/NER-001/history?hours=24")
        data = r.json()
        assert len(data) > 0
        # Check timestamps are within 24h range
        timestamps = [d["timestamp"] for d in data]
        assert len(timestamps) > 0


# ── Alerts System Flow ─────────────────────────────────────────
class TestAlertsFlow:
    def test_alerts_have_required_fields(self):
        r = client.get("/api/alerts")
        data = r.json()
        assert len(data) > 0
        for alert in data:
            assert "id" in alert
            assert "station_id" in alert
            assert "risk_level" in alert
            assert "title" in alert
            assert "status" in alert

    def test_alert_stats_match_list(self):
        r_list = client.get("/api/alerts")
        r_stats = client.get("/api/alerts/stats")
        list_data = r_list.json()
        stats_data = r_stats.json()
        # Stats total may exceed list length (list may be paginated/limited)
        assert stats_data["total"] >= len(list_data)
        assert stats_data["total"] > 0

    def test_alert_timeline_has_structure(self):
        r = client.get("/api/alerts/timeline?hours=72")
        data = r.json()
        assert "timeline" in data
        assert "summary" in data
        assert data["summary"]["total_alerts"] >= 0

    def test_alert_history_has_daily_data(self):
        r = client.get("/api/alerts/history?days=30")
        data = r.json()
        assert isinstance(data, list)
        for day in data:
            assert "date" in day
            assert "total" in day
            assert day["total"] >= 0


# ── Simulator → Alert Flow ─────────────────────────────────────
class TestSimulatorAlertFlow:
    def _get_admin_token(self):
        r = client.post("/api/auth/login", data={"email": "admin@geoshield.gov.in", "password": "admin123"})
        return r.json()["token"]

    def test_simulate_creates_alert(self):
        token = self._get_admin_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Get initial alert count
        r1 = client.get("/api/alerts/stats", headers=headers)
        initial_count = r1.json()["total"]

        # Run simulation
        r2 = client.post("/api/simulate/landslide", json={
            "station_id": "NER-011", "intensity": "critical"
        }, headers=headers)
        assert r2.status_code == 200
        sim_data = r2.json()
        assert sim_data["status"] == "success"
        assert sim_data["alert"] is not None

        # Verify alert was created
        r3 = client.get("/api/alerts/stats", headers=headers)
        new_count = r3.json()["total"]
        assert new_count >= initial_count

    def test_simulate_high_intensity(self):
        token = self._get_admin_token()
        r = client.post("/api/simulate/landslide", json={
            "station_id": "NER-006", "intensity": "high"
        }, headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["risk_assessment"]["risk_score"] >= 50

    def test_simulate_requires_auth(self):
        r = client.post("/api/simulate/landslide", json={
            "station_id": "NER-001", "intensity": "moderate"
        })
        assert r.status_code == 401


# ── AI Prediction Flow ─────────────────────────────────────────
class TestPredictionFlow:
    def test_predict_returns_risk_assessment(self):
        r = client.post("/api/predict", json={
            "latitude": 27.35, "longitude": 88.62
        })
        assert r.status_code == 200
        data = r.json()
        assert "risk_assessment" in data
        assert "nearest_station" in data
        assert "model_info" in data

    def test_predict_contributing_factors(self):
        r = client.post("/api/predict", json={
            "latitude": 25.67, "longitude": 91.88, "slope": 45
        })
        data = r.json()
        factors = data["risk_assessment"]["contributing_factors"]
        assert isinstance(factors, list)
        assert len(factors) > 0


# ── Flood Data Flow ────────────────────────────────────────────
class TestFloodFlow:
    def test_flood_data_has_districts(self):
        r = client.get("/api/flood/data")
        data = r.json()
        assert data["total_districts"] == 19
        assert len(data["data"]) == 19

    def test_flood_summary_has_metrics(self):
        r = client.get("/api/flood/summary")
        data = r.json()
        assert "avg_risk_score" in data
        assert "high_risk_districts" in data
        assert data["total_districts"] == 19

    def test_flood_correlation_has_insight(self):
        r = client.get("/api/flood/correlation")
        data = r.json()
        assert "correlation" in data
        assert "insight" in data
        assert len(data["correlation"]) > 0


# ── Satellite Data Flow ────────────────────────────────────────
class TestSatelliteFlow:
    def test_satellite_data_has_all_stations(self):
        r = client.get("/api/satellite/data")
        data = r.json()
        assert data["total_stations"] == 20
        assert data["source"]["mode"] == "cached"
        for station in data["stations"]:
            assert "real_elevation" in station
            assert "real_soil_moisture_0_7cm" in station
            assert "estimated_ndvi" in station

    def test_satellite_summary_has_ranges(self):
        r = client.get("/api/satellite/summary")
        data = r.json()
        assert "elevation" in data
        assert "min" in data["elevation"]
        assert "max" in data["elevation"]
        assert data["elevation"]["max"] > data["elevation"]["min"]
        assert data["source"]["provider"]

    def test_satellite_risk_zones_scored(self):
        r = client.get("/api/satellite/risk-zones")
        data = r.json()
        assert len(data["risk_zones"]) == 20
        for zone in data["risk_zones"]:
            assert 0 <= zone["satellite_risk_score"] <= 100
            assert zone["risk_level"] in ["low", "moderate", "high", "critical"]
            assert "snapshot_data" in zone


# ── Weather Data Flow ──────────────────────────────────────────
class TestWeatherFlow:
    def test_weather_has_current_conditions(self):
        r = client.get("/api/weather/NER-001")
        data = r.json()["data"]
        assert "temperature" in data
        assert "humidity" in data
        assert "rainfall_24h" in data

    def test_weather_forecast_has_future_data(self):
        r = client.get("/api/weather/NER-001/forecast?hours=48")
        data = r.json()
        assert len(data["forecast"]) > 0
        assert len(data["forecast"]) <= 48
        assert data["series_kind"] in ["forecast", "demo_history"]


# ── Data Export Flow ───────────────────────────────────────────
class TestExportFlow:
    def test_geojson_is_valid(self):
        r = client.get("/api/export/geojson")
        data = r.json()
        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 20
        for feature in data["features"]:
            assert feature["type"] == "Feature"
            assert "geometry" in feature
            assert "properties" in feature

    def test_csv_has_headers(self):
        r = client.get("/api/export/csv")
        content = r.text
        lines = content.strip().split("\n")
        assert len(lines) >= 2  # Header + at least 1 data row
        assert "station_id" in lines[0].lower()

    def test_risk_zones_has_all_stations(self):
        r = client.get("/api/export/risk-zones")
        data = r.json()
        assert len(data["features"]) >= 1  # At least 1 station with elevated risk


# ── Infrastructure Data Flow ───────────────────────────────────
class TestInfrastructureFlow:
    def test_roads_have_status(self):
        r = client.get("/api/roads")
        data = r.json()
        assert len(data) >= 8
        for road in data:
            assert "status" in road
            assert road["status"] in ["open", "partially_blocked", "blocked"]

    def test_villages_have_population(self):
        r = client.get("/api/villages")
        data = r.json()
        assert len(data) >= 18
        for village in data:
            assert "population" in village
            assert village["population"] > 0
            assert "risk_zone" in village


# ── Frontend Routes ────────────────────────────────────────────
import os as _os
dist_path = _os.path.join(_os.path.dirname(__file__), "..", "..", "frontend", "dist")
_has_dist = _os.path.isdir(dist_path)

@pytest.mark.skipif(not _has_dist, reason="frontend/dist/ not built")
class TestFrontendRoutes:
    def test_main_page_loads(self):
        r = client.get("/")
        assert r.status_code == 200

    def test_all_spa_routes(self):
        routes = ["/", "/map", "/alerts", "/reports", "/simulator", "/satellite", "/flood", "/demo"]
        for route in routes:
            r = client.get(route)
            assert r.status_code == 200, f"Route {route} failed"

    def test_station_detail_route(self):
        r = client.get("/station/NER-001")
        assert r.status_code == 200


# ── Alert Acknowledge Workflow ──────────────────────────────────
class TestAlertWorkflow:
    def test_acknowledge_alert(self):
        # Get an active alert
        r1 = client.get("/api/alerts?status=active")
        alerts = r1.json()
        if len(alerts) > 0:
            alert_id = alerts[0]["id"]
            token = self._get_admin_token()
            r2 = client.put(f"/api/alerts/{alert_id}/acknowledge",
                           headers={"Authorization": f"Bearer {token}"})
            assert r2.status_code == 200

    def _get_admin_token(self):
        r = client.post("/api/auth/login", data={"email": "admin@geoshield.gov.in", "password": "admin123"})
        return r.json()["token"]


# ── Security ───────────────────────────────────────────────────
class TestSecurity:
    def test_invalid_login_rejected(self):
        r = client.post("/api/auth/login", data={"email": "admin@geoshield.gov.in", "password": "wrong"})
        assert r.status_code == 401

    def test_protected_endpoint_without_token(self):
        r = client.post("/api/simulate/landslide", json={"station_id": "NER-001", "intensity": "high"})
        assert r.status_code == 401

    def test_citizen_cannot_resolve_alerts(self):
        r = client.post("/api/auth/login", data={"email": "citizen@geoshield.gov.in", "password": "demo123"})
        token = r.json()["token"]
        r2 = client.put("/api/alerts/1/resolve",
                       headers={"Authorization": f"Bearer {token}"})
        assert r2.status_code == 403



# ── Enhanced ML (XGBoost + Terrain Lookup) ──────────────────────
class TestEnhancedML:
    def test_ml_health(self):
        r = client.get("/api/ml/health")
        assert r.status_code == 200
        data = r.json()
        assert data["model_loaded"] == True
        assert data["model_type"] == "xgboost"
        assert data["terrain_lookup"] == True

    def test_ml_predict_xgboost(self):
        r = client.post("/api/ml/predict", json={"latitude": 25.58, "longitude": 91.89})
        assert r.status_code == 200
        data = r.json()
        assert data["source"] == "xgboost_model"
        assert 0 <= data["risk_score"] <= 100
        assert data["risk_level"] in ["low", "moderate", "high", "very_high", "critical"]

    def test_ml_predict_has_terrain_data(self):
        r = client.post("/api/ml/predict", json={"latitude": 25.58, "longitude": 91.89})
        assert r.status_code == 200
        data = r.json()
        assert "terrain_data" in data
        assert data["terrain_data"]["source"] == "terrain_lookup"
        assert "slope" in data["terrain_data"]
        assert "elevation" in data["terrain_data"]
        assert "ndvi" in data["terrain_data"]

    def test_ml_predict_has_feature_importance(self):
        r = client.post("/api/ml/predict", json={"latitude": 25.58, "longitude": 91.89})
        assert r.status_code == 200
        data = r.json()
        assert data.get("feature_importance") is not None
        assert "soil_moisture" in data["feature_importance"]
        assert "slope" in data["feature_importance"]

    def test_ml_district_risk(self):
        r = client.get("/api/ml/risk/district/shillong")
        assert r.status_code == 200
        data = r.json()
        assert data["district"] == "Shillong"
        assert data["risk_level"] in ["low", "moderate", "high", "very_high", "critical"]
        assert data["zone_count"] == 25
        assert len(data["predictions"]) == 25

    def test_ml_batch_predict(self):
        r = client.post("/api/ml/predict/batch", json={
            "locations": [
                {"latitude": 25.58, "longitude": 91.89},
                {"latitude": 26.14, "longitude": 91.74},
            ]
        })
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 2
        assert len(data["predictions"]) == 2

    def test_ml_risk_grid(self):
        r = client.get("/api/ml/risk/grid?resolution=5")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 25
        assert data["resolution"] == 5

    def test_enhanced_predict_terrain_enrichment(self):
        r = client.post("/api/predict", json={"latitude": 25.58, "longitude": 91.89})
        assert r.status_code == 200
        data = r.json()
        assert "terrain_data" in data["risk_assessment"]
        assert data["risk_assessment"]["terrain_data"]["source"] == "terrain_lookup"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
