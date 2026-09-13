import sys
from datetime import datetime, timedelta, timezone

import pytest

from app.spark.session import create_spark_session
from app.spark.batch import process_batch
from app.spark.transformations import (
    vehicle_latest,
    vehicle_aggregates,
    time_window_aggregates,
    repartition_for_vehicle,
)


@pytest.fixture(scope="module")
def spark():
    session = create_spark_session(
        "EV-Fleet-Area11-Test"
    )
    yield session
    session.stop()


def records():
    now = datetime.now(timezone.utc).replace(
        tzinfo=None
    )

    return [
        (
            "e1", "EV_TELEMETRY", "1.0", "test",
            "ev001", 85.0, 30.0, 40.0,
            "Bangalore", "NOT_CHARGING",
            now - timedelta(minutes=4),
            now,
            "MOVING", False,
        ),
        (
            "e2", "EV_TELEMETRY", "1.0", "test",
            "ev001", 15.0, 35.0, 20.0,
            "Bangalore", "NOT_CHARGING",
            now - timedelta(minutes=2),
            now,
            "MOVING", False,
        ),
        (
            "e3", "EV_TELEMETRY", "1.0", "test",
            "ev002", 5.0, 90.0, 120.0,
            "Hyderabad", "CHARGING",
            now - timedelta(minutes=1),
            now,
            "STOPPED", True,
        ),
        (
            "e4", "EV_TELEMETRY", "1.0", "test",
            "ev003", 75.0, 30.0, 40.0,
            "Delhi", "NOT_CHARGING",
            now,
            now,
            "MOVING", False,
        ),
        (
            "e5", "EV_TELEMETRY", "1.0", "test",
            "ev004", 110.0, 30.0, 40.0,
            "Mumbai", "NOT_CHARGING",
            now,
            now,
            "MOVING", False,
        ),
    ]

def test_spark_session(spark):
    assert spark.version.startswith("3.5")


def test_explicit_schema(spark):
    result = process_batch(spark, records())
    assert result["raw"].schema["vehicle_id"].dataType.simpleString() == "string"
    assert result["raw"].schema["battery"].dataType.simpleString() == "double"


def test_dataframe_count(spark):
    result = process_batch(spark, records())
    assert result["raw"].count() == 5


def test_normalization(spark):
    result = process_batch(spark, records())
    row = (
        result["transformed"]
        .filter("vehicle_id = 'EV001'")
        .first()
    )
    assert row.vehicle_id == "EV001"


def test_battery_classification(spark):
    result = process_batch(spark, records())
    row = (
        result["transformed"]
        .filter("event_id = 'e2'")
        .first()
    )
    assert row.battery_status == "LOW"


def test_temperature_classification(spark):
    result = process_batch(spark, records())
    row = (
        result["transformed"]
        .filter("event_id = 'e3'")
        .first()
    )
    assert row.temperature_status == "CRITICAL"


def test_overspeed_classification(spark):
    result = process_batch(spark, records())
    row = (
        result["transformed"]
        .filter("event_id = 'e3'")
        .first()
    )
    assert row.speed_status == "OVERSPEED"


def test_charging_normalization(spark):
    result = process_batch(spark, records())
    row = (
        result["transformed"]
        .filter("event_id = 'e3'")
        .first()
    )
    assert row.is_charging is True


def test_quality_classification(spark):
    result = process_batch(spark, records())

    valid_count = result["valid"].count()
    invalid_count = result["invalid"].count()

    assert valid_count == 4
    assert invalid_count == 1


def test_latest_per_vehicle(spark):
    result = process_batch(spark, records())
    latest = vehicle_latest(result["valid"])

    assert latest.count() == 3


def test_vehicle_aggregates(spark):
    result = process_batch(spark, records())
    aggregates = vehicle_aggregates(result["valid"])

    assert aggregates.count() == 3


def test_window_aggregates(spark):
    result = process_batch(spark, records())
    windows = time_window_aggregates(
        result["valid"]
    )

    assert windows.count() >= 1


def test_repartitioning(spark):
    result = process_batch(spark, records())
    repartitioned = repartition_for_vehicle(
        result["valid"],
        4,
    )

    assert repartitioned.rdd.getNumPartitions() == 4


def test_deterministic_order(spark):
    result = process_batch(spark, records())

    ordered = result["valid"].orderBy(
        "vehicle_id",
        "timestamp",
        "event_id",
    )

    rows = ordered.collect()

    assert rows == sorted(
        rows,
        key=lambda r: (
            r.vehicle_id,
            r.timestamp,
            r.event_id,
        ),
    )













