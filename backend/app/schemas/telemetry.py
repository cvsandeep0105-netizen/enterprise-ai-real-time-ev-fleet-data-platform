from datetime import datetime
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
CANONICAL_EVENT_TYPE = "EV_TELEMETRY"


class TelemetryEvent(BaseModel):
    """
    Canonical EV telemetry event contract.

    Governance rules:
    - Strict schema: unknown fields are rejected.
    - schema_version is explicitly governed.
    - timestamp accepts the legacy event_timestamp input name.
    - model_dump() always produces canonical field names.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    event_id: str = Field(
        min_length=1,
        max_length=100,
    )

    event_type: str = Field(
        default=CANONICAL_EVENT_TYPE,
        max_length=50,
    )

    schema_version: str = Field(
        default="1.0",
        max_length=20,
    )

    producer: str = Field(
        default="ev-telemetry-api",
        max_length=100,
    )

    vehicle_id: str = Field(
        min_length=1,
        max_length=50,
    )

    battery: float = Field(
        ge=0,
        le=100,
    )

    temp: float

    speed: float = Field(
        ge=0,
    )

    location: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    charging_status: Optional[str] = Field(
        default="NOT_CHARGING",
        max_length=30,
    )

    timestamp: datetime = Field(
        validation_alias=AliasChoices(
            "timestamp",
            "event_timestamp",
        )
    )

    ingestion_timestamp: Optional[datetime] = None

    battery_status: Optional[str] = Field(
        default=None,
        max_length=20,
    )

    vehicle_status: Optional[str] = Field(
        default=None,
        max_length=20,
    )

    temperature_status: Optional[str] = Field(
        default=None,
        max_length=20,
    )

    is_charging: Optional[bool] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, value: str) -> str:
        if value != CANONICAL_EVENT_TYPE:
            raise ValueError(
                f"Unsupported event_type: {value}. "
                f"Expected {CANONICAL_EVENT_TYPE}."
            )
        return value

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        if value not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValueError(
                f"Unsupported schema_version: {value}. "
                f"Supported versions: "
                f"{sorted(SUPPORTED_SCHEMA_VERSIONS)}"
            )
        return value


class TelemetryResponse(BaseModel):
    message: str
    event_id: str
    vehicle_id: str
    timestamp: datetime
