from datetime import datetime, timezone, timedelta

import pytest

from app.warehouse import WarehouseService, get_warehouse_service


def test_service_singleton_is_available():
    assert isinstance(get_warehouse_service(), WarehouseService)


def test_record_id_is_deterministic():
    service = WarehouseService()
    t = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    payload = {"vehicle_id": "EV-001", "battery_soc": 87.5}

    a = service.build_record(
        event_type="telemetry",
        event_time=t,
        payload=payload,
        source_id="EV-001",
    )
    b = service.build_record(
        event_type="telemetry",
        event_time=t,
        payload=payload,
        source_id="EV-001",
    )

    assert a.record_id == b.record_id
    assert len(a.record_id) == 64
    assert all(c in "0123456789abcdef" for c in a.record_id)


def test_payload_dictionary_order_does_not_change_identity():
    service = WarehouseService()
    t = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    a = service.build_record(
        event_type="telemetry",
        event_time=t,
        payload={"vehicle_id": "EV-001", "soc": 90},
    )
    b = service.build_record(
        event_type="telemetry",
        event_time=t,
        payload={"soc": 90, "vehicle_id": "EV-001"},
    )

    assert a.record_id == b.record_id


def test_different_payload_changes_identity():
    service = WarehouseService()
    t = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    a = service.build_record(
        event_type="telemetry",
        event_time=t,
        payload={"vehicle_id": "EV-001", "soc": 90},
    )
    b = service.build_record(
        event_type="telemetry",
        event_time=t,
        payload={"vehicle_id": "EV-001", "soc": 91},
    )

    assert a.record_id != b.record_id


def test_different_event_time_changes_identity():
    service = WarehouseService()
    payload = {"vehicle_id": "EV-001"}

    a = service.build_record(
        event_type="telemetry",
        event_time=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        payload=payload,
    )
    b = service.build_record(
        event_type="telemetry",
        event_time=datetime(2026, 1, 1, 12, 0, 1, tzinfo=timezone.utc),
        payload=payload,
    )

    assert a.record_id != b.record_id


def test_different_event_type_changes_identity():
    service = WarehouseService()
    t = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    payload = {"vehicle_id": "EV-001"}

    a = service.build_record(
        event_type="telemetry",
        event_time=t,
        payload=payload,
    )
    b = service.build_record(
        event_type="alert",
        event_time=t,
        payload=payload,
    )

    assert a.record_id != b.record_id


def test_different_source_changes_identity():
    service = WarehouseService()
    t = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    payload = {"vehicle_id": "EV-001"}

    a = service.build_record(
        event_type="telemetry",
        event_time=t,
        payload=payload,
        source_id="source-a",
    )
    b = service.build_record(
        event_type="telemetry",
        event_time=t,
        payload=payload,
        source_id="source-b",
    )

    assert a.record_id != b.record_id


def test_timezone_is_normalized_to_utc():
    service = WarehouseService()
    local_time = datetime.fromisoformat("2026-01-01T17:30:00+05:30")

    record = service.build_record(
        event_type="telemetry",
        event_time=local_time,
        payload={"vehicle_id": "EV-001"},
    )

    assert record.event_time == datetime(
        2026, 1, 1, 12, 0, tzinfo=timezone.utc
    )


def test_naive_timestamp_is_rejected():
    service = WarehouseService()

    with pytest.raises(ValueError, match="timezone-aware"):
        service.build_record(
            event_type="telemetry",
            event_time=datetime(2026, 1, 1, 12, 0),
            payload={},
        )


def test_non_datetime_timestamp_is_rejected():
    service = WarehouseService()

    with pytest.raises(TypeError):
        service.build_record(
            event_type="telemetry",
            event_time="2026-01-01T12:00:00Z",
            payload={},
        )


def test_empty_event_type_is_rejected():
    service = WarehouseService()

    with pytest.raises(ValueError):
        service.build_record(
            event_type="   ",
            event_time=datetime.now(timezone.utc),
            payload={},
        )


def test_non_mapping_payload_is_rejected():
    service = WarehouseService()

    with pytest.raises(TypeError):
        service.build_record(
            event_type="telemetry",
            event_time=datetime.now(timezone.utc),
            payload=[],
        )


def test_empty_source_is_rejected():
    service = WarehouseService()

    with pytest.raises(ValueError):
        service.build_record(
            event_type="telemetry",
            event_time=datetime.now(timezone.utc),
            payload={},
            source_id="   ",
        )


def test_payload_is_copied_not_aliased():
    service = WarehouseService()
    payload = {"vehicle_id": "EV-001", "soc": 90}

    record = service.build_record(
        event_type="telemetry",
        event_time=datetime.now(timezone.utc),
        payload=payload,
    )

    payload["soc"] = 10

    assert record.payload["soc"] == 90


def test_event_type_and_source_are_normalized():
    service = WarehouseService()

    record = service.build_record(
        event_type="  telemetry  ",
        event_time=datetime.now(timezone.utc),
        payload={},
        source_id="  EV-001  ",
    )

    assert record.event_type == "telemetry"


def test_realistic_ev_payload_is_accepted():
    service = WarehouseService()

    payload = {
        "vehicle_id": "EV-042",
        "battery_soc": 73.4,
        "battery_voltage": 398.7,
        "battery_temperature": 31.8,
        "speed_kmh": 64.2,
        "latitude": 17.385,
        "longitude": 78.4867,
        "status": "DRIVING",
    }

    record = service.build_record(
        event_type="telemetry",
        event_time=datetime.now(timezone.utc),
        payload=payload,
        source_id="EV-042",
    )

    assert record.record_id
    assert record.payload["vehicle_id"] == "EV-042"
    assert record.payload["battery_soc"] == 73.4
