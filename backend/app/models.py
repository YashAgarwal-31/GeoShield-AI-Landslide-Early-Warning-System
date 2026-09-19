from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Boolean, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class ReportType(str, enum.Enum):
    CRACK = "crack"
    SLOPE_MOVEMENT = "slope_movement"
    BLOCKED_ROAD = "blocked_road"
    FLOODING = "flooding"
    OTHER = "other"


class SensorStation(Base):
    __tablename__ = "sensor_stations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, unique=True, index=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    state = Column(String)
    district = Column(String)
    village = Column(String)
    elevation = Column(Float)  # meters above sea level
    slope_angle = Column(Float)  # degrees
    soil_type = Column(String)
    vegetation_cover = Column(Float)  # percentage
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, index=True)
    rainfall_mm = Column(Float, default=0.0)
    soil_moisture = Column(Float, default=0.0)  # percentage
    soil_temperature = Column(Float, default=0.0)  # celsius
    ground_displacement = Column(Float, default=0.0)  # mm
    tilt_angle_x = Column(Float, default=0.0)  # degrees
    tilt_angle_y = Column(Float, default=0.0)  # degrees
    pore_water_pressure = Column(Float, default=0.0)  # kPa
    vibration_level = Column(Float, default=0.0)
    source = Column(String, default="unknown", index=True)
    external_id = Column(String, nullable=True, unique=True, index=True)
    timestamp = Column(DateTime, server_default=func.now())


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, index=True)
    risk_level = Column(String)  # low, moderate, high, critical
    risk_score = Column(Float)  # 0-100
    landslide_probability = Column(Float)  # 0-1
    contributing_factors = Column(Text)  # JSON string
    predicted_time_window = Column(Integer)  # hours
    recommendation = Column(Text)
    model_version = Column(String, default="v1.0")
    timestamp = Column(DateTime, server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, index=True)
    risk_level = Column(String)
    title = Column(String)
    message = Column(Text)
    status = Column(String, default="active")
    affected_population = Column(Integer, default=0)
    nearby_villages = Column(Text)  # JSON string
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String)
    description = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    reporter_name = Column(String, nullable=True)
    reporter_phone = Column(String, nullable=True)
    reporter_language = Column(String, default="en")
    submitted_by = Column(String, nullable=True, index=True)
    status = Column(String, default="pending")  # pending, verified, dismissed
    verified_by = Column(String, nullable=True)
    attachment_filename = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    rainfall_1h = Column(Float)
    rainfall_24h = Column(Float)
    rainfall_7d = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)
    pressure = Column(Float)
    visibility = Column(Float)
    forecast_rainfall_24h = Column(Float)
    forecast_rainfall_48h = Column(Float)
    timestamp = Column(DateTime, server_default=func.now())


class RoadStatus(Base):
    __tablename__ = "road_status"

    id = Column(Integer, primary_key=True, index=True)
    road_name = Column(String)
    road_type = Column(String)  # national_highway, state_highway, district_road
    start_lat = Column(Float)
    start_lng = Column(Float)
    end_lat = Column(Float)
    end_lng = Column(Float)
    status = Column(String, default="open")  # open, partially_blocked, blocked
    blockage_reason = Column(String, nullable=True)
    alternative_route = Column(String, nullable=True)
    updated_at = Column(DateTime, server_default=func.now())


class Village(Base):
    __tablename__ = "villages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    state = Column(String)
    district = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    population = Column(Integer)
    risk_zone = Column(String)  # safe, low_risk, medium_risk, high_risk
    nearest_hospital_km = Column(Float)
    nearest_police_km = Column(Float)
    evacuation_route = Column(Text, nullable=True)


class UserAccount(Base):
    __tablename__ = "user_accounts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="citizen")
    is_active = Column(Boolean, default=True, nullable=False)
    token_version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, index=True)
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    district = Column(String, nullable=False, default="all", index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, nullable=True, index=True)
    channel = Column(String, nullable=False, index=True)
    provider = Column(String, nullable=False)
    recipient = Column(String, nullable=True)
    district = Column(String, nullable=True, index=True)
    status = Column(String, nullable=False, index=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
