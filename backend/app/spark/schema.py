from pyspark.sql.types import (
    BooleanType,
    DoubleType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)


TELEMETRY_SCHEMA = StructType([
    StructField("event_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("schema_version", StringType(), False),
    StructField("producer", StringType(), False),
    StructField("vehicle_id", StringType(), False),
    StructField("battery", DoubleType(), True),
    StructField("temp", DoubleType(), True),
    StructField("speed", DoubleType(), True),
    StructField("location", StringType(), True),
    StructField("charging_status", StringType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("ingestion_timestamp", TimestampType(), True),
    StructField("vehicle_status", StringType(), True),
    StructField("is_charging", BooleanType(), True),
])


DERIVED_SCHEMA_FIELDS = [
    "battery_status",
    "temperature_status",
    "speed_status",
    "quality_status",
]
