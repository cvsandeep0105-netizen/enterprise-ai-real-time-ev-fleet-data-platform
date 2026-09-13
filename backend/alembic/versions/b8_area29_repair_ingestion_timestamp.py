"""Area 29: repair ingestion timestamp

Revision ID: b8_ingest_ts
Revises: b7_ingest_ts
"""

from alembic import op

revision = "b8_ingest_ts"
down_revision = "b7_ingest_ts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE ev_data ADD COLUMN IF NOT EXISTS ingestion_timestamp TIMESTAMP NULL"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE ev_data DROP COLUMN IF EXISTS ingestion_timestamp"
    )