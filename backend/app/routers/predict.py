"""
GeoShield - Click-to-Predict and Export API
Allows users to click anywhere on the map and get AI risk prediction.
Supports GeoJSON and CSV export of all risk data.
"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import json
import csv
import io

from app.database import get_db
from app.models import SensorStation, RiskAssessment, Village, RoadStatus
from app.ai_engine.risk_predictor import get_predictor
from app.ai_engine.enhanced_predictor import get_enhanced_predictor

router = APIRouter(prefix="/api", tags=["predict"])


class PredictRequest(BaseModel):
    latitude: float = Field(..., ge=21.0, le=30.0, description="Latitude in NER region")
    longitude: float = Field(..., ge=88.0, le=98.0, description="Longitude in NER region")
    slope: Optional[float] = Field(None, ge=0, le=90, description="Slope angle in degrees")
    elevation: Optional[float] = Field(None, ge=0, le=6000, description="Elevation in meters")
    rainfall_mm: Optional[float] = Field(None, ge=0, le=500, description="Rainfall in mm")
    soil_moisture: Optional[float] = Field(None, ge=0, le=100, description="Soil moisture %")
    ndvi: Optional[float] = Field(None, ge=-1, le=1, description="NDVI vegetation index")


@router.post("/predict")
def predict_risk_at_location(req: PredictRequest, db: Session = Depends(get_db)):
    """
    AI risk prediction for any clicked location on the map.
    Uses nearest-station interpolation + ML model for accurate assessment.
    """
    predictor = get_predictor()

    # Find nearest sensor station for context
    stations = db.query(SensorStation).filter(SensorStation.is_active == True).all()
    nearest = None
    min_dist = float('inf')

    for s in stations:
        d = ((s.latitude - req.latitude) ** 2 + (s.longitude - req.longitude) ** 2) ** 0.5
        if d < min_dist:
            min_dist = d
            nearest = s

    # Use provided values or nearest station defaults
    station_data = {
        "slope_angle": req.slope if req.slope is not None else (nearest.slope_angle if nearest else 20),
        "elevation": req.elevation if req.elevation is not None else (nearest.elevation if nearest else 500),
        "aspect": 180,  # default
        "vegetation_cover": (nearest.vegetation_cover if nearest else 60),
        "distance_to_road": 5000,
    }

    sensor_data = {
        "rainfall_mm": req.rainfall_mm if req.rainfall_mm is not None else 10,
        "soil_moisture": req.soil_moisture if req.soil_moisture is not None else 40,
        "ground_displacement": 0,
        "tilt_angle_x": 0,
        "tilt_angle_y": 0,
        "pore_water_pressure": 0,
    }

    # Run enhanced ML prediction with terrain enrichment
    enhanced = get_enhanced_predictor()
    enhanced_result = enhanced.predict(
        req.latitude, req.longitude,
        {
            "slope": req.slope if req.slope else (nearest.slope_angle if nearest else None),
            "elevation": req.elevation if req.elevation else (nearest.elevation if nearest else None),
            "rainfall_24hr": req.rainfall_mm if req.rainfall_mm else None,
            "soil_moisture": (req.soil_moisture / 100) if req.soil_moisture is not None else None,
            "ndvi": (nearest.vegetation_cover / 100) if nearest else None,
        }
    )

    # Also run original predictor for backward compatibility
    prediction = predictor.predict_risk(sensor_data, station_data)

    # The enhanced model owns the final score/level, so any derived guidance
    # must be recalculated from that same level. Previously a high enhanced
    # score could be paired with the original model's low-risk recommendation.
    final_risk_level = enhanced_result["risk_level"]
    final_recommendation = predictor.recommendation_for_level(
        final_risk_level,
        prediction.get("contributing_factors", []),
    )

    return {
        "location": {
            "latitude": req.latitude,
            "longitude": req.longitude,
        },
        "nearest_station": {
            "station_id": nearest.station_id if nearest else None,
            "name": nearest.name if nearest else None,
            "distance_km": round(min_dist * 111, 1) if nearest else None,
        },
        "risk_assessment": {
            **prediction,
            "risk_score": enhanced_result["risk_score"],
            "risk_level": final_risk_level,
            "recommendation": final_recommendation,
            "confidence": enhanced_result["confidence"],
            "source": enhanced_result["source"],
            "feature_importance": enhanced_result.get("feature_importance"),
            "terrain_data": enhanced_result.get("terrain_data"),
        },
        "model_info": {
            "type": f"{enhanced_result['source'].upper()} + RF+GB Ensemble",
            "training_samples": "12,000 regional and realistically generated NER samples",
            "features": 9,
            "terrain_enriched": True,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/export/geojson")
def export_geojson(db: Session = Depends(get_db)):
    """Export all station risk data as GeoJSON for GIS tools."""
    stations = db.query(SensorStation).filter(SensorStation.is_active == True).all()

    features = []
    for s in stations:
        risk = db.query(RiskAssessment).filter(
            RiskAssessment.station_id == s.station_id
        ).order_by(desc(RiskAssessment.timestamp)).first()

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [s.longitude, s.latitude]
            },
            "properties": {
                "station_id": s.station_id,
                "name": s.name,
                "state": s.state,
                "district": s.district,
                "village": s.village,
                "elevation": s.elevation,
                "slope_angle": s.slope_angle,
                "soil_type": s.soil_type,
                "vegetation_cover": s.vegetation_cover,
                "risk_score": risk.risk_score if risk else 0,
                "risk_level": risk.risk_level if risk else "low",
                "landslide_probability": risk.landslide_probability if risk else 0,
                "last_updated": risk.timestamp.isoformat() if risk and risk.timestamp else None,
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "name": "GeoShield_NER_Risk_Data",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features,
        "metadata": {
            "generated_by": "GeoShield AI - SIH 2026",
            "total_stations": len(features),
            "timestamp": datetime.utcnow().isoformat(),
        }
    }

    return geojson


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    """Export all station risk data as CSV for Excel/analysis."""
    stations = db.query(SensorStation).filter(SensorStation.is_active == True).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "station_id", "name", "state", "district", "latitude", "longitude",
        "elevation", "slope_angle", "soil_type", "vegetation_cover",
        "risk_score", "risk_level", "landslide_probability", "last_updated"
    ])

    for s in stations:
        risk = db.query(RiskAssessment).filter(
            RiskAssessment.station_id == s.station_id
        ).order_by(desc(RiskAssessment.timestamp)).first()

        writer.writerow([
            s.station_id, s.name, s.state, s.district,
            s.latitude, s.longitude, s.elevation, s.slope_angle,
            s.soil_type, s.vegetation_cover,
            risk.risk_score if risk else 0,
            risk.risk_level if risk else "low",
            risk.landslide_probability if risk else 0,
            risk.timestamp.isoformat() if risk and risk.timestamp else "",
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=geoshield_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/export/risk-zones")
def export_risk_zones_geojson(db: Session = Depends(get_db)):
    """Export risk zones as GeoJSON polygons for high-risk areas."""
    stations = db.query(SensorStation).filter(SensorStation.is_active == True).all()

    features = []
    for s in stations:
        risk = db.query(RiskAssessment).filter(
            RiskAssessment.station_id == s.station_id
        ).order_by(desc(RiskAssessment.timestamp)).first()

        if risk and risk.risk_level in ("high", "critical"):
            # Create a simple circular polygon around the station
            import math
            radius_km = 5 if risk.risk_level == "critical" else 3
            center_lat, center_lng = s.latitude, s.longitude
            coords = []
            for angle in range(0, 361, 10):
                rad = math.radians(angle)
                lat = center_lat + (radius_km / 111) * math.cos(rad)
                lng = center_lng + (radius_km / (111 * math.cos(math.radians(center_lat)))) * math.sin(rad)
                coords.append([round(lng, 4), round(lat, 4)])

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords]
                },
                "properties": {
                    "station_id": s.station_id,
                    "name": s.name,
                    "risk_level": risk.risk_level,
                    "risk_score": risk.risk_score,
                    "radius_km": radius_km,
                }
            })

    return {
        "type": "FeatureCollection",
        "name": "GeoShield_High_Risk_Zones",
        "features": features,
    }
