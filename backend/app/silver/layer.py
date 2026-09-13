from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from app.bronze import read_bronze
from app.spark.transformations import (
    classify_quality,
    derive_operational_status,
    normalize_telemetry,
)


SILVER_FORMAT = "parquet"

DEFAULT_SILVER_PATH = "data_lake/silver/telemetry"


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
            "Silver input is missing required columns: "
            + ", ".join(missing)
        )


def add_silver_metadata(df: DataFrame) -> DataFrame:
    """
    Add Silver processing metadata.

    Existing Bronze and telemetry columns are preserved.
    """

    _require_dataframe(df)

    result = df

    if "_silver_processed_at" not in result.columns:
        result = result.withColumn(
            "_silver_processed_at",
            F.current_timestamp(),
        )

    if "_silver_processing_date" not in result.columns:
        result = result.withColumn(
            "_silver_processing_date",
            F.to_date(F.col("_silver_processed_at")),
        )

    if "_silver_record_hash" not in result.columns:
        hash_columns = [
            F.coalesce(
                F.col(column).cast("string"),
                F.lit(""),
            )
            for column in result.columns
            if not column.startswith("_silver_")
        ]

        result = result.withColumn(
            "_silver_record_hash",
            F.sha2(
                F.concat_ws("||", *hash_columns),
                256,
            ),
        )

    return result


def deduplicate_silver(df: DataFrame) -> DataFrame:
    """
    Deterministically retain one record per event_id.

    The newest event timestamp wins. If timestamps are equal,
    the newest Bronze ingestion timestamp wins. event_id provides
    the final deterministic tie-breaker.
    """

    _require_dataframe(df)

    _require_columns(
        df,
        [
            "event_id",
            "timestamp",
        ],
    )

    order_columns = [
        F.col("timestamp").desc_nulls_last(),
    ]

    if "_bronze_ingested_at" in df.columns:
        order_columns.append(
            F.col("_bronze_ingested_at").desc_nulls_last()
        )

    order_columns.append(
        F.col("event_id").desc()
    )

    window = (
        Window
        .partitionBy("event_id")
        .orderBy(*order_columns)
    )

    return (
        df
        .withColumn("_silver_row_number", F.row_number().over(window))
        .filter(F.col("_silver_row_number") == 1)
        .drop("_silver_row_number")
    )


def prepare_silver(df: DataFrame) -> DataFrame:
    """
    Transform Bronze telemetry into the canonical Silver dataset.

    Pipeline:
        normalization
        -> operational classification
        -> quality classification
        -> valid-record filtering
        -> deterministic event deduplication
        -> Silver metadata
    """

    _require_dataframe(df)

    _require_columns(
        df,
        [
            "event_id",
            "vehicle_id",
            "timestamp",
            "ingestion_timestamp",
            "battery",
            "temp",
            "speed",
        ],
    )

    result = normalize_telemetry(df)
    result = derive_operational_status(result)
    result = classify_quality(result)

    result = result.filter(
        F.col("quality_status") == "VALID"
    )

    result = deduplicate_silver(result)

    result = add_silver_metadata(result)

    return result


def write_silver(
    df: DataFrame,
    path: str | Path = DEFAULT_SILVER_PATH,
    mode: str = "append",
    partition_by: str = "_silver_processing_date",
) -> dict:
    """
    Persist clean Silver telemetry as Parquet.

    Silver contains only valid, deduplicated telemetry.
    """

    _require_dataframe(df)

    if not df.columns:
        raise ValueError(
            "Silver input DataFrame must contain columns"
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

    prepared = prepare_silver(df)

    target = _safe_path(path)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        prepared.write
        .format(SILVER_FORMAT)
        .mode(mode)
        .partitionBy(partition_by)
        .save(str(target))
    )

    return {
        "path": str(target),
        "format": SILVER_FORMAT,
        "mode": mode,
        "partition_by": partition_by,
        "records": prepared.count(),
        "columns": len(prepared.columns),
    }


def read_silver(
    spark: SparkSession,
    path: str | Path = DEFAULT_SILVER_PATH,
) -> DataFrame:
    """Read Silver Parquet data with Spark."""

    if not isinstance(spark, SparkSession):
        raise TypeError(
            "spark must be a SparkSession"
        )

    target = _safe_path(path)

    if not target.exists():
        raise FileNotFoundError(
            f"Silver path does not exist: {target}"
        )

    return (
        spark.read
        .format(SILVER_FORMAT)
        .load(str(target))
    )


def silver_exists(
    path: str | Path = DEFAULT_SILVER_PATH,
) -> bool:
    return _safe_path(path).exists()


def silver_count(
    spark: SparkSession,
    path: str | Path = DEFAULT_SILVER_PATH,
) -> int:
    return read_silver(
        spark,
        path,
    ).count()
