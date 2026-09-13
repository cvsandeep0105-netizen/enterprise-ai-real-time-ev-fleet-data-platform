from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.gold import (
    add_gold_metadata,
    build_fleet_kpis,
    build_time_window_kpis,
    build_vehicle_kpis,
    build_vehicle_latest,
    gold_exists,
    read_gold,
    write_gold,
)
from app.spark.schema import TELEMETRY_SCHEMA
from app.spark.session import create_spark_session
from app.spark.transformations import (
    transform_telemetry,
    valid_telemetry,
)


@pytest.fixture(scope="module")
def spark():
    session = create_spark_session(
        "EV-Fleet-Area14-Test"
    )

    yield session

    session.stop()


@pytest.fixture
def gold_path(tmp_path):
    return tmp_path / "gold" / "dataset"


def records():
    now = datetime.now(timezone.utc).replace(
        tzinfo=None
    )

    return [
        (
            "g1",
            "EV_TELEMETRY",
            "1.0",
            "test",
            "ev001",
            85.0,
            30.0,
            40.0,
            "Bangalore",
            "NOT_CHARGING",
            now - timedelta(minutes=4),
            now,
            "MOVING",
            False,
        ),
        (
            "g2",
            "EV_TELEMETRY",
            "1.0",
            "test",
            "ev001",
            15.0,
            35.0,
            40.0,
            "Bangalore",
            "NOT_CHARGING",
            now - timedelta(minutes=2),
            now,
            "MOVING",
            False,
        ),
        (
            "g3",
            "EV_TELEMETRY",
            "1.0",
            "test",
            "ev002",
            60.0,
            70.0,
            0.0,
            "Hyderabad",
            "CHARGING",
            now - timedelta(minutes=3),
            now,
            "STOPPED",
            True,
        ),
        (
            "g4",
            "EV_TELEMETRY",
            "1.0",
            "test",
            "ev003",
            5.0,
            30.0,
            120.0,
            "Delhi",
            "NOT_CHARGING",
            now - timedelta(minutes=1),
            now,
            "MOVING",
            False,
        ),
    ]


def dataframe(spark):
    raw = spark.createDataFrame(
        records(),
        TELEMETRY_SCHEMA,
    )

    transformed = transform_telemetry(raw)

    return valid_telemetry(transformed)


def test_gold_metadata_added(spark):
    result = add_gold_metadata(
        dataframe(spark),
        "test_dataset",
    )

    assert "_gold_dataset" in result.columns
    assert "_gold_processed_at" in result.columns
    assert "_gold_processing_date" in result.columns
    assert "_gold_record_hash" in result.columns


def test_gold_metadata_dataset_name(spark):
    result = add_gold_metadata(
        dataframe(spark),
        "vehicle_kpis",
    )

    assert (
        result
        .select("_gold_dataset")
        .first()[0]
        == "vehicle_kpis"
    )


def test_gold_metadata_hash_is_deterministic(spark):
    result = add_gold_metadata(
        dataframe(spark),
        "test_dataset",
    )

    assert (
        result
        .select("_gold_record_hash")
        .distinct()
        .count()
        == 4
    )


def test_vehicle_latest_one_per_vehicle(spark):
    result = build_vehicle_latest(
        dataframe(spark)
    )

    assert result.count() == 3
    assert (
        result
        .select("vehicle_id")
        .distinct()
        .count()
        == 3
    )


def test_vehicle_latest_selects_newest_event(spark):
    result = build_vehicle_latest(
        dataframe(spark)
    )

    row = (
        result
        .filter("vehicle_id = 'EV001'")
        .first()
    )

    assert row is not None
    assert row.event_id == "g2"
    assert row.battery == 15.0


def test_vehicle_latest_contains_gold_metadata(spark):
    result = build_vehicle_latest(
        dataframe(spark)
    )

    assert "_gold_dataset" in result.columns

    assert (
        result
        .filter("vehicle_id = 'EV001'")
        .first()
        ._gold_dataset
        == "vehicle_latest"
    )


def test_vehicle_kpis_vehicle_count(spark):
    result = build_vehicle_kpis(
        dataframe(spark)
    )

    assert result.count() == 3


