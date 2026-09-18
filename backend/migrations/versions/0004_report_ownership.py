"""scope citizen reports to the submitting account

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "citizen_reports",
        sa.Column("submitted_by", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_citizen_reports_submitted_by",
        "citizen_reports",
        ["submitted_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_citizen_reports_submitted_by",
        table_name="citizen_reports",
    )
    op.drop_column("citizen_reports", "submitted_by")
