from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    Central application configuration.

    Configuration is supplied through environment variables and the
    backend .env file for local development. Production deployments
    must provide a strong JWT secret explicitly.
    """

    app_name: str = "EV Fleet Data Platform API"
    app_version: str = "1.0.0"

    environment: str = Field(
        default="development",
        validation_alias="APP_ENVIRONMENT",
    )

    debug: bool = Field(
        default=False,
        validation_alias="APP_DEBUG",
    )

    postgres_user: str = Field(
        validation_alias="POSTGRES_USER",
    )

    postgres_password: str = Field(
        validation_alias="POSTGRES_PASSWORD",
    )

    postgres_host: str = Field(
        default="localhost",
        validation_alias="POSTGRES_HOST",
    )

    postgres_port: int = Field(
        default=5433,
        validation_alias="POSTGRES_PORT",
    )

    postgres_db: str = Field(
        default="airflow",
        validation_alias="POSTGRES_DB",
    )

    kafka_broker: str = Field(
        default="localhost:29092",
        validation_alias="KAFKA_BROKER",
    )

    kafka_topic: str = Field(
        default="ev.telemetry.v1",
        validation_alias="KAFKA_TOPIC",
    )

    producer_interval_seconds: float = Field(
        default=2.0,
        validation_alias="PRODUCER_INTERVAL_SECONDS",
    )
    jwt_secret_key: str = Field(validation_alias="JWT_SECRET_KEY", repr=False)

    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias="JWT_ALGORITHM",
    )

    jwt_access_token_expire_minutes: int = Field(
        default=30,
        validation_alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    cors_origins: str = Field(
        default="http://localhost:5173",
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        value = value.strip().lower()
        allowed = {"development", "testing", "staging", "production"}
        if value not in allowed:
            raise ValueError(
                f"APP_ENVIRONMENT must be one of: {sorted(allowed)}"
            )
        return value

    @field_validator("postgres_port")
    @classmethod
    def validate_postgres_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("POSTGRES_PORT must be between 1 and 65535")
        return value

    @field_validator("producer_interval_seconds")
    @classmethod
    def validate_producer_interval(cls, value: float) -> float:
        if value <= 0:
            raise ValueError(
                "PRODUCER_INTERVAL_SECONDS must be greater than zero"
            )
        return value

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must contain at least 32 characters"
            )

        return value

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, value: str) -> str:
        value = value.strip().upper()

        if value != "HS256":
            raise ValueError("JWT_ALGORITHM must be HS256")

        return value

    @field_validator("jwt_access_token_expire_minutes")
    @classmethod
    def validate_jwt_expiration(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than zero"
            )
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    def validate_production_security(self) -> None:
        """
        Enforce security requirements that only apply to production.
        Development/testing retain a deterministic local secret so the
        existing test suite remains self-contained.
        """
        if self.environment != "production":
            return

        insecure_markers = (
            "AREA21_DEVELOPMENT_SECRET",
            "CHANGE_ME",
            "SECRET_CHANGE_ME",
        )

        if any(marker in self.jwt_secret_key for marker in insecure_markers):
            raise ValueError(
                "Production requires an explicitly configured JWT_SECRET_KEY"
            )

        if self.debug:
            raise ValueError(
                "APP_DEBUG must be false in production"
            )


@lru_cache
def get_settings() -> Settings:
    configuration = Settings()
    configuration.validate_production_security()
    return configuration


settings = get_settings()

