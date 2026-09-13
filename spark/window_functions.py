from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import (
    row_number,
    rank,
    dense_rank,
    avg,
    desc,
    col
)

# Create Spark Session
spark = (
    SparkSession.builder
    .appName("Spark Window Functions")
    .getOrCreate()
)

# PostgreSQL Connection
jdbc_url = "jdbc:postgresql://localhost:5432/ev_fleet_db"

properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

# Read processed telemetry table
df = spark.read.jdbc(
    url=jdbc_url,
    table="processed_telemetry",
    properties=properties
)

print("\n========== ROW NUMBER ==========")

window_spec = Window.partitionBy("vehicle_id").orderBy(desc("timestamp"))

latest_df = (
    df.withColumn(
        "row_num",
        row_number().over(window_spec)
    )
)

latest_df.select(
    "vehicle_id",
    "battery",
    "speed",
    "timestamp",
    "row_num"
).show(20)

print("\n========== RANK BY SPEED ==========")

speed_window = Window.orderBy(desc("speed"))

df.withColumn(
    "rank",
    rank().over(speed_window)
).select(
    "vehicle_id",
    "speed",
    "rank"
).show(20)

print("\n========== DENSE RANK BY BATTERY ==========")

battery_window = Window.orderBy(desc("battery"))

df.withColumn(
    "dense_rank",
    dense_rank().over(battery_window)
).select(
    "vehicle_id",
    "battery",
    "dense_rank"
).show(20)

print("\n========== RUNNING AVERAGE BATTERY ==========")

running_window = (
    Window.partitionBy("vehicle_id")
    .orderBy("timestamp")
    .rowsBetween(Window.unboundedPreceding, Window.currentRow)
)

df.withColumn(
    "running_avg_battery",
    avg("battery").over(running_window)
).select(
    "vehicle_id",
    "battery",
    "running_avg_battery",
    "timestamp"
).show(20)

spark.stop()