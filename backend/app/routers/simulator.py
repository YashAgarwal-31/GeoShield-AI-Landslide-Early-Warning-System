"""
Landslide Simulator API.

This module is for controlled demonstration/testing. Simulation endpoints are
restricted to operational roles and all generated alert messages are labelled
SIMULATION so they cannot be mistaken for field observations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional
import json
import random

from app.database import get_db
from app.models import SensorStation, SensorReading, RiskAssessment, Alert
from app.ai_engine.risk_predictor import get_predictor
from app.ai_engine.enhanced_predictor import get_enhanced_predictor
from app.auth import require_role

router = APIRouter(prefix="/api/simulate", tags=["simulate"])


def _to_core_risk_level(level: str, score: float) -> str:
    """Map enhanced-model labels to the four operational alert levels."""
    if level == "very_high":
        return "high"
    if level in {"low", "moderate", "high", "critical"}:
        return level
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "moderate"
    return "low"


class LandslideRequest(BaseModel):
    station_id: Optional[str] = Field(None, pattern=r"^NER-\d{3}$")
    intensity: Literal["low", "moderate", "high", "critical"] = "high"
    custom_rainfall: Optional[float] = Field(None, ge=0, le=500)
    custom_moisture: Optional[float] = Field(None, ge=0, le=100)


def _run_simulation(
    db: Session,
    station_id: Optional[str],
    intensity: str,
    custom_rainfall: Optional[float] = None,
    custom_moisture: Optional[float] = None,
) -> dict:
    """Run one labelled demonstration scenario."""

    if station_id:
        station = db.query(SensorStation).filter(
            SensorStation.station_id == station_id
        ).first()
        if not station:
            raise HTTPException(status_code=404, detail="Station not found")
    else:
        high_risk_stations = db.query(SensorStation).filter(
            SensorStation.slope_angle > 35
        ).all()
        if not high_risk_stations:
            high_risk_stations = db.query(SensorStation).all()
        if not high_risk_stations:
            raise HTTPException(status_code=409, detail="No stations available for simulation")
        station = random.choice(high_risk_stations)

    intensity_params = {
        "low": {"rainfall": 30, "moisture": 55, "displacement": 2, "tilt": 1},
        "moderate": {"rainfall": 60, "moisture": 70, "displacement": 5, "tilt": 2},
        "high": {"rainfall": 100, "moisture": 85, "displacement": 12, "tilt": 4},
        "critical": {"rainfall": 180, "moisture": 95, "displacement": 25, "tilt": 8},
    }
    params = intensity_params[intensity]

    rainfall = (
        custom_rainfall
        if custom_rainfall is not None
        else params["rainfall"] + random.uniform(-10, 10)
    )
    moisture = (
        custom_moisture
        if custom_moisture is not None
        else params["moisture"] + random.uniform(-5, 5)
    )

    reading = SensorReading(
        station_id=station.station_id,
        rainfall_mm=round(rainfall, 1),
        soil_moisture=round(moisture, 1),
        soil_temperature=round(random.uniform(22, 30), 1),
        ground_displacement=round(params["displacement"] + random.uniform(-2, 2), 2),
        tilt_angle_x=round(random.uniform(-params["tilt"], params["tilt"]), 2),
        tilt_angle_y=round(random.uniform(-params["tilt"], params["tilt"]), 2),
        pore_water_pressure=round(min(100, rainfall * 0.6 + random.uniform(5, 15)), 1),
        vibration_level=round(random.uniform(15, 40), 1),
        timestamp=datetime.utcnow(),
    )
    db.add(reading)

    predictor = get_predictor()
    sensor_data = {
        "rainfall_mm": rainfall,
        "soil_moisture": moisture,
        "ground_displacement": params["displacement"],
        "tilt_angle_x": reading.tilt_angle_x,
        "tilt_angle_y": reading.tilt_angle_y,
        "pore_water_pressure": reading.pore_water_pressure,
    }
    station_data = {
        "slope_angle": station.slope_angle,
        "elevation": station.elevation,
        "vegetation_cover": station.vegetation_cover,
    }
    result = predictor.predict_risk(sensor_data, station_data)

    try:
        enhanced = get_enhanced_predictor()
        enhanced_result = enhanced.predict(
            station.latitude,
            station.longitude,
            {
                "slope": station.slope_angle,
                "elevation": station.elevation,
                "rainfall_24hr": rainfall,
                "soil_moisture": moisture / 100,
                "ndvi": station.vegetation_cover / 100,
            },
        )
        result["risk_score"] = enhanced_result["risk_score"]
        result["risk_level"] = _to_core_risk_level(
            enhanced_result["risk_level"],
            float(enhanced_result["risk_score"]),
        )
        result["recommendation"] = predictor.recommendation_for_level(
            result["risk_level"],
            result.get("contributing_factors", []),
        )
    except Exception:
        # The baseline predictor remains the deterministic fallback for demo use.
        pass

    if intensity == "critical":
        result["risk_score"] = max(result["risk_score"], 90)
        result["risk_level"] = "critical"
        result["landslide_probability"] = max(result["landslide_probability"], 0.85)
    elif intensity == "high":
        result["risk_score"] = max(result["risk_score"], 70)
        if result["risk_level"] in {"low", "moderate"}:
            result["risk_level"] = "high"
        result["landslide_probability"] = max(result["landslide_probability"], 0.65)

    assessment = RiskAssessment(
        station_id=station.station_id,
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        landslide_probability=result["landslide_probability"],
        contributing_factors=json.dumps(result["contributing_factors"]),
        predicted_time_window=result["predicted_time_window_hours"],
        recommendation=result["recommendation"],
        model_version="v1.0-sim",
    )
    db.add(assessment)

    alert_created = None
    if result["risk_level"] in {"moderate", "high", "critical"}:
        severity_map = {
            "moderate": "Moderate Landslide Warning",
            "high": "High Landslide Risk Alert",
            "critical": "CRITICAL - Immediate Landslide Threat",
        }
        pop_affected = (
            random.randint(5000, 50000)
            if result["risk_level"] == "critical"
            else random.randint(500, 15000)
        )

        alert = Alert(
            station_id=station.station_id,
            risk_level=result["risk_level"],
            title=f"[SIMULATION] {severity_map[result['risk_level']]} - {station.name}",
            message=(
                f"SIMULATION: {result['risk_level'].upper()} landslide risk scenario at "
                f"{station.name}, {station.village}, {station.district}. "
                f"Rainfall: {rainfall:.0f}mm, Soil Moisture: {moisture:.0f}%, "
                f"Ground Displacement: {params['displacement']:.1f}mm. "
                f"{result['recommendation']}"
            ),
            status="active",
            affected_population=pop_affected,
            nearby_villages=json.dumps([station.village]),
            latitude=station.latitude,
            longitude=station.longitude,
        )
        db.add(alert)
        alert_created = alert

    db.commit()

    return {
        "status": "success",
        "simulation": {
            "station": {
                "id": station.station_id,
                "name": station.name,
                "state": station.state,
                "district": station.district,
            },
            "intensity": intensity,
            "sensor_reading": {
                "rainfall_mm": round(rainfall, 1),
                "soil_moisture": round(moisture, 1),
                "ground_displacement": round(params["displacement"], 1),
                "pore_pressure": reading.pore_water_pressure,
            },
        },
        "risk_assessment": {
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "landslide_probability": round(result["landslide_probability"], 3),
            "contributing_factors": result["contributing_factors"],
            "time_window_hours": result["predicted_time_window_hours"],
            "recommendation": result["recommendation"],
        },
        "alert": (
            {
                "id": alert_created.id,
                "title": alert_created.title,
                "affected_population": alert_created.affected_population,
            }
            if alert_created
            else None
        ),
    }


@router.post("/landslide")
def simulate_landslide(
    request: LandslideRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "field_officer", "district_admin")),
):
    """Run one controlled demonstration scenario."""
    return _run_simulation(
        db=db,
        station_id=request.station_id,
        intensity=request.intensity,
        custom_rainfall=request.custom_rainfall,
        custom_moisture=request.custom_moisture,
    )


@router.post("/batch")
def simulate_batch(
    count: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "field_officer", "district_admin")),
):
    """Run several controlled demonstration scenarios."""
    results = []
    stations = db.query(SensorStation).filter(SensorStation.slope_angle > 30).all()
    if not stations:
        stations = db.query(SensorStation).all()
    if not stations:
        raise HTTPException(status_code=409, detail="No stations available for simulation")

    intensities = ["moderate", "high", "critical", "high", "moderate"]
    for index in range(min(count, len(stations))):
        results.append(
            _run_simulation(
                db=db,
                station_id=stations[index % len(stations)].station_id,
                intensity=intensities[index % len(intensities)],
            )
        )

    return {
        "status": "success",
        "simulations_count": len(results),
        "results": results,
    }


@router.post("/reset")
def reset_simulations(
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    """
    Remove only data that can be identified as simulator-generated.

    Sensor readings are intentionally retained because the current schema does
    not tag their provenance. Deleting "recent" readings would risk removing
    legitimate data.
    """
    deleted_alerts = (
        db.query(Alert)
        .filter(Alert.message.like("SIMULATION:%"))
        .delete(synchronize_session=False)
    )
    deleted_assessments = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.model_version == "v1.0-sim")
        .delete(synchronize_session=False)
    )
    db.commit()

    return {
        "status": "success",
        "message": "Simulator-tagged alerts and assessments cleared; sensor readings retained.",
        "deleted_alerts": deleted_alerts,
        "deleted_assessments": deleted_assessments,
    }
