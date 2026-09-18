"""initial schema — baseline for all GeoShield tables

Revision ID: 0001
Revises:
Create Date: 2026-08-28

This is a hand-written baseline migration that creates every table
matching the models in app/models.py.  Future autogenerate revisions
should chain off this one.

Note: sent_sms / sent_push columns were intentionally omitted — they
were dead code removed in a prior cleanup.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── sensor_stations ──────────────────────────────────────────────
    op.create_table(
        "sensor_stations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("station_id", sa.String(), unique=True, index=True),
        sa.Column("name", sa.String()),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("state", sa.String()),
        sa.Column("district", sa.String()),
        sa.Column("village", sa.String()),
        sa.Column("elevation", sa.Float()),
        sa.Column("slope_angle", sa.Float()),
        sa.Column("soil_type", sa.String()),
        sa.Column("vegetation_cover", sa.Float()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── sensor_readings ──────────────────────────────────────────────
    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("station_id", sa.String(), index=True),
        sa.Column("rainfall_mm", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("soil_moisture", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("soil_temperature", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("ground_displacement", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("tilt_angle_x", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("tilt_angle_y", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("pore_water_pressure", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("vibration_level", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── risk_assessments ─────────────────────────────────────────────
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("station_id", sa.String(), index=True),
        sa.Column("risk_level", sa.String()),
        sa.Column("risk_score", sa.Float()),
        sa.Column("landslide_probability", sa.Float()),
        sa.Column("contributing_factors", sa.Text()),
        sa.Column("predicted_time_window", sa.Integer()),
        sa.Column("recommendation", sa.Text()),
        sa.Column("model_version", sa.String(), server_default=sa.text("'v1.0'")),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── alerts ───────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("station_id", sa.String(), index=True),
        sa.Column("risk_level", sa.String()),
        sa.Column("title", sa.String()),
        sa.Column("message", sa.Text()),
        sa.Column("status", sa.String(), server_default=sa.text("'active'")),
        sa.Column("affected_population", sa.Integer(), server_default=sa.text("0")),
        sa.Column("nearby_villages", sa.Text()),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        # NOTE: sent_sms and sent_push were removed in prior cleanup
    )

    # ── citizen_reports ──────────────────────────────────────────────
    op.create_table(
        "citizen_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_type", sa.String()),
        sa.Column("description", sa.Text()),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("reporter_name", sa.String(), nullable=True),
        sa.Column("reporter_phone", sa.String(), nullable=True),
        sa.Column("reporter_language", sa.String(), server_default=sa.text("'en'")),
        sa.Column("status", sa.String(), server_default=sa.text("'pending'")),
        sa.Column("verified_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── weather_data ─────────────────────────────────────────────────
    op.create_table(
        "weather_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("station_id", sa.String(), index=True),
        sa.Column("temperature", sa.Float()),
        sa.Column("humidity", sa.Float()),
        sa.Column("rainfall_1h", sa.Float()),
        sa.Column("rainfall_24h", sa.Float()),
        sa.Column("rainfall_7d", sa.Float()),
        sa.Column("wind_speed", sa.Float()),
        sa.Column("wind_direction", sa.Float()),
        sa.Column("pressure", sa.Float()),
        sa.Column("visibility", sa.Float()),
        sa.Column("forecast_rainfall_24h", sa.Float()),
        sa.Column("forecast_rainfall_48h", sa.Float()),
        sa.Column("timestamp", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── road_status ──────────────────────────────────────────────────
    op.create_table(
        "road_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("road_name", sa.String()),
        sa.Column("road_type", sa.String()),
        sa.Column("start_lat", sa.Float()),
        sa.Column("start_lng", sa.Float()),
        sa.Column("end_lat", sa.Float()),
        sa.Column("end_lng", sa.Float()),
        sa.Column("status", sa.String(), server_default=sa.text("'open'")),
        sa.Column("blockage_reason", sa.String(), nullable=True),
        sa.Column("alternative_route", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── villages ─────────────────────────────────────────────────────
    op.create_table(
        "villages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String()),
        sa.Column("state", sa.String()),
        sa.Column("district", sa.String()),
        sa.Column("latitude", sa.Float()),
        sa.Column("longitude", sa.Float()),
        sa.Column("population", sa.Integer()),
        sa.Column("risk_zone", sa.String()),
        sa.Column("nearest_hospital_km", sa.Float()),
        sa.Column("nearest_police_km", sa.Float()),
        sa.Column("evacuation_route", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("villages")
    op.drop_table("road_status")
    op.drop_table("weather_data")
    op.drop_table("citizen_reports")
    op.drop_table("alerts")
    op.drop_table("risk_assessments")
    op.drop_table("sensor_readings")
    op.drop_table("sensor_stations")
