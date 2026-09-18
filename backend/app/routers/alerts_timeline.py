"""
GeoShield - Alert Timeline API
Provides chronological timeline view of all alerts for dashboard visualization.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Alert, RiskAssessment


router = APIRouter(prefix="/api/alerts", tags=["alerts-timeline"])


@router.get("/timeline")
def get_alert_timeline(
    hours: int = Query(72, ge=1, le=720, description="Hours of history"),
    risk_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get alerts as a chronological timeline for visualization.
    Groups alerts by hour and includes risk assessment context.
    """
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
    
    query = db.query(Alert).filter(Alert.created_at >= since)
    if risk_level:
        query = query.filter(Alert.risk_level == risk_level)
    
    alerts = query.order_by(desc(Alert.created_at)).all()
    
    # Group by hour for timeline
    timeline = {}
    for alert in alerts:
        hour_key = alert.created_at.strftime("%Y-%m-%d %H:00")
        if hour_key not in timeline:
            timeline[hour_key] = {
                "timestamp": hour_key,
                "alerts": [],
                "total_affected": 0,
                "max_risk": "low",
            }
        
        risk_order = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
        if risk_order.get(alert.risk_level, 0) > risk_order.get(timeline[hour_key]["max_risk"], 0):
            timeline[hour_key]["max_risk"] = alert.risk_level
        
        timeline[hour_key]["alerts"].append({
            "id": alert.id,
            "station_id": alert.station_id,
            "risk_level": alert.risk_level,
            "title": alert.title,
            "status": alert.status,
            "affected_population": alert.affected_population,
            "created_at": alert.created_at.isoformat(),
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        })
        timeline[hour_key]["total_affected"] += alert.affected_population
    
    # Convert to sorted list
    result = sorted(timeline.values(), key=lambda x: x["timestamp"], reverse=True)
    
    return {
        "timeline": result,
        "summary": {
            "total_alerts": len(alerts),
            "total_hours": hours,
            "critical_count": sum(1 for a in alerts if a.risk_level == "critical"),
            "high_count": sum(1 for a in alerts if a.risk_level == "high"),
            "moderate_count": sum(1 for a in alerts if a.risk_level == "moderate"),
            "low_count": sum(1 for a in alerts if a.risk_level == "low"),
            "total_affected_population": sum(a.affected_population for a in alerts),
        }
    }


@router.get("/history")
def get_alert_history(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get daily alert counts for trend chart.
    """
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    alerts = db.query(Alert).filter(Alert.created_at >= since).all()
    
    daily = {}
    for alert in alerts:
        day_key = alert.created_at.strftime("%Y-%m-%d")
        if day_key not in daily:
            daily[day_key] = {"date": day_key, "critical": 0, "high": 0, "moderate": 0, "low": 0, "total": 0}
        daily[day_key][alert.risk_level] = daily[day_key].get(alert.risk_level, 0) + 1
        daily[day_key]["total"] += 1
    
    return sorted(daily.values(), key=lambda x: x["date"])
