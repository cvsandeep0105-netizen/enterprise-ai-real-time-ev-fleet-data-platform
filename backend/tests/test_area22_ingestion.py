from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from app.ingestion import (
    IngestionMetadata,
    IngestionService,
    IngestionStatus,
    SourceType,
)


def metadata(source_type=SourceType.JSON):
    return IngestionMetadata(
        source_name="ev.telemetry",
        source_type=source_type,
        batch_id="batch-001",
    )


def test_ingestion_accepts_valid_records():
    result = IngestionService().ingest_records(
        [{"vehicle_id": "EV001", "soc": 82}],
        metadata(),
    )
    assert result.status == IngestionStatus.ACCEPTED
    assert result.accepted_count == 1
    assert result.rejected_count == 0
    assert len(result.records[0].record_id) == 64


def test_record_id_is_deterministic():
    service = IngestionService()
    first = service.ingest_records(
        [{"vehicle_id": "EV001", "soc": 82}],
        metadata(),
    )
    second = service.ingest_records(
        [{"vehicle_id": "EV001", "soc": 82}],
        metadata(),
    )
    assert first.records[0].record_id == second.records[0].record_id


def test_duplicate_records_are_rejected():
    result = IngestionService().ingest_records(
        [
            {"vehicle_id": "EV001", "soc": 82},
            {"vehicle_id": "EV001", "soc": 82},
        ],
        metadata(),
    )
    assert result.status == IngestionStatus.PARTIAL
    assert result.accepted_count == 1
    assert result.rejected_count == 1


def test_empty_payload_is_rejected():
    result = IngestionService().ingest_records(
        [{}],
        metadata(),
    )
    assert result.status == IngestionStatus.REJECTED
    assert result.accepted_count == 0
    assert result.rejected_count == 1


def test_non_object_payload_is_rejected():
    result = IngestionService().ingest_records(
        [None],  # type: ignore[list-item]
        metadata(),
    )
    assert result.status == IngestionStatus.REJECTED


def test_metadata_rejects_empty_source_name():
    with pytest.raises(ValueError):
        IngestionMetadata(
            source_name=" ",
            source_type=SourceType.JSON,
            batch_id="batch-001",
        )


def test_metadata_rejects_empty_batch_id():
    with pytest.raises(ValueError):
        IngestionMetadata(
            source_name="ev.telemetry",
            source_type=SourceType.JSON,
            batch_id=" ",
        )


def test_metadata_has_utc_timestamp():
    value = metadata()
    assert value.received_at.tzinfo is not None
    assert value.received_at.utcoffset() == timezone.utc.utcoffset(value.received_at)


def test_json_file_ingestion(tmp_path):
    source = tmp_path / "telemetry.json"
    source.write_text(
        json.dumps(
            [
                {"vehicle_id": "EV001", "soc": 80},
                {"vehicle_id": "EV002", "soc": 75},
            ]
        ),
        encoding="utf-8",
    )

    result = IngestionService().ingest_file(source, metadata())
    assert result.status == IngestionStatus.ACCEPTED
    assert result.accepted_count == 2


def test_csv_file_ingestion(tmp_path):
    source = tmp_path / "telemetry.csv"
    source.write_text(
        "vehicle_id,soc\nEV001,80\nEV002,75\n",
        encoding="utf-8",
    )

    result = IngestionService().ingest_file(
        source,
        metadata(SourceType.CSV),
    )
    assert result.status == IngestionStatus.ACCEPTED
    assert result.accepted_count == 2


def test_wrong_source_type_is_rejected(tmp_path):
    source = tmp_path / "telemetry.csv"
    source.write_text("vehicle_id,soc\nEV001,80\n", encoding="utf-8")

    with pytest.raises(Exception):
        IngestionService().ingest_file(source, metadata(SourceType.JSON))


def test_unsupported_format_is_rejected(tmp_path):
    source = tmp_path / "telemetry.txt"
    source.write_text("data", encoding="utf-8")

    with pytest.raises(Exception):
        IngestionService().ingest_file(
            source,
            metadata(SourceType.JSON),
        )


def test_missing_file_is_rejected(tmp_path):
    with pytest.raises(Exception):
        IngestionService().ingest_file(
            tmp_path / "missing.json",
            metadata(),
        )


def test_json_object_is_supported(tmp_path):
    source = tmp_path / "telemetry.json"
    source.write_text(
        json.dumps({"vehicle_id": "EV001", "soc": 91}),
        encoding="utf-8",
    )

    result = IngestionService().ingest_file(source, metadata())
    assert result.accepted_count == 1


def test_result_metadata_is_preserved():
    value = metadata()
    result = IngestionService().ingest_records(
        [{"vehicle_id": "EV001"}],
        value,
    )
    assert result.metadata.batch_id == "batch-001"
    assert result.metadata.source_name == "ev.telemetry"
