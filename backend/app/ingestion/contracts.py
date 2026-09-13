from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(str, Enum):
    CSV = "csv"
    JSON = "json"


class IngestionStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PARTIAL = "partial"


class IngestionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str = Field(min_length=1, max_length=200)
    source_type: SourceType
    batch_id: str = Field(min_length=1, max_length=200)
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = Field(default="1.0", min_length=1, max_length=50)

    @field_validator("source_name", "batch_id", "schema_version")
    @classmethod
    def strip_values(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value


class IngestionRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    record_id: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any]


class IngestionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: IngestionStatus
    metadata: IngestionMetadata
    records: list[IngestionRecord] = Field(default_factory=list)
    accepted_count: int = Field(default=0, ge=0)
    rejected_count: int = Field(default=0, ge=0)
    error_count: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)

    @property
    def total_count(self) -> int:
        return self.accepted_count + self.rejected_count
