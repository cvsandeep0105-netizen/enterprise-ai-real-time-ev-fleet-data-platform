import pytest
from pydantic import ValidationError

from app.core.config import Settings, settings


def test_settings_import():
    assert settings.app_name == "EV Fleet Data Platform API"


def test_environment_contract():
    assert settings.environment in {
        "development",
        "testing",
        "staging",
        "production",
    }


def test_jwt_configuration_contract():
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_minutes > 0
    assert len(settings.jwt_secret_key) >= 32


def test_cors_configuration_contract():
    assert settings.cors_origin_list
    assert "http://localhost:5173" in settings.cors_origin_list


def test_database_configuration_contract():
    assert settings.postgres_user
    assert settings.postgres_password
    assert settings.postgres_host
    assert 1 <= settings.postgres_port <= 65535
    assert settings.postgres_db


def test_kafka_configuration_contract():
    assert settings.kafka_broker
    assert settings.kafka_topic
    assert settings.producer_interval_seconds > 0


def test_invalid_environment_rejected():
    with pytest.raises(ValidationError):
        Settings(
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test",
            APP_ENVIRONMENT="invalid-environment",
        )


def test_short_jwt_secret_rejected():
    with pytest.raises(ValidationError):
        Settings(
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test",
            JWT_SECRET_KEY="too-short",
        )


def test_invalid_jwt_algorithm_rejected():
    with pytest.raises(ValidationError):
        Settings(
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test",
            JWT_ALGORITHM="RS256",
        )


def test_invalid_postgres_port_rejected():
    with pytest.raises(ValidationError):
        Settings(
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test",
            POSTGRES_PORT=70000,
        )


def test_invalid_producer_interval_rejected():
    with pytest.raises(ValidationError):
        Settings(
            POSTGRES_USER="test",
            POSTGRES_PASSWORD="test",
            PRODUCER_INTERVAL_SECONDS=0,
        )


def test_production_rejects_development_secret():
    production = Settings(
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        APP_ENVIRONMENT="production",
        JWT_SECRET_KEY="AREA21_DEVELOPMENT_SECRET_CHANGE_ME_32CHARS",
    )

    with pytest.raises(ValueError):
        production.validate_production_security()


def test_production_rejects_debug_mode():
    production = Settings(
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        APP_ENVIRONMENT="production",
        APP_DEBUG=True,
        JWT_SECRET_KEY="A" * 64,
    )

    with pytest.raises(ValueError):
        production.validate_production_security()


def test_production_accepts_secure_configuration():
    production = Settings(
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        APP_ENVIRONMENT="production",
        APP_DEBUG=False,
        JWT_SECRET_KEY="A" * 64,
    )

    production.validate_production_security()


def test_configuration_does_not_expose_secret_in_repr():
    value = "A" * 64
    production = Settings(
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        JWT_SECRET_KEY=value,
    )

    rendered = repr(production)
    assert value not in rendered
