"""Weather API with optional live retrieval and explicit offline fallback."""

from datetime import datetime
import os

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SensorStation, WeatherData
from app.services.external_data import source_metadata, weather_adapter
from app.services.imd import imd_adapter


router = APIRouter(prefix="/api/weather", tags=["weather"])
WEATHER_MAX_AGE_SECONDS = int(os.getenv("WEATHER_MAX_AGE_SECONDS", "21600"))


def _serialize_weather(weather: WeatherData) -> dict:
    return {
        "temperature": weather.temperature,
        "humidity": weather.humidity,
        "rainfall_1h": weather.rainfall_1h,
        "rainfall_24h": weather.rainfall_24h,
        "rainfall_7d": weather.rainfall_7d,
        "wind_speed": weather.wind_speed,
        "wind_direction": weather.wind_direction,
        "pressure": weather.pressure,
        "visibility": weather.visibility,
        "forecast_rainfall_24h": weather.forecast_rainfall_24h,
        "forecast_rainfall_48h": weather.forecast_rainfall_48h,
        "timestamp": weather.timestamp.isoformat() if weather.timestamp else None,
    }


def _fallback_source(
    observed_at: datetime | None,
    reason: str | None,
    *,
    has_data: bool = True,
) -> dict:
    return source_metadata(
        mode="fallback" if has_data else "unavailable",
        provider="GeoShield seeded demo database",
        observed_at=observed_at,
        max_age_seconds=WEATHER_MAX_AGE_SECONDS,
        fallback_reason=reason,
        detail=(
            "Seeded demonstration weather; not a physical sensor or live forecast."
            if has_data
            else "No live or seeded weather record is available for this station."
        ),
    )


def _try_imd_current(station: SensorStation | None):
    if station is None:
        return None, None
    data, source = imd_adapter.current_nearest(station.latitude, station.longitude)
    if data is None:
        return None, source
    return {
        "temperature": data.get("temperature"),
        "humidity": data.get("humidity"),
        "rainfall_1h": None,
        "rainfall_24h": data.get("rainfall_24h"),
        "rainfall_7d": None,
        "wind_speed": data.get("wind_speed"),
        "wind_direction": data.get("wind_direction"),
        "pressure": data.get("pressure"),
        "visibility": None,
        "forecast_rainfall_24h": None,
        "forecast_rainfall_48h": None,
        "timestamp": source.get("observed_at"),
        "station_name": data.get("station"),
        "distance_km": data.get("distance_km"),
    }, source


def _try_live_weather(
    station_id: str,
    station: SensorStation | None,
    hours: int,
):
    if station is None:
        return None, "station_coordinates_unavailable"
    return weather_adapter.get(
        station_id,
        station.latitude,
        station.longitude,
        forecast_hours=hours,
    )


@router.get("/{station_id}")
def get_weather(station_id: str, db: Session = Depends(get_db)):
    station = db.query(SensorStation).filter(
        SensorStation.station_id == station_id
    ).first()
    imd_data, imd_source = _try_imd_current(station)
    if imd_data is not None:
        return {
            "station_id": station_id,
            "data": imd_data,
            "source": imd_source,
        }

    live_result, reason = _try_live_weather(station_id, station, 48)
    if live_result is not None:
        response_source = dict(live_result.source)
        if imd_source and imd_source.get("fallback_reason"):
            response_source["preferred_provider_fallback"] = imd_source["fallback_reason"]
        return {
            "station_id": station_id,
            "data": live_result.data,
            "source": response_source,
        }

    weather = db.query(WeatherData).filter(
        WeatherData.station_id == station_id
    ).order_by(desc(WeatherData.timestamp)).first()
    if not weather:
        return {
            "station_id": station_id,
            "data": None,
            "source": _fallback_source(None, reason, has_data=False),
        }

    return {
        "station_id": station_id,
        "data": _serialize_weather(weather),
        "source": _fallback_source(weather.timestamp, reason),
    }


@router.get("/{station_id}/forecast")
def get_forecast(
    station_id: str,
    hours: int = 48,
    db: Session = Depends(get_db),
):
    hours = max(1, min(hours, 168))
    station = db.query(SensorStation).filter(
        SensorStation.station_id == station_id
    ).first()
    live_result, reason = _try_live_weather(station_id, station, hours)
    if live_result is not None:
        return {
            "station_id": station_id,
            "hours": hours,
            "series_kind": "forecast",
            "forecast": live_result.forecast,
            "source": live_result.source,
        }

    weather_entries = db.query(WeatherData).filter(
        WeatherData.station_id == station_id
    ).order_by(desc(WeatherData.timestamp)).limit(max(1, hours // 3)).all()
    observed_at = weather_entries[0].timestamp if weather_entries else None
    return {
        "station_id": station_id,
        "hours": hours,
        "series_kind": "demo_history",
        "forecast": [
            {
                "timestamp": w.timestamp.isoformat() if w.timestamp else None,
                "temperature": w.temperature,
                "rainfall_1h": w.rainfall_1h,
                "forecast_rainfall_24h": w.forecast_rainfall_24h,
                "humidity": w.humidity,
            }
            for w in reversed(weather_entries)
        ],
        "source": _fallback_source(
            observed_at,
            reason,
            has_data=bool(weather_entries),
        ),
    }
