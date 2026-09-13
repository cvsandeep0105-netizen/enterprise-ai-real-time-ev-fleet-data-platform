"""Area 29: add ingestion timestamp

Revision ID: b7_ingest_ts
Revises: a5_schema_alignment
"""

from alembic import op
import sqlalchemy as sa

revision = "b7_ingest_ts"
down_revision = "a5_schema_alignment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ev_data",
        sa.Column(
            "ingestion_timestamp",
            sa.DateTime(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("ev_data", "ingestion_timestamp")