"""add web push subscriptions and notification delivery logs

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_email", sa.String(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.Text(), nullable=False),
        sa.Column("auth", sa.Text(), nullable=False),
        sa.Column("district", sa.String(), nullable=False, server_default="all"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_push_subscriptions_user_email", "push_subscriptions", ["user_email"])
    op.create_index("ix_push_subscriptions_district", "push_subscriptions", ["district"])
    op.create_unique_constraint("uq_push_subscriptions_endpoint", "push_subscriptions", ["endpoint"])

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("alert_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("recipient", sa.String(), nullable=True),
        sa.Column("district", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_notification_deliveries_alert_id", "notification_deliveries", ["alert_id"])
    op.create_index("ix_notification_deliveries_channel", "notification_deliveries", ["channel"])
    op.create_index("ix_notification_deliveries_district", "notification_deliveries", ["district"])
    op.create_index("ix_notification_deliveries_status", "notification_deliveries", ["status"])


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_status", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_district", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_channel", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_alert_id", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")

    op.drop_constraint("uq_push_subscriptions_endpoint", "push_subscriptions", type_="unique")
    op.drop_index("ix_push_subscriptions_district", table_name="push_subscriptions")
    op.drop_index("ix_push_subscriptions_user_email", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")
