"""persistent users and sensor ingestion provenance

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column("source", sa.String(), nullable=False, server_default="legacy"),
    )
    op.add_column(
        "sensor_readings",
        sa.Column("external_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_sensor_readings_source",
        "sensor_readings",
        ["source"],
        unique=False,
    )
    op.create_index(
        "ix_sensor_readings_external_id",
        "sensor_readings",
        ["external_id"],
        unique=True,
    )

    op.create_table(
        "user_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="citizen"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_user_accounts_id", "user_accounts", ["id"], unique=False)
    op.create_index("ix_user_accounts_email", "user_accounts", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_accounts_email", table_name="user_accounts")
    op.drop_index("ix_user_accounts_id", table_name="user_accounts")
    op.drop_table("user_accounts")

    op.drop_index("ix_sensor_readings_external_id", table_name="sensor_readings")
    op.drop_index("ix_sensor_readings_source", table_name="sensor_readings")
    op.drop_column("sensor_readings", "external_id")
    op.drop_column("sensor_readings", "source")
