import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.bronze import write_bronze, read_bronze, read_bronze
from app.silver import (
    add_silver_metadata,
    deduplicate_silver,
    prepare_silver,
    read_silver,
    silver_count,
    silver_exists,
    write_silver,
)
from app.spark.schema import TELEMETRY_SCHEMA
from app.spark.session import create_spark_session


@pytest.fixture(scope="module")
def spark():
    session = create_spark_session(
        "EV-Fleet-Area13-Test"
    )
    yield session
    session.stop()


@pytest.fixture
def silver_path(tmp_path):
    return tmp_path / "silver" / "telemetry"


def records():
    now = datetime.now(timezone.utc).replace(
        tzinfo=None
    )

    return [
        (
            "s1", "EV_TELEMETRY", "1.0", "test",
            "ev001", 85.0, 30.0, 40.0,
            "Bangalore", "NOT_CHARGING",
            now, now, "MOVING", False,
        ),
        (
            "s2", "EV_TELEMETRY", "1.0", "test",
            "ev002", 15.0, 35.0, 0.0,
            "Hyderabad", "NOT_CHARGING",
            now, now, "STOPPED", False,
        ),
        (
            "s3", "EV_TELEMETRY", "1.0", "test",
            "ev003", 90.0, 90.0, 0.0,
            "Delhi", "CHARGING",
            now, now, "STOPPED", True,
        ),
    ]


def dataframe(spark):
    return spark.createDataFrame(
        records(),
        TELEMETRY_SCHEMA,
    )


def test_silver_metadata_added(spark):
    result = add_silver_metadata(
        dataframe(spark)
    )

    assert "_silver_processed_at" in result.columns
    assert "_silver_processing_date" in result.columns
    assert "_silver_record_hash" in result.columns


def test_silver_metadata_deterministic(spark):
    result = add_silver_metadata(
        dataframe(spark)
    )

    assert (
        result
        .select("_silver_record_hash")
        .distinct()
        .count()
        == 3
    )


def test_prepare_silver_preserves_valid_records(spark):
    result = prepare_silver(
        dataframe(spark)
    )

    assert result.count() == 3


def test_prepare_silver_normalizes_vehicle_id(spark):
    result = prepare_silver(
        dataframe(spark)
    )

    row = (
        result
        .filter("vehicle_id = 'EV001'")
        .first()
    )

    assert row is not None
    assert row.vehicle_id == "EV001"


def test_prepare_silver_derives_statuses(spark):
    result = prepare_silver(
        dataframe(spark)
    )

    row = (
        result
        .filter("event_id = 's3'")
        .first()
    )

    assert row.battery_status == "NORMAL"
    assert row.temperature_status == "CRITICAL"
    assert row.speed_status == "STOPPED"
    assert row.quality_status == "VALID"


def test_prepare_silver_removes_invalid_records(spark):
    now = datetime.now(timezone.utc).replace(
        tzinfo=None
    )

    invalid = [
        (
            "bad1", "EV_TELEMETRY", "1.0", "test",
            "ev999", 150.0, 30.0, 40.0,
            "Bangalore", "NOT_CHARGING",
            now, now, "MOVING", False,
        )
    ]

    df = spark.createDataFrame(
        invalid,
        TELEMETRY_SCHEMA,
    )

    result = prepare_silver(df)

    assert result.count() == 0


def test_deduplicate_silver_by_event_id(spark):
    now = datetime.now(timezone.utc).replace(
        tzinfo=None
    )

    data = [
        (
            "dup1", "EV_TELEMETRY", "1.0", "test",
            "ev001", 50.0, 30.0, 40.0,
            "Bangalore", "NOT_CHARGING",
            now, now, "MOVING", False,
        ),
        (
            "dup1", "EV_TELEMETRY", "1.0", "test",
            "ev001", 60.0, 30.0, 40.0,
            "Bangalore", "NOT_CHARGING",
            now, now, "MOVING", False,
        ),
    ]

    df = spark.createDataFrame(
        data,
        TELEMETRY_SCHEMA,
    )

    result = deduplicate_silver(df)

    assert result.count() == 1
    assert result.select("event_id").distinct().count() == 1


def test_write_silver(spark, silver_path):
    result = write_silver(
        dataframe(spark),
        silver_path,
    )

    assert result["format"] == "parquet"
    assert result["mode"] == "append"
    assert result["records"] == 3
    assert Path(silver_path).exists()


def test_read_silver_round_trip(spark, silver_path):
    write_silver(
        dataframe(spark),
        silver_path,
    )

    result = read_silver(
        spark,
        silver_path,
    )

    assert result.count() == 3
    assert "quality_status" in result.columns
    assert "_silver_record_hash" in result.columns


def test_silver_count(spark, silver_path):
    write_silver(
        dataframe(spark),
        silver_path,
    )

    assert silver_count(
        spark,
        silver_path,
    ) == 3


def test_silver_exists(spark, silver_path):
    assert silver_exists(silver_path) is False

    write_silver(
        dataframe(spark),
        silver_path,
    )

    assert silver_exists(silver_path) is True


def test_missing_silver_path(spark, silver_path):
    with pytest.raises(FileNotFoundError):
        read_silver(
            spark,
            silver_path,
        )


def test_invalid_dataframe_rejected(silver_path):
    with pytest.raises(TypeError):
        write_silver(
            "not-a-dataframe",
            silver_path,
        )


def test_missing_required_column_rejected(spark):
    df = spark.createDataFrame(
        [(1, "EV001")],
        ["event_id", "vehicle_id"],
    )

    with pytest.raises(ValueError):
        prepare_silver(df)


def test_silver_does_not_modify_input(spark):
    df = dataframe(spark)
    original_columns = df.columns

    prepare_silver(df)

    assert df.columns == original_columns


def test_bronze_to_silver_contract(spark, silver_path):
    bronze_path = silver_path.parent / "bronze"

    bronze_result = write_bronze(
        dataframe(spark),
        bronze_path,
    )

    bronze_df = read_silver.__globals__["read_bronze"](
        spark,
        bronze_path,
    )

    silver_df = prepare_silver(
        bronze_df
    )

    assert bronze_result["records"] == 3
    assert silver_df.count() == 3
    assert "_bronze_record_hash" in silver_df.columns
    assert "_silver_record_hash" in silver_df.columns


def test_silver_append_preserves_records(spark, silver_path):
    df = dataframe(spark)

    write_silver(
        df,
        silver_path,
    )

    write_silver(
        df,
        silver_path,
    )

    assert silver_count(
        spark,
        silver_path,
    ) == 6
