from datetime import datetime, timezone, timedelta

import pytest

from app.quality.data_quality import (
    DataQualityError,
    quality_result,
    validate_telemetry_quality,
)
from app.schemas.telemetry import TelemetryEvent


def make_event(**overrides):
    data = {
        "event_id": "quality-test-001",
        "event_type": "EV_TELEMETRY",
        "schema_version": "1.0",
        "producer": "quality-test",
        "vehicle_id": "EV001",
        "battery": 80,
        "temp": 30,
        "speed": 0,
        "location": "Bangalore",
        "charging_status": "NOT_CHARGING",
        "timestamp": datetime.now(timezone.utc) - timedelta(seconds=5),
        "ingestion_timestamp": datetime.now(timezone.utc),
        "vehicle_status": "STOPPED",
        "is_charging": False,
    }

    data.update(overrides)
    if "battery" in overrides and (overrides["battery"] < 0 or overrides["battery"] > 100):
        return TelemetryEvent.model_construct(**data)

    return TelemetryEvent(**data)


def assert_code(**overrides):
    event = make_event(**overrides)

    with pytest.raises(DataQualityError) as exc:
        validate_telemetry_quality(event)

    return exc.value.code


class TestDataQuality:

    def test_valid_event(self):
        assert validate_telemetry_quality(
            make_event()
        ).event_id == "quality-test-001"

    def test_battery_out_of_range(self):
        assert assert_code(battery=101) == "BATTERY_OUT_OF_RANGE"

    def test_negative_battery(self):
        assert assert_code(battery=-1) == "BATTERY_OUT_OF_RANGE"

    def test_temperature_out_of_range(self):
        assert assert_code(temp=101) == "TEMPERATURE_OUT_OF_RANGE"

    def test_speed_out_of_range(self):
        assert assert_code(speed=301) == "SPEED_OUT_OF_RANGE"

    def test_invalid_vehicle_status(self):
        assert assert_code(
            vehicle_status="FLYING"
        ) == "INVALID_VEHICLE_STATUS"

    def test_invalid_charging_status(self):
        assert assert_code(
            charging_status="UNKNOWN"
        ) == "INVALID_CHARGING_STATUS"

    def test_charging_flag_conflict(self):
        assert assert_code(
            charging_status="CHARGING",
            is_charging=False,
        ) == "CHARGING_STATUS_CONFLICT"

    def test_charging_movement_conflict(self):
        assert assert_code(
            charging_status="CHARGING",
            is_charging=True,
            speed=20,
            vehicle_status="MOVING",
        ) == "CHARGING_MOVEMENT_CONFLICT"

    def test_stopped_movement_conflict(self):
        assert assert_code(
            vehicle_status="STOPPED",
            speed=20,
        ) == "VEHICLE_STATUS_CONFLICT"

    def test_moving_zero_speed_conflict(self):
        assert assert_code(
            vehicle_status="MOVING",
            speed=0,
        ) == "VEHICLE_STATUS_CONFLICT"

    def test_future_timestamp(self):
        assert assert_code(
            timestamp=datetime.now(timezone.utc) + timedelta(minutes=5)
        ) == "FUTURE_TIMESTAMP"

    def test_ingestion_before_event(self):
        event_time = datetime.now(timezone.utc) - timedelta(minutes=5)

        assert assert_code(
            timestamp=event_time,
            ingestion_timestamp=event_time - timedelta(minutes=1),
        ) == "TIMESTAMP_ORDER_ERROR"

    def test_quality_result_success(self):
        result = quality_result(make_event())

        assert result["valid"] is True
        assert result["quality_code"] == "QUALITY_OK"

    def test_quality_result_failure(self):
        result = quality_result(
            make_event(battery=150)
        )

        assert result["valid"] is False
        assert result["quality_code"] == "BATTERY_OUT_OF_RANGE"


