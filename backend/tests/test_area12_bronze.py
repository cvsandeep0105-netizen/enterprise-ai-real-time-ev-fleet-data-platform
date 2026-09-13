import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.spark.schema import TELEMETRY_SCHEMA
from app.spark.session import create_spark_session
from app.bronze import (
    add_bronze_metadata,
    bronze_count,
    bronze_distinct_events,
    read_bronze,
    write_bronze,
)


@pytest.fixture(scope="module")
def spark():
    session = create_spark_session("EV-Fleet-Area12-Test")
    yield session
    session.stop()


@pytest.fixture
def bronze_path(tmp_path):
    return tmp_path / "bronze" / "telemetry"


def records():
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    return [
        (
            "b1", "EV_TELEMETRY", "1.0", "test",
            "EV001", 85.0, 30.0, 40.0,
            "Bangalore", "NOT_CHARGING",
            now, now, "MOVING", False,
        ),
        (
            "b2", "EV_TELEMETRY", "1.0", "test",
            "EV002", 55.0, 35.0, 60.0,
            "Hyderabad", "CHARGING",
            now, now, "STOPPED", True,
        ),
        (
            "b3", "EV_TELEMETRY", "1.0", "test",
            "EV003", 20.0, 40.0, 80.0,
            "Delhi", "NOT_CHARGING",
            now, now, "MOVING", False,
        ),
    ]


def dataframe(spark):
    return spark.createDataFrame(records(), TELEMETRY_SCHEMA)


def test_metadata_preserves_source_columns(spark):
    df = dataframe(spark)
    result = add_bronze_metadata(df)

    assert result.count() == 3
    assert "event_id" in result.columns
    assert "vehicle_id" in result.columns
    assert "_bronze_ingested_at" in result.columns
    assert "_bronze_ingestion_date" in result.columns
    assert "_bronze_record_hash" in result.columns


def test_metadata_hash_is_deterministic(spark):
    df = dataframe(spark)
    result = add_bronze_metadata(df)

    assert result.select("_bronze_record_hash").distinct().count() == 3


def test_bronze_write(spark, bronze_path):
    result = write_bronze(
        dataframe(spark),
        bronze_path,
    )

    assert result["format"] == "parquet"
    assert result["mode"] == "append"
    assert result["records"] == 3
    assert Path(bronze_path).exists()


def test_bronze_read_round_trip(spark, bronze_path):
    write_bronze(dataframe(spark), bronze_path)

    result = read_bronze(spark, bronze_path)

    assert result.count() == 3
    assert set(["event_id", "vehicle_id"]).issubset(result.columns)


def test_bronze_count(spark, bronze_path):
    write_bronze(dataframe(spark), bronze_path)

    assert bronze_count(spark, bronze_path) == 3


def test_distinct_events(spark, bronze_path):
    write_bronze(dataframe(spark), bronze_path)

    assert bronze_distinct_events(spark, bronze_path) == 3


def test_append_mode(spark, bronze_path):
    df = dataframe(spark)

    write_bronze(df, bronze_path)
    write_bronze(df, bronze_path)

    assert bronze_count(spark, bronze_path) == 6


def test_missing_bronze_path(spark, bronze_path):
    with pytest.raises(FileNotFoundError):
        read_bronze(spark, bronze_path)


def test_invalid_dataframe_rejected(bronze_path):
    with pytest.raises(TypeError):
        write_bronze("not-a-dataframe", bronze_path)
