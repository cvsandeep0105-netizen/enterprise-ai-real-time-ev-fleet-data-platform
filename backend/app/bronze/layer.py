from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


BRONZE_FORMAT = "parquet"
DEFAULT_BRONZE_PATH = "data_lake/bronze/telemetry"


def _safe_path(path: str | Path) -> Path:
    value = Path(path)
    if value.is_absolute():
        return value
    return Path.cwd() / value


def bronze_schema(df: DataFrame):
    return df.schema


def add_bronze_metadata(df: DataFrame) -> DataFrame:
    """
    Add immutable ingestion metadata without changing source telemetry values.
    Existing columns are preserved.
    """
    result = df

    if "_bronze_ingested_at" not in result.columns:
        result = result.withColumn(
            "_bronze_ingested_at",
            F.current_timestamp(),
        )

    if "_bronze_ingestion_date" not in result.columns:
        result = result.withColumn(
            "_bronze_ingestion_date",
            F.to_date(F.col("_bronze_ingested_at")),
        )

    if "_bronze_record_hash" not in result.columns:
        hash_columns = [
            F.coalesce(F.col(c).cast("string"), F.lit(""))
            for c in df.columns
        ]
        result = result.withColumn(
            "_bronze_record_hash",
            F.sha2(
                F.concat_ws("||", *hash_columns),
                256,
            ),
        )

    return result


def write_bronze(
    df: DataFrame,
    path: str | Path = DEFAULT_BRONZE_PATH,
    mode: str = "append",
    partition_by: str = "_bronze_ingestion_date",
) -> dict:
    """
    Persist telemetry into the immutable Bronze layer.

    Parquet is used for analytics-friendly raw storage.
    Records are partitioned by ingestion date.
    """
    if not isinstance(df, DataFrame):
        raise TypeError("df must be a PySpark DataFrame")

    if not df.columns:
        raise ValueError("Bronze input DataFrame must contain columns")

    if mode not in {"append", "overwrite", "error", "ignore"}:
        raise ValueError(
            "mode must be one of: append, overwrite, error, ignore"
        )

    enriched = add_bronze_metadata(df)

    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    (
        enriched.write
        .format(BRONZE_FORMAT)
        .mode(mode)
        .partitionBy(partition_by)
        .save(str(target))
    )

    return {
        "path": str(target),
        "format": BRONZE_FORMAT,
        "mode": mode,
        "partition_by": partition_by,
        "records": enriched.count(),
        "columns": len(enriched.columns),
    }


def read_bronze(
    spark: SparkSession,
    path: str | Path = DEFAULT_BRONZE_PATH,
) -> DataFrame:
    """Read Bronze Parquet data with Spark."""
    if not isinstance(spark, SparkSession):
        raise TypeError("spark must be a SparkSession")

    target = _safe_path(path)

    if not target.exists():
        raise FileNotFoundError(
            f"Bronze path does not exist: {target}"
        )

    return spark.read.format(BRONZE_FORMAT).load(str(target))


def bronze_exists(path: str | Path = DEFAULT_BRONZE_PATH) -> bool:
    return _safe_path(path).exists()


def bronze_count(
    spark: SparkSession,
    path: str | Path = DEFAULT_BRONZE_PATH,
) -> int:
    return read_bronze(spark, path).count()


def bronze_distinct_events(
    spark: SparkSession,
    path: str | Path = DEFAULT_BRONZE_PATH,
) -> int:
    df = read_bronze(spark, path)

    if "event_id" not in df.columns:
        raise ValueError(
            "Bronze telemetry requires event_id for deduplication"
        )

    return df.select("event_id").distinct().count()
