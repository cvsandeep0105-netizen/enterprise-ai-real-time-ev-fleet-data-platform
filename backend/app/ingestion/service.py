from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from .contracts import (
    IngestionMetadata,
    IngestionRecord,
    IngestionResult,
    IngestionStatus,
    SourceType,
)
from .exceptions import IngestionValidationError


class IngestionService:
    """
    Deterministic, dependency-light ingestion boundary.

    External systems such as Kafka, object storage, databases, and
    orchestration are intentionally kept outside this service. This
    component establishes the canonical record/metadata contract that
    those systems can consume.
    """

    MAX_RECORDS = 100_000

    def ingest_records(
        self,
        records: Iterable[dict[str, Any]],
        metadata: IngestionMetadata,
    ) -> IngestionResult:
        accepted: list[IngestionRecord] = []
        errors: list[str] = []
        seen: set[str] = set()

        for index, payload in enumerate(records):
            if index >= self.MAX_RECORDS:
                errors.append(
                    f"batch exceeds maximum record limit of {self.MAX_RECORDS}"
                )
                break

            if not isinstance(payload, dict) or not payload:
                errors.append(f"record {index}: payload must be a non-empty object")
                continue

            record_id = self._record_id(metadata, payload)

            if record_id in seen:
                errors.append(f"record {index}: duplicate record")
                continue

            seen.add(record_id)
            accepted.append(
                IngestionRecord(
                    record_id=record_id,
                    payload=payload,
                )
            )

        rejected = len(errors)
        status = (
            IngestionStatus.ACCEPTED
            if rejected == 0
            else IngestionStatus.PARTIAL
            if accepted
            else IngestionStatus.REJECTED
        )

        return IngestionResult(
            status=status,
            metadata=metadata,
            records=accepted,
            accepted_count=len(accepted),
            rejected_count=rejected,
            error_count=rejected,
            errors=errors,
        )

    def ingest_file(
        self,
        path: str | Path,
        metadata: IngestionMetadata,
    ) -> IngestionResult:
        file_path = Path(path)

        if not file_path.exists():
            raise IngestionValidationError(
                f"source file does not exist: {file_path}"
            )

        if not file_path.is_file():
            raise IngestionValidationError(
                f"source path is not a file: {file_path}"
            )

        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            if metadata.source_type != SourceType.CSV:
                raise IngestionValidationError(
                    "metadata source_type does not match CSV file"
                )
            records = self._read_csv(file_path)
        elif suffix == ".json":
            if metadata.source_type != SourceType.JSON:
                raise IngestionValidationError(
                    "metadata source_type does not match JSON file"
                )
            records = self._read_json(file_path)
        else:
            raise IngestionValidationError(
                f"unsupported ingestion format: {suffix or '<none>'}"
            )

        return self.ingest_records(records, metadata)

    @staticmethod
    def _record_id(
        metadata: IngestionMetadata,
        payload: dict[str, Any],
    ) -> str:
        canonical = json.dumps(
            {
                "source_name": metadata.source_name,
                "schema_version": metadata.schema_version,
                "payload": payload,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def _read_csv(path: Path) -> list[dict[str, Any]]:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))

    @staticmethod
    def _read_json(path: Path) -> list[dict[str, Any]]:
        try:
            with path.open("r", encoding="utf-8-sig") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise IngestionValidationError(
                f"invalid JSON source: {exc.msg}"
            ) from exc

        if isinstance(data, dict):
            return [data]

        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return data

        raise IngestionValidationError(
            "JSON source must contain an object or an array of objects"
        )
