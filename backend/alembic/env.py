from pathlib import Path
import sys
from logging.config import fileConfig

# Make backend/ importable when Alembic runs from the project root.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.database.database import Base

# Import the canonical application ORM models.
from app.models.database_models import (
    Telemetry,
    Alert,
    Vehicle,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = (
    "postgresql+psycopg2://"
    f"{settings.postgres_user}:"
    f"{settings.postgres_password}@"
    f"{settings.postgres_host}:"
    f"{settings.postgres_port}/"
    f"{settings.postgres_db}"
)

config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    """
    Only manage tables represented by the application's SQLAlchemy metadata.
    Do not attempt to delete unrelated tables such as Airflow metadata.
    """
    if type_ == "table" and reflected and compare_to is None:
        return False

    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
