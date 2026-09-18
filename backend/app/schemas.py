"""
Pydantic schemas for GeoShield API request/response validation.
Prevents invalid data from reaching the database layer.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────
class RiskLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class IntensityLevel(str, Enum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class AlertStatus(str, Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"


class ReportType(str, Enum):
    crack = "crack"
    slope_movement = "slope_movement"
    blocked_road = "blocked_road"
    flooding = "flooding"
    other = "other"


# ── Predict ────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")
    slope: Optional[float] = Field(None, ge=0, le=90, description="Slope angle in degrees")
    elevation: Optional[float] = Field(None, ge=-500, le=9000, description="Elevation in meters")
    rainfall_mm: Optional[float] = Field(None, ge=0, le=1000, description="Rainfall in mm")
    soil_moisture: Optional[float] = Field(None, ge=0, le=100, description="Soil moisture %")
    ndvi: Optional[float] = Field(None, ge=-1, le=1, description="NDVI index (-1 to 1)")

    @field_validator("latitude")
    @classmethod
    def validate_ner_latitude(cls, v):
        if not (21.0 <= v <= 30.0):
            # Allow non-NER but warn
            pass
        return v


# ── Simulate ───────────────────────────────────────────────────
class SimulateRequest(BaseModel):
    station_id: Optional[str] = Field(None, pattern=r"^NER-\d{3}$", description="Station ID (NER-XXX)")
    intensity: IntensityLevel = Field(default="high", description="Simulation intensity level")
    custom_rainfall: Optional[float] = Field(None, ge=0, le=500, description="Custom rainfall in mm")
    custom_moisture: Optional[float] = Field(None, ge=0, le=100, description="Custom soil moisture %")


# ── Alert ──────────────────────────────────────────────────────
class AlertCreateRequest(BaseModel):
    station_id: str = Field(..., pattern=r"^NER-\d{3}$", description="Station ID")
    risk_level: RiskLevel = Field(..., description="Risk level")
    title: str = Field(..., min_length=5, max_length=200, description="Alert title")
    message: str = Field(..., min_length=10, max_length=2000, description="Alert message")
    affected_population: int = Field(default=0, ge=0, le=1000000, description="People affected")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


# ── Report ─────────────────────────────────────────────────────
class ReportCreateRequest(BaseModel):
    report_type: ReportType = Field(..., description="Type of report")
    description: str = Field(..., min_length=10, max_length=2000, description="Description")
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    reporter_name: Optional[str] = Field(None, max_length=100)
    reporter_phone: Optional[str] = Field(None, pattern=r"^\+?[\d\s-]{7,15}$")
    reporter_language: Optional[str] = Field("en", pattern=r"^(en|hi|bn|as|ne)$")


# ── Auth ───────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$", description="Valid email")
    password: str = Field(..., min_length=4, max_length=128, description="Password")


class UserCreateRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="citizen", pattern=r"^(admin|field_officer|district_admin|citizen)$")


class UserStatusRequest(BaseModel):
    is_active: bool


class UserPasswordRequest(BaseModel):
    password: str = Field(..., min_length=8, max_length=128)


class SensorStationCreateRequest(BaseModel):
    station_id: str = Field(..., pattern=r"^NER-\d{3}$")
    name: str = Field(..., min_length=2, max_length=120)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    state: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    village: str = Field(default="", max_length=120)
    elevation: float = Field(default=0, ge=-500, le=9000)
    slope_angle: float = Field(default=0, ge=0, le=90)
    soil_type: str = Field(default="unknown", max_length=100)
    vegetation_cover: float = Field(default=0, ge=0, le=100)


class SensorStationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=120)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    state: Optional[str] = Field(None, min_length=2, max_length=100)
    district: Optional[str] = Field(None, min_length=2, max_length=100)
    village: Optional[str] = Field(None, max_length=120)
    elevation: Optional[float] = Field(None, ge=-500, le=9000)
    slope_angle: Optional[float] = Field(None, ge=0, le=90)
    soil_type: Optional[str] = Field(None, max_length=100)
    vegetation_cover: Optional[float] = Field(None, ge=0, le=100)
    is_active: Optional[bool] = None


class SensorReadingIngestRequest(BaseModel):
    external_id: Optional[str] = Field(None, min_length=3, max_length=128)
    rainfall_mm: float = Field(default=0, ge=0, le=1000)
    soil_moisture: float = Field(default=0, ge=0, le=100)
    soil_temperature: float = Field(default=0, ge=-30, le=80)
    ground_displacement: float = Field(default=0, ge=0, le=1000)
    tilt_angle_x: float = Field(default=0, ge=-90, le=90)
    tilt_angle_y: float = Field(default=0, ge=-90, le=90)
    pore_water_pressure: float = Field(default=0, ge=0, le=5000)
    vibration_level: float = Field(default=0, ge=0, le=10000)
    observed_at: Optional[str] = Field(
        None,
        description="Optional ISO-8601 observation timestamp; server time is used when omitted.",
    )


# ── Response wrappers ─────────────────────────────────────────
class PredictResponse(BaseModel):
    location: dict
    nearest_station: Optional[dict]
    risk_assessment: dict
    model_info: dict
    timestamp: str


class SimulateResponse(BaseModel):
    status: str
    simulation: dict
    risk_assessment: dict
    alert: Optional[dict]


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
