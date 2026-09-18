from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import hmac
import json
import os

from app.database import get_db
from app.models import SensorStation, SensorReading, RiskAssessment, Alert
from app.schemas import (
    SensorReadingIngestRequest,
    SensorStationCreateRequest,
    SensorStationUpdateRequest,
)
from app.ai_engine.risk_predictor import get_predictor
from app.auth import require_role
from app.realtime import alert_manager

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _require_sensor_key(
    sensor_key: str | None = Header(default=None, alias="X-GeoShield-Sensor-Key"),
) -> None:
    if not _env_bool("SENSOR_INGEST_ENABLED", False):
        raise HTTPException(status_code=503, detail="Sensor ingestion is disabled")

    expected = os.getenv("SENSOR_INGEST_API_KEY", "")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Sensor ingestion is not configured",
        )
    if sensor_key is None or not hmac.compare_digest(sensor_key, expected):
        raise HTTPException(status_code=401, detail="Invalid sensor ingestion key")


def _parse_observed_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="observed_at must be ISO-8601") from exc

    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


@router.post("/stations", status_code=201)
def create_station(
    payload: SensorStationCreateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin")),
):
    existing = (
        db.query(SensorStation)
        .filter(SensorStation.station_id == payload.station_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Station already exists")

    station = SensorStation(
        station_id=payload.station_id,
        name=payload.name.strip(),
        latitude=payload.latitude,
        longitude=payload.longitude,
        state=payload.state.strip(),
        district=payload.district.strip(),
        village=payload.village.strip(),
        elevation=payload.elevation,
        slope_angle=payload.slope_angle,
        soil_type=payload.soil_type.strip() or "unknown",
        vegetation_cover=payload.vegetation_cover,
        is_active=True,
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    return {
        "id": station.id,
        "station_id": station.station_id,
        "name": station.name,
        "is_active": station.is_active,
    }


@router.put("/stations/{station_id}")
def update_station(
    station_id: str,
    payload: SensorStationUpdateRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(require_role("admin", "district_admin")),
):
    station = (
        db.query(SensorStation)
        .filter(SensorStation.station_id == station_id)
        .first()
    )
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if isinstance(value, str):
            value = value.strip()
        setattr(station, field, value)

    db.commit()
    db.refresh(station)
    return {
        "station_id": station.station_id,
        "name": station.name,
        "is_active": station.is_active,
        "state": station.state,
        "district": station.district,
    }


@router.get("/stations")
def get_stations(db: Session = Depends(get_db)):
    # Subquery: latest reading per station (eliminates N+1)
    latest_reading_sq = db.query(
        SensorReading.station_id,
        SensorReading.rainfall_mm,
        SensorReading.soil_moisture,
        SensorReading.ground_displacement,
        SensorReading.source,
        SensorReading.external_id,
        SensorReading.timestamp,
        func.row_number().over(
            partition_by=SensorReading.station_id,
            order_by=SensorReading.timestamp.desc()
        ).label('rn')
    ).subquery()
    latest_readings = {r.station_id: r for r in db.query(latest_reading_sq).filter(latest_reading_sq.c.rn == 1).all()}

    # Subquery: latest risk assessment per station
    latest_risk_sq = db.query(
        RiskAssessment.station_id,
        RiskAssessment.risk_level,
        RiskAssessment.risk_score,
        RiskAssessment.landslide_probability,
        func.row_number().over(
            partition_by=RiskAssessment.station_id,
            order_by=RiskAssessment.timestamp.desc()
        ).label('rn')
    ).subquery()
    latest_risks = {r.station_id: r for r in db.query(latest_risk_sq).filter(latest_risk_sq.c.rn == 1).all()}

    stations = db.query(SensorStation).filter(SensorStation.is_active == True).all()
    result = []
    for s in stations:
        latest = latest_readings.get(s.station_id)
        risk = latest_risks.get(s.station_id)
        result.append({
            "id": s.id,
            "station_id": s.station_id,
            "name": s.name,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "state": s.state,
            "district": s.district,
            "village": s.village,
            "elevation": s.elevation,
            "slope_angle": s.slope_angle,
            "soil_type": s.soil_type,
            "vegetation_cover": s.vegetation_cover,
            "is_active": s.is_active,
            "latest_reading": {
                "rainfall_mm": latest.rainfall_mm if latest else 0,
                "soil_moisture": latest.soil_moisture if latest else 0,
                "ground_displacement": latest.ground_displacement if latest else 0,
                "timestamp": latest.timestamp.isoformat() if latest and latest.timestamp else None,
            "source": latest.source if latest else None,
            } if latest else None,
            "risk": {
                "level": risk.risk_level if risk else "low",
                "score": risk.risk_score if risk else 0,
                "probability": risk.landslide_probability if risk else 0,
            } if risk else None,
        })
    return result


@router.get("/stations/{station_id}")
def get_station(station_id: str, db: Session = Depends(get_db)):
    station = db.query(SensorStation).filter(SensorStation.station_id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    latest_readings = db.query(SensorReading).filter(
        SensorReading.station_id == station_id
    ).order_by(desc(SensorReading.timestamp)).limit(168).all()

    risk = db.query(RiskAssessment).filter(
        RiskAssessment.station_id == station_id
    ).order_by(desc(RiskAssessment.timestamp)).first()

    return {
        "station": {
            "station_id": station.station_id,
            "name": station.name,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "state": station.state,
            "district": station.district,
            "village": station.village,
            "elevation": station.elevation,
            "slope_angle": station.slope_angle,
            "soil_type": station.soil_type,
            "vegetation_cover": station.vegetation_cover,
        },
        "readings": [{
            "rainfall_mm": r.rainfall_mm,
            "soil_moisture": r.soil_moisture,
            "soil_temperature": r.soil_temperature,
            "ground_displacement": r.ground_displacement,
            "tilt_angle_x": r.tilt_angle_x,
            "tilt_angle_y": r.tilt_angle_y,
            "pore_water_pressure": r.pore_water_pressure,
            "vibration_level": r.vibration_level,
            "source": r.source,
            "external_id": r.external_id,
            "timestamp": r.timestamp.isoformat(),
        } for r in reversed(latest_readings)],
        "risk_assessment": {
            "risk_level": risk.risk_level if risk else "low",
            "risk_score": risk.risk_score if risk else 0,
            "landslide_probability": risk.landslide_probability if risk else 0,
            "contributing_factors": risk.contributing_factors if risk else '[]',
            "predicted_time_window_hours": risk.predicted_time_window if risk else 168,
            "recommendation": risk.recommendation if risk else 'Continue monitoring.',
            "timestamp": risk.timestamp.isoformat() if risk and risk.timestamp else None,
        } if risk else None,
    }


@router.get("/stations/{station_id}/history")
def get_station_history(
    station_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    readings = db.query(SensorReading).filter(
        SensorReading.station_id == station_id,
        SensorReading.timestamp >= since
    ).order_by(SensorReading.timestamp).all()

    return [{
        "rainfall_mm": r.rainfall_mm,
        "soil_moisture": r.soil_moisture,
        "ground_displacement": r.ground_displacement,
        "tilt_angle_x": r.tilt_angle_x,
        "pore_water_pressure": r.pore_water_pressure,
        "timestamp": r.timestamp.isoformat(),
    } for r in readings]


@router.get("/readings/latest")
def get_all_latest_readings(db: Session = Depends(get_db)):
    subquery = db.query(
        SensorReading.station_id,
        func.max(SensorReading.timestamp).label("max_time")
    ).group_by(SensorReading.station_id).subquery()

    readings = db.query(SensorReading).join(
        subquery,
        (SensorReading.station_id == subquery.c.station_id) &
        (SensorReading.timestamp == subquery.c.max_time)
    ).all()

    return [{
        "station_id": r.station_id,
        "rainfall_mm": r.rainfall_mm,
        "soil_moisture": r.soil_moisture,
        "ground_displacement": r.ground_displacement,
        "source": r.source,
        "external_id": r.external_id,
        "timestamp": r.timestamp.isoformat(),
    } for r in readings]


@router.post("/stations/{station_id}/readings", status_code=201)
async def ingest_sensor_reading(
    station_id: str,
    payload: SensorReadingIngestRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_require_sensor_key),
):
    """Persist a gateway/sensor reading, run risk inference, and create an alert when needed."""
    station = (
        db.query(SensorStation)
        .filter(SensorStation.station_id == station_id)
        .first()
    )
    if not station or not station.is_active:
        raise HTTPException(status_code=404, detail="Active station not found")

    if payload.external_id:
        existing = (
            db.query(SensorReading)
            .filter(SensorReading.external_id == payload.external_id)
            .first()
        )
        if existing:
            return {
                "status": "duplicate",
                "reading_id": existing.id,
                "external_id": existing.external_id,
            }

    observed_at = _parse_observed_at(payload.observed_at)
    reading = SensorReading(
        station_id=station.station_id,
        rainfall_mm=payload.rainfall_mm,
        soil_moisture=payload.soil_moisture,
        soil_temperature=payload.soil_temperature,
        ground_displacement=payload.ground_displacement,
        tilt_angle_x=payload.tilt_angle_x,
        tilt_angle_y=payload.tilt_angle_y,
        pore_water_pressure=payload.pore_water_pressure,
        vibration_level=payload.vibration_level,
        source="sensor_gateway",
        external_id=payload.external_id,
        timestamp=observed_at,
    )
    db.add(reading)
    db.flush()

    predictor = get_predictor()
    result = predictor.predict_risk(
        {
            "rainfall_mm": payload.rainfall_mm,
            "soil_moisture": payload.soil_moisture,
            "ground_displacement": payload.ground_displacement,
            "tilt_angle_x": payload.tilt_angle_x,
            "tilt_angle_y": payload.tilt_angle_y,
            "pore_water_pressure": payload.pore_water_pressure,
        },
        {
            "slope_angle": station.slope_angle,
            "elevation": station.elevation,
            "vegetation_cover": station.vegetation_cover,
        },
    )

    assessment = RiskAssessment(
        station_id=station.station_id,
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        landslide_probability=result["landslide_probability"],
        contributing_factors=json.dumps(result["contributing_factors"]),
        predicted_time_window=result["predicted_time_window_hours"],
        recommendation=result["recommendation"],
        model_version="v2.1-sensor-ingest",
        timestamp=observed_at,
    )
    db.add(assessment)

    alert = None
    if result["risk_level"] in {"moderate", "high", "critical"}:
        alert = Alert(
            station_id=station.station_id,
            risk_level=result["risk_level"],
            title=f"[SENSOR] {result['risk_level'].upper()} landslide risk - {station.name}",
            message=(
                f"Sensor-ingested observation at {station.name}, {station.district}. "
                f"Rainfall={payload.rainfall_mm:.1f} mm, "
                f"soil moisture={payload.soil_moisture:.1f}%, "
                f"ground displacement={payload.ground_displacement:.2f} mm. "
                f"{result['recommendation']}"
            ),
            status="active",
            affected_population=0,
            nearby_villages=json.dumps([station.village] if station.village else []),
            latitude=station.latitude,
            longitude=station.longitude,
        )
        db.add(alert)

    db.commit()
    db.refresh(reading)
    if alert is not None:
        db.refresh(alert)
        await alert_manager.publish_alert(
            event_type="alert.created",
            alert=alert,
            district=station.district,
        )

    await alert_manager.broadcast(
        {
            "type": "sensor.reading",
            "station_id": station.station_id,
            "district": station.district,
            "reading": {
                "id": reading.id,
                "source": reading.source,
                "external_id": reading.external_id,
                "observed_at": reading.timestamp.isoformat() if reading.timestamp else None,
            },
            "risk_assessment": {
                "risk_level": result["risk_level"],
                "risk_score": result["risk_score"],
                "landslide_probability": result["landslide_probability"],
            },
        },
        district=station.district,
    )

    return {
        "status": "accepted",
        "reading": {
            "id": reading.id,
            "station_id": reading.station_id,
            "source": reading.source,
            "external_id": reading.external_id,
            "observed_at": reading.timestamp.isoformat() if reading.timestamp else None,
        },
        "risk_assessment": {
            "risk_level": result["risk_level"],
            "risk_score": result["risk_score"],
            "landslide_probability": result["landslide_probability"],
            "contributing_factors": result["contributing_factors"],
            "time_window_hours": result["predicted_time_window_hours"],
            "recommendation": result["recommendation"],
        },
        "alert": (
            {"id": alert.id, "risk_level": alert.risk_level, "title": alert.title}
            if alert is not None
            else None
        ),
    }
