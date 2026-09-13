"""align alerts and vehicles with canonical ORM

Revision ID: a5_schema_alignment
Revises: ee4c3478d994
Create Date: 2026-08-28
"""

from alembic import op
import sqlalchemy as sa


revision = "a5_schema_alignment"
down_revision = "ee4c3478d994"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --------------------------------------------------------
    # ALERTS
    # --------------------------------------------------------

    op.alter_column(
        "alerts",
        "id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )

    op.alter_column(
        "alerts",
        "vehicle_id",
        existing_type=sa.String(length=100),
        type_=sa.String(length=50),
        existing_nullable=False,
    )

    op.alter_column(
        "alerts",
        "severity",
        existing_type=sa.String(length=100),
        type_=sa.String(length=30),
        existing_nullable=True,
        nullable=False,
    )

    op.alter_column(
        "alerts",
        "message",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.alter_column(
        "alerts",
        "status",
        existing_type=sa.String(length=100),
        type_=sa.String(length=20),
        existing_nullable=True,
        nullable=False,
    )

    op.alter_column(
        "alerts",
        "timestamp",
        existing_type=sa.DateTime(),
        nullable=False,
    )

    op.drop_index(
        "ix_alerts_id",
        table_name="alerts",
    )

    op.create_index(
        "idx_alerts_vehicle_status_timestamp",
        "alerts",
        ["vehicle_id", "status", "timestamp"],
        unique=False,
    )

    # --------------------------------------------------------
    # VEHICLES
    # --------------------------------------------------------

    op.alter_column(
        "vehicles",
        "id",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
    )

    op.alter_column(
        "vehicles",
        "vehicle_id",
        existing_type=sa.String(),
        type_=sa.String(length=50),
        existing_nullable=True,
        nullable=False,
    )

    op.alter_column(
        "vehicles",
        "battery",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
    )

    op.alter_column(
        "vehicles",
        "speed",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
    )

    op.drop_index(
        "ix_vehicles_id",
        table_name="vehicles",
    )


def downgrade() -> None:
    # Reverse VEHICLES
    op.create_index(
        "ix_vehicles_id",
        "vehicles",
        ["id"],
        unique=False,
    )

    op.alter_column(
        "vehicles",
        "speed",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
    )

    op.alter_column(
        "vehicles",
        "battery",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
    )

    op.alter_column(
        "vehicles",
        "vehicle_id",
        existing_type=sa.String(length=50),
        type_=sa.String(),
        existing_nullable=False,
        nullable=True,
    )

    op.alter_column(
        "vehicles",
        "id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )

    # Reverse ALERTS
    op.drop_index(
        "idx_alerts_vehicle_status_timestamp",
        table_name="alerts",
    )

    op.create_index(
        "ix_alerts_id",
        "alerts",
        ["id"],
        unique=False,
    )

    op.alter_column(
        "alerts",
        "timestamp",
        existing_type=sa.DateTime(),
        nullable=True,
    )

    op.alter_column(
        "alerts",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=100),
        existing_nullable=False,
        nullable=True,
    )

    op.alter_column(
        "alerts",
        "message",
        existing_type=sa.Text(),
        nullable=False,
    )

    op.alter_column(
        "alerts",
        "severity",
        existing_type=sa.String(length=30),
        type_=sa.String(length=100),
        existing_nullable=False,
        nullable=True,
    )

    op.alter_column(
        "alerts",
        "vehicle_id",
        existing_type=sa.String(length=50),
        type_=sa.String(length=100),
        existing_nullable=False,
    )

    op.alter_column(
        "alerts",
        "id",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
    )
