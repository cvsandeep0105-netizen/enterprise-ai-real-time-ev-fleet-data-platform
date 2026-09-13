from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def normalize_telemetry(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn("vehicle_id", F.upper(F.trim("vehicle_id")))
        .withColumn("event_type", F.upper(F.trim("event_type")))
        .withColumn("schema_version", F.trim("schema_version"))
        .withColumn("producer", F.trim("producer"))
        .withColumn("location", F.trim("location"))
        .withColumn("charging_status", F.upper(F.trim("charging_status")))
        .withColumn("vehicle_status", F.upper(F.trim("vehicle_status")))
        .withColumn(
            "is_charging",
            F.when(
                F.col("charging_status") == "CHARGING",
                F.lit(True),
            ).otherwise(F.lit(False)),
        )
    )


def derive_operational_status(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn(
            "battery_status",
            F.when(F.col("battery").isNull(), "UNKNOWN")
             .when(F.col("battery") < 10, "CRITICAL")
             .when(F.col("battery") < 20, "LOW")
             .when(F.col("battery") <= 100, "NORMAL")
             .otherwise("INVALID"),
        )
        .withColumn(
            "temperature_status",
            F.when(F.col("temp").isNull(), "UNKNOWN")
             .when(F.col("temp") > 80, "CRITICAL")
             .when(F.col("temp") > 60, "HIGH")
             .when(F.col("temp") >= -20, "NORMAL")
             .otherwise("INVALID"),
        )
        .withColumn(
            "speed_status",
            F.when(F.col("speed").isNull(), "UNKNOWN")
             .when(F.col("speed") < 0, "INVALID")
             .when(F.col("speed") > 100, "OVERSPEED")
             .when(F.col("speed") == 0, "STOPPED")
             .otherwise("NORMAL"),
        )
    )


def classify_quality(df: DataFrame) -> DataFrame:
    """
    Classify telemetry data quality independently from operational severity.

    Operational conditions such as CRITICAL temperature or OVERSPEED are
    valid telemetry events and must remain in the valid stream. Quality
    routing is reserved for structurally invalid/impossible measurements.
    """
    condition = (
        F.col("event_id").isNotNull()
        & F.col("vehicle_id").isNotNull()
        & F.col("timestamp").isNotNull()
        & F.col("ingestion_timestamp").isNotNull()
        & F.col("battery").isNotNull()
        & F.col("battery").between(0, 100)
        & F.col("temp").isNotNull()
        & (F.col("temp") >= -20)
        & F.col("speed").isNotNull()
        & (F.col("speed") >= 0)
        & (F.col("ingestion_timestamp") >= F.col("timestamp"))
    )

    return df.withColumn(
        "quality_status",
        F.when(condition, F.lit("VALID"))
         .otherwise(F.lit("INVALID")),
    )

def transform_telemetry(df: DataFrame) -> DataFrame:
    df = normalize_telemetry(df)
    df = derive_operational_status(df)
    df = classify_quality(df)
    return df


def valid_telemetry(df: DataFrame) -> DataFrame:
    return df.filter(F.col("quality_status") == "VALID")


def invalid_telemetry(df: DataFrame) -> DataFrame:
    return df.filter(F.col("quality_status") == "INVALID")


def vehicle_latest(df: DataFrame) -> DataFrame:
    """
    Return the latest valid telemetry record for every vehicle.
    """
    from pyspark.sql.window import Window

    window = (
        Window
        .partitionBy("vehicle_id")
        .orderBy(
            F.col("timestamp").desc(),
            F.col("event_id").desc(),
        )
    )

    return (
        df
        .withColumn("_row_number", F.row_number().over(window))
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
    )


def vehicle_aggregates(df: DataFrame) -> DataFrame:
    """
    Calculate per-vehicle telemetry aggregates.
    """
    return (
        df
        .groupBy("vehicle_id")
        .agg(
            F.count("*").alias("event_count"),
            F.avg("battery").alias("average_battery"),
            F.min("battery").alias("minimum_battery"),
            F.max("battery").alias("maximum_battery"),
            F.avg("temp").alias("average_temperature"),
            F.max("temp").alias("maximum_temperature"),
            F.avg("speed").alias("average_speed"),
            F.max("speed").alias("maximum_speed"),
            F.sum(
                F.when(F.col("battery") < 20, 1).otherwise(0)
            ).alias("low_battery_events"),
            F.sum(
                F.when(F.col("speed") > 100, 1).otherwise(0)
            ).alias("overspeed_events"),
        )
    )

def time_window_aggregates(
    df: DataFrame,
    window_duration: str = "5 minutes",
) -> DataFrame:
    return (
        df
        .groupBy(
            F.window(
                F.col("timestamp"),
                window_duration,
            ),
            F.col("vehicle_id"),
        )
        .agg(
            F.count("*").alias("event_count"),
            F.avg("battery").alias("average_battery"),
            F.avg("speed").alias("average_speed"),
            F.max("temp").alias("maximum_temperature"),
        )
        .select(
            F.col("window.start").alias("window_start"),
            F.col("window.end").alias("window_end"),
            "vehicle_id",
            "event_count",
            "average_battery",
            "average_speed",
            "maximum_temperature",
        )
    )


def repartition_for_vehicle(
    df: DataFrame,
    partitions: int = 4,
) -> DataFrame:
    return df.repartition(
        partitions,
        "vehicle_id",
    )


def deterministic_order(df: DataFrame) -> DataFrame:
    return df.orderBy(
        F.col("vehicle_id"),
        F.col("timestamp"),
        F.col("event_id"),
    )







