"""bootstrap historical application schema

Revision ID: 9f2c7a1b4d60
Revises:
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa

revision = "9f2c7a1b4d60"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.String(length=100), nullable=True),
        sa.Column("alert_type", sa.String(length=50), nullable=True),
        sa.Column("alert_value", sa.Float(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True, server_default=sa.text("'ACTIVE'")),
        sa.Column("timestamp", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "ev_data",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("event_id", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=True),
        sa.Column("schema_version", sa.String(length=20), nullable=True),
        sa.Column("producer", sa.String(length=100), nullable=True),
        sa.Column("vehicle_id", sa.Text(), nullable=True),
        sa.Column("battery", sa.BigInteger(), nullable=True),
        sa.Column("temp", sa.BigInteger(), nullable=True),
        sa.Column("speed", sa.BigInteger(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("charging_status", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.Text(), nullable=True),
        sa.Column("battery_status", sa.Text(), nullable=True),
        sa.Column("vehicle_status", sa.Text(), nullable=True),
        sa.Column("temperature_status", sa.Text(), nullable=True),
        sa.Column("is_charging", sa.Boolean(), nullable=True),
    )

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.String(), nullable=True),
        sa.Column("battery", sa.Integer(), nullable=True),
        sa.Column("speed", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
    )
    op.create_index("ix_vehicles_id", "vehicles", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False, server_default=sa.text("'user'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
    op.drop_index("ix_vehicles_id", table_name="vehicles")
    op.drop_table("vehicles")
    op.drop_table("ev_data")
    op.drop_table("alerts")