def test_vehicle_kpis_metrics(spark):
    result = build_vehicle_kpis(
        dataframe(spark)
    )

    row = (
        result
        .filter("vehicle_id = 'EV001'")
        .first()
    )

    assert row.event_count == 2
    assert row.minimum_battery == 15.0
    assert row.maximum_battery == 85.0
    assert row.low_battery_events == 1
    assert row.overspeed_events == 0
    assert row.charging_events == 0


def test_vehicle_kpis_charging_events(spark):
    result = build_vehicle_kpis(
        dataframe(spark)
    )

    row = (
        result
        .filter("vehicle_id = 'EV002'")
        .first()
    )

    assert row.charging_events == 1


def test_vehicle_kpis_overspeed_events(spark):
    result = build_vehicle_kpis(
        dataframe(spark)
    )

    row = (
        result
        .filter("vehicle_id = 'EV003'")
        .first()
    )

    assert row.overspeed_events == 1
    assert row.low_battery_events == 1


def test_fleet_kpis_single_record(spark):
    result = build_fleet_kpis(
        dataframe(spark)
    )

    assert result.count() == 1


def test_fleet_kpis_metrics(spark):
    result = build_fleet_kpis(
        dataframe(spark)
    )

    row = result.first()

    assert row.total_events == 4
    assert row.total_vehicles == 3
    assert row.charging_events == 1
    assert row.low_battery_events == 1
    assert row.overspeed_events == 1


def test_fleet_kpis_contains_metadata(spark):
    result = build_fleet_kpis(
        dataframe(spark)
    )

    row = result.first()

    assert row._gold_dataset == "fleet_kpis"
    assert row._gold_record_hash is not None


def test_time_window_kpis(spark):
    result = build_time_window_kpis(
        dataframe(spark),
        "5 minutes",
    )

    assert result.count() >= 1

    assert "window_start" in result.columns
    assert "window_end" in result.columns
    assert "vehicle_id" in result.columns
    assert "event_count" in result.columns
    assert "average_battery" in result.columns


def test_time_window_kpis_metadata(spark):
    result = build_time_window_kpis(
        dataframe(spark),
        "5 minutes",
    )

    assert "_gold_dataset" in result.columns

    assert (
        result
        .select("_gold_dataset")
        .distinct()
        .first()[0]
        == "time_window_kpis"
    )


def test_gold_write_read_round_trip(
    spark,
    gold_path,
):
    source = build_vehicle_kpis(
        dataframe(spark)
    )

    result = write_gold(
        source,
        gold_path,
        "vehicle_kpis",
    )

    assert result["format"] == "parquet"
    assert result["dataset"] == "vehicle_kpis"
    assert result["records"] == 3
    assert Path(gold_path).exists()

    loaded = read_gold(
        spark,
        gold_path,
    )

    assert loaded.count() == 3
    assert "vehicle_id" in loaded.columns
    assert "_gold_record_hash" in loaded.columns


def test_gold_exists(
    spark,
    gold_path,
):
    assert gold_exists(gold_path) is False

    source = build_vehicle_kpis(
        dataframe(spark)
    )

    write_gold(
        source,
        gold_path,
        "vehicle_kpis",
    )

    assert gold_exists(gold_path) is True


def test_missing_gold_path(
    spark,
    gold_path,
):
    with pytest.raises(FileNotFoundError):
        read_gold(
            spark,
            gold_path,
        )


def test_invalid_dataframe_rejected(
    gold_path,
):
    with pytest.raises(TypeError):
        write_gold(
            "not-a-dataframe",
            gold_path,
            "vehicle_kpis",
        )


def test_missing_required_column_rejected(spark):
    df = spark.createDataFrame(
        [
            ("g1", "EV001"),
        ],
        [
            "event_id",
            "vehicle_id",
        ],
    )

    with pytest.raises(ValueError):
        build_vehicle_latest(df)


def test_empty_dataset_name_rejected(spark):
    with pytest.raises(ValueError):
        add_gold_metadata(
            dataframe(spark),
            "",
        )


def test_invalid_window_duration_rejected(spark):
    with pytest.raises(ValueError):
        build_time_window_kpis(
            dataframe(spark),
            "",
        )


def test_gold_does_not_modify_input(spark):
    df = dataframe(spark)
    original_columns = df.columns

    build_vehicle_kpis(df)

    assert df.columns == original_columns
