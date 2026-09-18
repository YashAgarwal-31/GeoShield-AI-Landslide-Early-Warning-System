from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from sqlalchemy.orm import subqueryload
from datetime import datetime, timedelta
from app.database import get_db
from app.models import (
    SensorStation, SensorReading, RiskAssessment, Alert,
    CitizenReport, RoadStatus, Village, WeatherData
)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _get_latest_risk_subquery(db: Session):
    """Subquery to get latest risk assessment per station."""
    return db.query(
        RiskAssessment.station_id,
        RiskAssessment.risk_level,
        RiskAssessment.risk_score,
        RiskAssessment.landslide_probability,
        RiskAssessment.timestamp,
        func.row_number().over(
            partition_by=RiskAssessment.station_id,
            order_by=RiskAssessment.timestamp.desc()
        ).label('rn')
    ).subquery()


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_stations = db.query(SensorStation).filter(SensorStation.is_active == True).count()

    # Current risk distribution: count only the latest assessment for each
    # station. Historical/simulation assessments must not inflate dashboard
    # totals after repeated demos.
    latest_risk_sq = _get_latest_risk_subquery(db)
    current_risks = db.query(latest_risk_sq).filter(
        latest_risk_sq.c.rn == 1
    ).all()
    risk_dist = {"low": 0, "moderate": 0, "high": 0, "critical": 0}
    for risk in current_risks:
        if risk.risk_level in risk_dist:
            risk_dist[risk.risk_level] += 1

    active_alerts = db.query(Alert).filter(Alert.status == "active").count()
    pending_reports = db.query(CitizenReport).filter(CitizenReport.status == "pending").count()

    # Road status
    road_stats = db.query(
        RoadStatus.status,
        func.count(RoadStatus.id)
    ).group_by(RoadStatus.status).all()
    road_dist = {status: count for status, count in road_stats}

    # Total affected population from active alerts
    affected = db.query(func.sum(Alert.affected_population)).filter(
        Alert.status == "active"
    ).scalar() or 0

    # Total villages
    total_villages = db.query(Village).count()
    high_risk_villages = db.query(Village).filter(
        Village.risk_zone == "high_risk"
    ).count()

    # Average current risk score (latest assessment per station only).
    current_scores = [float(r.risk_score) for r in current_risks if r.risk_score is not None]
    avg_risk = (sum(current_scores) / len(current_scores)) if current_scores else 0

    # Recent reports count (last 24h)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    recent_reports = db.query(CitizenReport).filter(
        CitizenReport.created_at >= yesterday
    ).count()

    return {
        "total_stations": total_stations,
        "active_stations": total_stations,
        "risk_distribution": {
            "low": risk_dist.get("low", 0),
            "moderate": risk_dist.get("moderate", 0),
            "high": risk_dist.get("high", 0),
            "critical": risk_dist.get("critical", 0),
        },
        "active_alerts": active_alerts,
        "pending_reports": pending_reports,
        "recent_reports_24h": recent_reports,
        "road_status": {
            "open": road_dist.get("open", 0),
            "partially_blocked": road_dist.get("partially_blocked", 0),
            "blocked": road_dist.get("blocked", 0),
        },
        "affected_population": int(affected),
        "total_villages": total_villages,
        "high_risk_villages": high_risk_villages,
        "average_risk_score": round(float(avg_risk), 1),
        "last_updated": datetime.utcnow().isoformat(),
    }


@router.get("/risk-heatmap")
def get_risk_heatmap(db: Session = Depends(get_db)):
    # Get latest risk assessment per station using a subquery
    latest_risk_sq = db.query(
        RiskAssessment.station_id,
        RiskAssessment.risk_level,
        RiskAssessment.risk_score,
        RiskAssessment.timestamp,
        func.row_number().over(
            partition_by=RiskAssessment.station_id,
            order_by=RiskAssessment.timestamp.desc()
        ).label('rn')
    ).subquery()

    latest_risks = db.query(latest_risk_sq).filter(latest_risk_sq.c.rn == 1).all()

    # Create a dict for quick lookup
    risk_map = {r.station_id: r for r in latest_risks}

    # Single query for all active stations
    stations = db.query(SensorStation).filter(SensorStation.is_active == True).all()

    heatmap_data = []
    for station in stations:
        risk = risk_map.get(station.station_id)
        if risk:
            heatmap_data.append({
                "lat": station.latitude,
                "lng": station.longitude,
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
                "station_name": station.name,
                "station_id": station.station_id,
                "state": station.state,
                "district": station.district,
            })

    return heatmap_data


@router.get("/rainfall-trend")
def get_rainfall_trend(db: Session = Depends(get_db)):
    # Get average rainfall per hour for all stations, last 48 hours
    since = datetime.utcnow() - timedelta(hours=48)
    readings = db.query(SensorReading).filter(
        SensorReading.timestamp >= since
    ).order_by(SensorReading.timestamp).all()

    # Group by hour
    hourly = {}
    for r in readings:
        hour_key = r.timestamp.strftime("%Y-%m-%d %H:00")
        if hour_key not in hourly:
            hourly[hour_key] = []
        hourly[hour_key].append(r.rainfall_mm)

    return [
        {"timestamp": hour, "avg_rainfall": round(sum(vals) / len(vals), 1)}
        for hour, vals in sorted(hourly.items())
    ]


@router.get("/risk-trend")
def get_risk_trend(db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(hours=48)
    assessments = db.query(RiskAssessment).filter(
        RiskAssessment.timestamp >= since
    ).order_by(RiskAssessment.timestamp).all()

    hourly = {}
    for a in assessments:
        hour_key = a.timestamp.strftime("%Y-%m-%d %H:00")
        if hour_key not in hourly:
            hourly[hour_key] = []
        hourly[hour_key].append(a.risk_score)

    return [
        {"timestamp": hour, "avg_risk": round(sum(vals) / len(vals), 1)}
        for hour, vals in sorted(hourly.items())
    ]


@router.get("/state-summary")
def get_state_summary(db: Session = Depends(get_db)):
    # Get latest risk assessment per station using a subquery
    latest_risk_sq = db.query(
        RiskAssessment.station_id,
        RiskAssessment.risk_level,
        RiskAssessment.risk_score,
        RiskAssessment.timestamp,
        func.row_number().over(
            partition_by=RiskAssessment.station_id,
            order_by=RiskAssessment.timestamp.desc()
        ).label('rn')
    ).subquery()

    latest_risks = db.query(latest_risk_sq).filter(latest_risk_sq.c.rn == 1).all()

    # Create a dict for quick lookup
    risk_map = {r.station_id: r for r in latest_risks}

    # Single query for all active stations
    stations = db.query(SensorStation).filter(SensorStation.is_active == True).all()

    state_data = {}
    for s in stations:
        risk = risk_map.get(s.station_id)

        if s.state not in state_data:
            state_data[s.state] = {
                "state": s.state,
                "stations": 0,
                "avg_risk_score": 0,
                "risk_scores": [],
                "critical_count": 0,
            }
        state_data[s.state]["stations"] += 1
        if risk:
            state_data[s.state]["risk_scores"].append(risk.risk_score)
            if risk.risk_level == "critical":
                state_data[s.state]["critical_count"] += 1

    result = []
    for state, data in state_data.items():
        scores = data["risk_scores"]
        result.append({
            "state": data["state"],
            "stations": data["stations"],
            "avg_risk_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "critical_count": data["critical_count"],
        })

    return sorted(result, key=lambda x: x["avg_risk_score"], reverse=True)
