from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.analytics import AnalyticsService
from app.gold import (
    build_fleet_kpis,
    build_time_window_kpis,
    build_vehicle_kpis,
    build_vehicle_latest,
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
        "EV-Fleet-Area15-Test"
    )
    yield session
    session.stop()


@pytest.fixture(scope="module")
def datasets(tmp_path_factory):
    root = tmp_path_factory.mktemp("area15_gold")

    return {
        "latest": root / "vehicle_latest",
        "vehicle": root / "vehicle_kpis",
        "fleet": root / "fleet_kpis",
        "window": root / "time_window_kpis",
    }


def records():
    now = datetime.now(timezone.utc).replace(
        tzinfo=None
    )

    return [
        (
            "a1", "EV_TELEMETRY", "1.0", "test",
            "ev001", 85.0, 30.0, 40.0,
            "Bangalore", "NOT_CHARGING",
            now, now, "MOVING", False,
        ),
        (
            "a2", "EV_TELEMETRY", "1.0", "test",
            "ev002", 15.0, 35.0, 0.0,
            "Hyderabad", "NOT_CHARGING",
            now, now, "STOPPED", False,
        ),
        (
            "a3", "EV_TELEMETRY", "1.0", "test",
            "ev003", 90.0, 70.0, 0.0,
            "Delhi", "CHARGING",
            now, now, "STOPPED", True,
        ),
    ]


@pytest.fixture(scope="module")
def service(spark, datasets):
    df = spark.createDataFrame(
        records(),
        TELEMETRY_SCHEMA,
    )

    transformed = transform_telemetry(df)
    valid = valid_telemetry(transformed)

    write_gold(
        build_vehicle_latest(valid),
        datasets["latest"],
        "vehicle_latest",
        mode="overwrite",
    )

    write_gold(
        build_vehicle_kpis(valid),
        datasets["vehicle"],
        "vehicle_kpis",
        mode="overwrite",
    )

    write_gold(
        build_fleet_kpis(valid),
        datasets["fleet"],
        "fleet_kpis",
        mode="overwrite",
    )

    write_gold(
        build_time_window_kpis(valid),
        datasets["window"],
        "time_window_kpis",
        mode="overwrite",
    )

    return AnalyticsService(
        spark,
        vehicle_latest_path=datasets["latest"],
        vehicle_kpi_path=datasets["vehicle"],
        fleet_kpi_path=datasets["fleet"],
        time_window_kpi_path=datasets["window"],
    )


def test_service_requires_spark():
    with pytest.raises(TypeError):
        AnalyticsService("not-spark")


def test_fleet_overview(service):
    result = service.fleet_overview()

    assert result.count() == 1

    row = result.first()

    assert row.total_vehicles == 3
    assert row.total_events == 3


def test_vehicle_kpis(service):
    result = service.vehicle_kpis()

    assert result.count() == 3
    assert "vehicle_id" in result.columns
    assert "average_battery" in result.columns


def test_vehicle_kpis_filter_normalizes_id(service):
    result = service.vehicle_kpis("  EV001 ")

    assert result.count() == 1
    assert result.first().vehicle_id == "EV001"


def test_vehicle_kpis_empty_id_rejected(service):
    with pytest.raises(ValueError):
        service.vehicle_kpis("   ")


def test_latest_vehicle_state(service):
    result = service.latest_vehicle_state()

    assert result.count() == 3
    assert "timestamp" in result.columns


def test_latest_vehicle_filter(service):
    result = service.latest_vehicle_state("ev002")

    assert result.count() == 1
    assert result.first().vehicle_id == "EV002"


def test_time_window_kpis(service):
    result = service.time_window_kpis()

    assert result.count() >= 1
    assert "window_start" in result.columns
    assert "window_end" in result.columns


def test_time_window_filter(service):
    result = service.time_window_kpis("EV003")

    assert result.count() >= 1

    assert all(
        row.vehicle_id == "EV003"
        for row in result.collect()
    )


def test_vehicle_exists(service):
    assert service.vehicle_exists("EV001") is True
    assert service.vehicle_exists("EV999") is False


def test_vehicle_exists_empty_id_rejected(service):
    with pytest.raises(ValueError):
        service.vehicle_exists("")


def test_service_is_read_only(service):
    before = service.vehicle_kpis().count()

    service.fleet_overview().count()
    service.latest_vehicle_state().count()
    service.time_window_kpis().count()

    after = service.vehicle_kpis().count()

    assert before == after


def test_gold_paths_are_not_modified(service, datasets):
    for path in datasets.values():
        assert Path(path).exists()


def test_input_contract_validation(spark, tmp_path):
    bad = spark.createDataFrame(
        [(1,)],
        ["wrong_column"],
    )

    path = tmp_path / "bad_gold"

    write_gold(
        bad,
        path,
        "bad",
    )

    service = AnalyticsService(
        spark,
        fleet_kpi_path=path,
    )

    with pytest.raises(ValueError):
        service.fleet_overview()
