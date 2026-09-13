from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def add_streaming_watermark(
    df: DataFrame,
    delay: str = "10 minutes",
) -> DataFrame:
    return df.withWatermark(
        "timestamp",
        delay,
    )


def deduplicate_stream(
    df: DataFrame,
    watermark: str = "10 minutes",
) -> DataFrame:
    return (
        df
        .withWatermark("timestamp", watermark)
        .dropDuplicates(["event_id"])
    )


def prepare_stream(
    df: DataFrame,
) -> DataFrame:
    return deduplicate_stream(
        add_streaming_watermark(df)
    )
