from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from app.gold import (
    DEFAULT_FLEET_KPI_PATH,
    DEFAULT_TIME_WINDOW_KPI_PATH,
    DEFAULT_VEHICLE_KPI_PATH,
    DEFAULT_VEHICLE_LATEST_PATH,
    read_gold,
)


class AnalyticsService:
    """
    Read-only serving interface over Gold analytical datasets.

    The service deliberately does not mutate Gold data. It provides
    application-facing query operations that can later be exposed
    through FastAPI.
    """

    def __init__(
        self,
        spark: SparkSession,
        *,
        vehicle_latest_path: str | Path = DEFAULT_VEHICLE_LATEST_PATH,
        vehicle_kpi_path: str | Path = DEFAULT_VEHICLE_KPI_PATH,
        fleet_kpi_path: str | Path = DEFAULT_FLEET_KPI_PATH,
        time_window_kpi_path: str | Path = DEFAULT_TIME_WINDOW_KPI_PATH,
    ):
        if not isinstance(spark, SparkSession):
            raise TypeError("spark must be a SparkSession")

        self.spark = spark
        self.vehicle_latest_path = Path(vehicle_latest_path)
        self.vehicle_kpi_path = Path(vehicle_kpi_path)
        self.fleet_kpi_path = Path(fleet_kpi_path)
        self.time_window_kpi_path = Path(time_window_kpi_path)

    def _read(self, path: str | Path) -> DataFrame:
        return read_gold(self.spark, path)

    @staticmethod
    def _require_columns(
        df: DataFrame,
        required: list[str],
    ) -> None:
        missing = [
            column
            for column in required
            if column not in df.columns
        ]

        if missing:
            raise ValueError(
                "Gold dataset is missing required columns: "
                + ", ".join(missing)
            )

    def fleet_overview(self) -> DataFrame:
        """Return the fleet-wide KPI record."""
        df = self._read(self.fleet_kpi_path)

        self._require_columns(
            df,
            [
                "total_events",
                "total_vehicles",
                "average_battery",
                "average_temperature",
                "average_speed",
                "charging_events",
                "low_battery_events",
                "overspeed_events",
            ],
        )

        return df

    def vehicle_kpis(
        self,
        vehicle_id: str | None = None,
    ) -> DataFrame:
        """Return vehicle KPIs, optionally filtered by vehicle."""
        df = self._read(self.vehicle_kpi_path)

        self._require_columns(
            df,
            [
                "vehicle_id",
                "event_count",
                "average_battery",
                "minimum_battery",
                "maximum_battery",
                "average_temperature",
                "average_speed",
            ],
        )

        if vehicle_id is not None:
            value = vehicle_id.strip().upper()

            if not value:
                raise ValueError(
                    "vehicle_id must not be empty"
                )

            df = df.filter(
                F.col("vehicle_id") == value
            )

        return df

    def latest_vehicle_state(
        self,
        vehicle_id: str | None = None,
    ) -> DataFrame:
        """Return latest telemetry state for each vehicle."""
        df = self._read(self.vehicle_latest_path)

        self._require_columns(
            df,
            [
                "vehicle_id",
                "event_id",
                "timestamp",
                "battery",
                "temp",
                "speed",
            ],
        )

        if vehicle_id is not None:
            value = vehicle_id.strip().upper()

            if not value:
                raise ValueError(
                    "vehicle_id must not be empty"
                )

            df = df.filter(
                F.col("vehicle_id") == value
            )

        return df

    def time_window_kpis(
        self,
        vehicle_id: str | None = None,
    ) -> DataFrame:
        """Return time-window analytical KPIs."""
        df = self._read(self.time_window_kpi_path)

        self._require_columns(
            df,
            [
                "window_start",
                "window_end",
                "vehicle_id",
                "event_count",
                "average_battery",
                "average_speed",
                "maximum_temperature",
            ],
        )

        if vehicle_id is not None:
            value = vehicle_id.strip().upper()

            if not value:
                raise ValueError(
                    "vehicle_id must not be empty"
                )

            df = df.filter(
                F.col("vehicle_id") == value
            )

        return df

    def vehicle_exists(
        self,
        vehicle_id: str,
    ) -> bool:
        """Return whether a vehicle exists in the Gold KPI dataset."""
        value = vehicle_id.strip().upper()

        if not value:
            raise ValueError(
                "vehicle_id must not be empty"
            )

        return (
            self.vehicle_kpis(value)
            .limit(1)
            .count()
            > 0
        )
