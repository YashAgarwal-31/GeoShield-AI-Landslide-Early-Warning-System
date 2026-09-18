from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models import SensorStation, SensorReading, RiskAssessment

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.get("/stations")
def get_stations(db: Session = Depends(get_db)):
    # Subquery: latest reading per station (eliminates N+1)
    latest_reading_sq = db.query(
        SensorReading.station_id,
        SensorReading.rainfall_mm,
        SensorReading.soil_moisture,
        SensorReading.ground_displacement,
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
        "timestamp": r.timestamp.isoformat(),
    } for r in readings]
