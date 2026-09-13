from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


GOLD_FORMAT = "parquet"

DEFAULT_GOLD_PATH = "data_lake/gold"

DEFAULT_VEHICLE_LATEST_PATH = "data_lake/gold/vehicle_latest"
DEFAULT_VEHICLE_KPI_PATH = "data_lake/gold/vehicle_kpis"
DEFAULT_FLEET_KPI_PATH = "data_lake/gold/fleet_kpis"
DEFAULT_TIME_WINDOW_KPI_PATH = "data_lake/gold/time_window_kpis"


def _safe_path(path: str | Path) -> Path:
    value = Path(path)

    if value.is_absolute():
        return value

    return Path.cwd() / value


def _require_dataframe(df: DataFrame) -> None:
    if not isinstance(df, DataFrame):
        raise TypeError("df must be a PySpark DataFrame")


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
            "Gold input is missing required columns: "
            + ", ".join(missing)
        )


def add_gold_metadata(
    df: DataFrame,
    dataset_name: str,
) -> DataFrame:
    """
    Add Gold processing metadata while preserving
    existing analytical columns.
    """

    _require_dataframe(df)

    if not dataset_name or not dataset_name.strip():
        raise ValueError(
            "dataset_name must not be empty"
        )

    result = df

    if "_gold_dataset" not in result.columns:
        result = result.withColumn(
            "_gold_dataset",
            F.lit(dataset_name),
        )

    if "_gold_processed_at" not in result.columns:
        result = result.withColumn(
            "_gold_processed_at",
            F.current_timestamp(),
        )

    if "_gold_processing_date" not in result.columns:
        result = result.withColumn(
            "_gold_processing_date",
            F.to_date(
                F.col("_gold_processed_at")
            ),
        )

    if "_gold_record_hash" not in result.columns:
        hash_columns = [
            F.coalesce(
                F.col(column).cast("string"),
                F.lit(""),
            )
            for column in result.columns
            if not column.startswith("_gold_")
        ]

        result = result.withColumn(
            "_gold_record_hash",
            F.sha2(
                F.concat_ws(
                    "||",
                    *hash_columns,
                ),
                256,
            ),
        )

    return result


def build_vehicle_latest(
    df: DataFrame,
) -> DataFrame:
    """
    Build one latest telemetry record per vehicle.

    Deterministic ordering:
        timestamp
        -> Bronze ingestion timestamp
        -> event_id
    """

    _require_dataframe(df)

    _require_columns(
        df,
        [
            "event_id",
            "vehicle_id",
            "timestamp",
        ],
    )

    order_columns = [
        F.col("timestamp").desc_nulls_last(),
    ]

    if "_bronze_ingested_at" in df.columns:
        order_columns.append(
            F.col(
                "_bronze_ingested_at"
            ).desc_nulls_last()
        )

    order_columns.append(
        F.col("event_id").desc()
    )

    window = (
        Window
        .partitionBy("vehicle_id")
        .orderBy(*order_columns)
    )

    result = (
        df
        .withColumn(
            "_gold_row_number",
            F.row_number().over(window),
        )
        .filter(
            F.col("_gold_row_number") == 1
        )
        .drop("_gold_row_number")
    )

    return add_gold_metadata(
        result,
        "vehicle_latest",
    )


def build_vehicle_kpis(
    df: DataFrame,
) -> DataFrame:
    """
    Build analytical KPIs for every vehicle.
    """

    _require_dataframe(df)

    _require_columns(
        df,
        [
            "vehicle_id", "battery", "temp", "speed", "is_charging", "timestamp",
        ],
    )

    result = (
        df
        .groupBy("vehicle_id")
        .agg(
            F.count("*").alias("event_count"),

            F.min("timestamp").alias(
                "first_event_timestamp"
            ),

            F.max("timestamp").alias(
                "last_event_timestamp"
            ),

            F.avg("battery").alias(
                "average_battery"
            ),

            F.min("battery").alias(
                "minimum_battery"
            ),

            F.max("battery").alias(
                "maximum_battery"
            ),

            F.avg("temp").alias(
                "average_temperature"
            ),

            F.max("temp").alias(
                "maximum_temperature"
            ),

            F.avg("speed").alias(
                "average_speed"
            ),

            F.max("speed").alias(
                "maximum_speed"
            ),

            F.sum(
                F.when(F.col("battery") < 20, 1).otherwise(0)).alias("low_battery_events"),

            F.sum(
                F.when(
                    F.col("speed") > 100,
                    1,
                ).otherwise(0)
            ).alias(
                "overspeed_events"
            ),

            F.sum(
                F.when(
                    F.col("is_charging") == True,
                    1,
                ).otherwise(0)
            ).alias(
                "charging_events"
            ),
        )
    )

    return add_gold_metadata(
        result,
        "vehicle_kpis",
    )


