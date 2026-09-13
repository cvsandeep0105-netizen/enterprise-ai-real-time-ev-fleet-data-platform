from pathlib import Path

from pyspark.sql import DataFrame

from app.spark.session import create_spark_session
from app.spark.schema import TELEMETRY_SCHEMA
from app.spark.transformations import (
    transform_telemetry,
    valid_telemetry,
    invalid_telemetry,
)


def build_telemetry_dataframe(
    spark,
    records: list[tuple],
) -> DataFrame:
    return spark.createDataFrame(
        records,
        schema=TELEMETRY_SCHEMA,
    )


def process_batch(
    spark,
    records: list[tuple],
):
    raw = build_telemetry_dataframe(
        spark,
        records,
    )

    transformed = transform_telemetry(raw)

    return {
        "raw": raw,
        "transformed": transformed,
        "valid": valid_telemetry(transformed),
        "invalid": invalid_telemetry(transformed),
    }
