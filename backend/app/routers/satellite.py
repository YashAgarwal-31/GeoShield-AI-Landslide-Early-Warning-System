"""Satellite-derived snapshot API with explicit provenance and freshness."""

import os

from fastapi import APIRouter, HTTPException

from app.services.external_data import SatelliteSnapshotAdapter


router = APIRouter(prefix="/api/satellite", tags=["satellite"])

SATELLITE_DATA_FILE = os.getenv(
    "SATELLITE_DATA_PATH",
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "datasets",
        "processed",
        "real_satellite_data.json",
    ),
)
satellite_adapter = SatelliteSnapshotAdapter(SATELLITE_DATA_FILE)


@router.get("/data")
def get_all_satellite_data():
    """Return the available cached station snapshot and its age."""
    data, source = satellite_adapter.load()
    return {
        "stations": data,
        "source": source,
        "total_stations": len(data),
    }


@router.get("/data/{station_id}")
def get_station_satellite_data(station_id: str):
    data, source = satellite_adapter.load()
    for station in data:
        if station["id"] == station_id:
            return {"station": station, "source": source}
    raise HTTPException(status_code=404, detail="Station not found")


@router.get("/summary")
def get_satellite_summary():
    """Aggregate the cached snapshot without presenting it as a live feed."""
    data, source = satellite_adapter.load()
    if not data:
        return {
            "error": "No satellite snapshot available",
            "total_stations": 0,
            "source": source,
        }

    elevations = [s["real_elevation"] for s in data]
    sm_0_7 = [s["real_soil_moisture_0_7cm"] for s in data]
    rain_24h = [s["real_rainfall_24h"] for s in data]
    rain_7d = [s["real_rainfall_7d"] for s in data]
    ndvi_vals = [s["estimated_ndvi"] for s in data]
    temps = [s["real_temperature"] for s in data]
    humidity = [s["real_humidity"] for s in data]

    return {
        "total_stations": len(data),
        "elevation": {
            "min": round(min(elevations), 1),
            "max": round(max(elevations), 1),
            "avg": round(sum(elevations) / len(elevations), 1),
            "unit": "meters",
        },
        "soil_moisture_surface": {
            "min": round(min(sm_0_7), 3),
            "max": round(max(sm_0_7), 3),
            "avg": round(sum(sm_0_7) / len(sm_0_7), 3),
            "unit": "m³/m³",
        },
        "rainfall_24h": {
            "min": round(min(rain_24h), 1),
            "max": round(max(rain_24h), 1),
            "avg": round(sum(rain_24h) / len(rain_24h), 1),
            "total": round(sum(rain_24h), 1),
            "unit": "mm",
        },
        "rainfall_7d": {
            "min": round(min(rain_7d), 1),
            "max": round(max(rain_7d), 1),
            "avg": round(sum(rain_7d) / len(rain_7d), 1),
            "total": round(sum(rain_7d), 1),
            "unit": "mm",
        },
        "ndvi": {
            "min": round(min(ndvi_vals), 3),
            "max": round(max(ndvi_vals), 3),
            "avg": round(sum(ndvi_vals) / len(ndvi_vals), 3),
            "description": "Estimated vegetation index (0-1)",
        },
        "temperature": {
            "min": round(min(temps), 1),
            "max": round(max(temps), 1),
            "avg": round(sum(temps) / len(temps), 1),
            "unit": "°C",
        },
        "humidity": {
            "min": round(min(humidity), 1),
            "max": round(max(humidity), 1),
            "avg": round(sum(humidity) / len(humidity), 1),
            "unit": "%",
        },
        "source": source,
    }


@router.get("/risk-zones")
def get_satellite_risk_zones():
    """Calculate demonstration risk zones from the cached snapshot."""
    data, source = satellite_adapter.load()
    risk_zones = []

    for station in data:
        elevation_risk = min(1.0, station["real_elevation"] / 3000)
        sm_risk = min(1.0, station["real_soil_moisture_0_7cm"] / 0.6)
        rain_risk = min(1.0, station["real_rainfall_24h"] / 50)
        ndvi_risk = max(0, 1 - station["estimated_ndvi"])
        composite_risk = (
            elevation_risk * 0.25
            + sm_risk * 0.30
            + rain_risk * 0.25
            + ndvi_risk * 0.20
        ) * 100

        risk_level = "low"
        if composite_risk >= 70:
            risk_level = "critical"
        elif composite_risk >= 50:
            risk_level = "high"
        elif composite_risk >= 30:
            risk_level = "moderate"

        risk_zones.append(
            {
                "station_id": station["id"],
                "name": station["name"],
                "state": station["state"],
                "lat": station["lat"],
                "lng": station["lng"],
                "satellite_risk_score": round(composite_risk, 1),
                "risk_level": risk_level,
                "factors": {
                    "elevation_risk": round(elevation_risk * 100, 1),
                    "soil_moisture_risk": round(sm_risk * 100, 1),
                    "rainfall_risk": round(rain_risk * 100, 1),
                    "vegetation_risk": round(ndvi_risk * 100, 1),
                },
                "snapshot_data": {
                    "elevation": station["real_elevation"],
                    "soil_moisture": station["real_soil_moisture_0_7cm"],
                    "rainfall_24h": station["real_rainfall_24h"],
                    "ndvi": station["estimated_ndvi"],
                },
            }
        )

    return {
        "risk_zones": sorted(
            risk_zones,
            key=lambda item: item["satellite_risk_score"],
            reverse=True,
        ),
        "source": source,
    }
