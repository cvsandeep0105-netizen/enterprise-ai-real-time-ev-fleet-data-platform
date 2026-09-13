from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping


@dataclass(frozen=True)
class StorageRecord:
    record_id: str
    event_type: str
    event_time: datetime
    payload: Mapping[str, Any]


class WarehouseService:
    """
    Deterministic application-level storage contract.

    Persistence adapters may consume StorageRecord instances without
    coupling ingestion to a specific database or warehouse engine.
    """

    @staticmethod
    def _canonical_payload(payload: Mapping[str, Any]) -> str:
        items = sorted(
            ((str(key), repr(value)) for key, value in payload.items()),
            key=lambda item: item[0],
        )
        return repr(items)

    def build_record(
        self,
        *,
        event_type: str,
        event_time: datetime,
        payload: Mapping[str, Any],
        source_id: str | None = None,
    ) -> StorageRecord:
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError("event_type must not be empty")

        normalized_type = event_type.strip()

        if not isinstance(event_time, datetime):
            raise TypeError("event_time must be a datetime")

        if event_time.tzinfo is None or event_time.utcoffset() is None:
            raise ValueError("event_time must be timezone-aware")

        if not isinstance(payload, Mapping):
            raise TypeError("payload must be a mapping")

        if source_id is not None and (
            not isinstance(source_id, str) or not source_id.strip()
        ):
            raise ValueError("source_id must be non-empty when provided")

        normalized_time = event_time.astimezone(timezone.utc)
        normalized_source = source_id.strip() if source_id else ""

        canonical = "|".join(
            (
                normalized_type,
                normalized_time.isoformat(),
                normalized_source,
                self._canonical_payload(payload),
            )
        )

        record_id = sha256(canonical.encode("utf-8")).hexdigest()

        return StorageRecord(
            record_id=record_id,
            event_type=normalized_type,
            event_time=normalized_time,
            payload=dict(payload),
        )


_service = WarehouseService()


def get_warehouse_service() -> WarehouseService:
    return _service