def build_fleet_kpis(
    df: DataFrame,
) -> DataFrame:
    """
    Build one fleet-wide KPI record.

    Fleet-level low-battery KPI follows the operational LOW band:
    battery >= 10 and battery < 20.
    CRITICAL battery (<10) remains a separate severity state and
    is intentionally not counted as LOW.
    """

    _require_dataframe(df)

    _require_columns(
        df,
        [
            "vehicle_id",
            "battery",
            "temp",
            "speed",
            "is_charging",
        ],
    )

    result = (
        df
        .agg(
            F.count("*").alias(
                "total_events"
            ),

            F.countDistinct(
                "vehicle_id"
            ).alias(
                "total_vehicles"
            ),

            F.avg("battery").alias(
                "average_battery"
            ),

            F.min("battery").alias(
                "minimum_battery"
            ),

            F.max("battery").alias(
                "maximum_battery"
            ),

            F.avg("temp").alias(
                "average_temperature"
            ),

            F.max("temp").alias(
                "maximum_temperature"
            ),

            F.avg("speed").alias(
                "average_speed"
            ),

            F.sum(
                F.when(
                    F.col("is_charging") == True,
                    1,
                ).otherwise(0)
            ).alias(
                "charging_events"
            ),

            F.sum(
                F.when(
                    (F.col("battery") >= 10)
                    & (F.col("battery") < 20),
                    1,
                ).otherwise(0)
            ).alias(
                "low_battery_events"
            ),

            F.sum(
                F.when(
                    F.col("speed") > 100,
                    1,
                ).otherwise(0)
            ).alias(
                "overspeed_events"
            ),
        )
    )

    return add_gold_metadata(
        result,
        "fleet_kpis",
    )

def build_time_window_kpis(
    df: DataFrame,
    window_duration: str = "5 minutes",
) -> DataFrame:
    """
    Build five-minute telemetry KPIs per vehicle.
    """

    _require_dataframe(df)

    if not window_duration.strip():
        raise ValueError(
            "window_duration must not be empty"
        )

    _require_columns(
        df,
        [
            "vehicle_id",
            "timestamp",
            "battery",
            "speed",
            "temp",
        ],
    )

    result = (
        df
        .groupBy(
            F.window(
                F.col("timestamp"),
                window_duration,
            ),
            F.col("vehicle_id"),
        )
        .agg(
            F.count("*").alias(
                "event_count"
            ),

            F.avg("battery").alias(
                "average_battery"
            ),

            F.avg("speed").alias(
                "average_speed"
            ),

            F.max("temp").alias(
                "maximum_temperature"
            ),
        )
        .select(
            F.col("window.start").alias(
                "window_start"
            ),

            F.col("window.end").alias(
                "window_end"
            ),

            "vehicle_id",
            "event_count",
            "average_battery",
            "average_speed",
            "maximum_temperature",
        )
    )

    return add_gold_metadata(
        result,
        "time_window_kpis",
    )


def write_gold(
    df: DataFrame,
    path: str | Path,
    dataset_name: str,
    mode: str = "append",
    partition_by: str = "_gold_processing_date",
) -> dict:
    """
    Persist a Gold analytical dataset as Parquet.
    """

    _require_dataframe(df)

    if not df.columns:
        raise ValueError(
            "Gold input DataFrame must contain columns"
        )

    if mode not in {
        "append",
        "overwrite",
        "error",
        "ignore",
    }:
        raise ValueError(
            "mode must be one of: "
            "append, overwrite, error, ignore"
        )

    prepared = add_gold_metadata(
        df,
        dataset_name,
    )

    target = _safe_path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        prepared.write
        .format(GOLD_FORMAT)
        .mode(mode)
        .partitionBy(partition_by)
        .save(str(target))
    )

    return {
        "path": str(target),
        "format": GOLD_FORMAT,
        "mode": mode,
        "dataset": dataset_name,
        "partition_by": partition_by,
        "records": prepared.count(),
        "columns": len(prepared.columns),
    }


def read_gold(
    spark: SparkSession,
    path: str | Path,
) -> DataFrame:
    """
    Read a Gold Parquet dataset.
    """

    if not isinstance(
        spark,
        SparkSession,
    ):
        raise TypeError(
            "spark must be a SparkSession"
        )

    target = _safe_path(path)

    if not target.exists():
        raise FileNotFoundError(
            f"Gold path does not exist: {target}"
        )

    return (
        spark.read
        .format(GOLD_FORMAT)
        .load(str(target))
    )


def gold_exists(
    path: str | Path,
) -> bool:
    return _safe_path(path).exists()





