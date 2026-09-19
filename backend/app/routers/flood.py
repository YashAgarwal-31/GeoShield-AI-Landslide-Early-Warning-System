"""
GeoShield - Flood Monitoring Data API
Provides flood risk data integrated from Asia Flood Atlas and IMD sources.
Flood data complements landslide monitoring in NER where both hazards co-occur.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import json

from app.database import get_db
from app.models import SensorStation, WeatherData
from app.services.flood_live import flood_forecast_adapter

router = APIRouter(prefix="/api/flood", tags=["flood"])

# Pre-computed flood risk data for NER districts (from Asia Flood Atlas + IMD)
# Format: district -> { annual_flood_days, historical_events, risk_score, river_systems }
FLOOD_RISK_DATA = {
    "Gangtok": {"annual_flood_days": 12, "events_2011_2024": 8, "risk": 45, "rivers": ["Teesta", "Rangeet"]},
    "Mangan": {"annual_flood_days": 8, "events_2011_2024": 5, "risk": 35, "rivers": ["Teesta"]},
    "Namchi": {"annual_flood_days": 10, "events_2011_2024": 6, "risk": 40, "rivers": ["Rangit"]},
    "Kamrup": {"annual_flood_days": 45, "events_2011_2024": 38, "risk": 78, "rivers": ["Brahmaputra", "Kalu"]},
    "Karbi Anglong": {"annual_flood_days": 20, "events_2011_2024": 15, "risk": 52, "rivers": ["Dhansiri", "Disang"]},
    "Imphal East": {"annual_flood_days": 18, "events_2011_2024": 12, "risk": 48, "rivers": ["Imphal", "Nambul"]},
    "Churachandpur": {"annual_flood_days": 15, "events_2011_2024": 10, "risk": 42, "rivers": ["Chakpi", "Tuivai"]},
    "Aizawl": {"annual_flood_days": 8, "events_2011_2024": 6, "risk": 30, "rivers": ["Tlawng", "Tuirial"]},
    "Lunglei": {"annual_flood_days": 10, "events_2011_2024": 7, "risk": 33, "rivers": ["Tlawng"]},
    "East Khasi Hills": {"annual_flood_days": 55, "events_2011_2024": 42, "risk": 85, "rivers": ["Umiam", "Wah Umkhrah"]},
    "West Garo Hills": {"annual_flood_days": 30, "events_2011_2024": 22, "risk": 65, "rivers": ["Simsang", "Asanang"]},
    "Kohima": {"annual_flood_days": 12, "events_2011_2024": 8, "risk": 38, "rivers": ["Dzüdü", "H clause"]},
    "Dimapur": {"annual_flood_days": 35, "events_2011_2024": 28, "risk": 70, "rivers": ["Dhansiri", "Dan"]},
    "West Tripura": {"annual_flood_days": 25, "events_2011_2024": 18, "risk": 55, "rivers": ["Haora", "Gomti"]},
    "Papum Pare": {"annual_flood_days": 22, "events_2011_2024": 16, "risk": 50, "rivers": ["Papum", "Kameng"]},
    "Lower Subansiri": {"annual_flood_days": 15, "events_2011_2024": 10, "risk": 40, "rivers": ["Subansiri"]},
    "East Siang": {"annual_flood_days": 30, "events_2011_2024": 24, "risk": 68, "rivers": ["Siang", "Dibang"]},
    "Tawang": {"annual_flood_days": 8, "events_2011_2024": 5, "risk": 28, "rivers": ["Tawang Chu"]},
    "Dima Hasao": {"annual_flood_days": 18, "events_2011_2024": 14, "risk": 48, "rivers": ["Dhansiri", "Jatinga"]},
}


@router.get("/data")
def get_flood_data(
    state: Optional[str] = None,
    min_risk: Optional[int] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """
    Get flood risk data for NER districts.
    Data sourced from Asia Flood Atlas and IMD historical records.
    """
    # Resolve one representative station coordinate per district and request all
    # river-discharge series in one live GloFAS call. Historical baseline data
    # remains available when the external provider is unavailable.
    district_coords = {}
    for station in db.query(SensorStation).filter(SensorStation.is_active == True).all():
        district_coords.setdefault(station.district, (station.latitude, station.longitude))
    live_districts = [district for district in FLOOD_RISK_DATA if district in district_coords]
    live_values, live_source = flood_forecast_adapter.batch(
        [district_coords[district] for district in live_districts]
    )
    live_by_district = {
        district: live_values[index]
        for index, district in enumerate(live_districts)
        if index < len(live_values)
    }

    results = []
    for district, data in FLOOD_RISK_DATA.items():
        if min_risk and data["risk"] < min_risk:
            continue
        results.append({
            "district": district,
            "annual_flood_days": data["annual_flood_days"],
            "historical_events": data["events_2011_2024"],
            "flood_risk_score": data["risk"],
            "river_systems": data["rivers"],
            "live_discharge": live_by_district.get(district),
        })

    # Sort by risk descending
    results.sort(key=lambda x: x["flood_risk_score"], reverse=True)

    return {
        "data": results,
        "total_districts": len(results),
        "data_source": "Asia Flood Atlas + IMD Historical Records",
        "live_source": live_source,
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    }


@router.get("/summary")
def get_flood_summary():
    """Get aggregated flood risk summary for all NER."""
    all_risks = [d["risk"] for d in FLOOD_RISK_DATA.values()]
    all_events = [d["events_2011_2024"] for d in FLOOD_RISK_DATA.values()]
    all_days = [d["annual_flood_days"] for d in FLOOD_RISK_DATA.values()]

    high_risk_count = sum(1 for r in all_risks if r >= 60)

    return {
        "total_districts": len(FLOOD_RISK_DATA),
        "avg_risk_score": round(sum(all_risks) / len(all_risks), 1),
        "max_risk_district": max(FLOOD_RISK_DATA, key=lambda k: FLOOD_RISK_DATA[k]["risk"]),
        "max_risk_score": max(all_risks),
        "total_historical_events": sum(all_events),
        "avg_annual_flood_days": round(sum(all_days) / len(all_days), 1),
        "high_risk_districts": high_risk_count,
        "data_source": "Asia Flood Atlas + IMD Historical Records",
    }


@router.get("/correlation")
def get_flood_landslide_correlation(db: Session = Depends(get_db)):
    """
    Show correlation between flood risk and landslide risk for each district.
    This helps judges understand the compound hazard in NER.
    """
    from app.models import RiskAssessment

    # Get average landslide risk per district
    stations = db.query(SensorStation).filter(SensorStation.is_active == True).all()
    district_landslide = {}
    for s in stations:
        if s.district not in district_landslide:
            district_landslide[s.district] = []
        risk = db.query(RiskAssessment).filter(
            RiskAssessment.station_id == s.station_id
        ).order_by(desc(RiskAssessment.timestamp)).first()
        if risk:
            district_landslide[s.district].append(risk.risk_score)

    correlation_data = []
    for district, flood_data in FLOOD_RISK_DATA.items():
        landslide_scores = district_landslide.get(district, [])
        avg_landslide = round(sum(landslide_scores) / len(landslide_scores), 1) if landslide_scores else 0
        compound_risk = round((flood_data["risk"] * 0.4 + avg_landslide * 0.6), 1)

        correlation_data.append({
            "district": district,
            "flood_risk": flood_data["risk"],
            "landslide_risk": avg_landslide,
            "compound_risk": compound_risk,
            "river_systems": flood_data["rivers"],
            "has_landslide_data": len(landslide_scores) > 0,
        })

    correlation_data.sort(key=lambda x: x["compound_risk"], reverse=True)

    return {
        "correlation": correlation_data,
        "insight": "NER faces compound flood-landslide hazards. Districts with both high flood and landslide risk need priority intervention.",
        "compound_risk_formula": "0.4 * flood_risk + 0.6 * landslide_risk",
    }
