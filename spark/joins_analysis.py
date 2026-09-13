from pyspark.sql import SparkSession

# Create Spark Session
spark = (
    SparkSession.builder
    .appName("Spark Join Analysis")
    .getOrCreate()
)

# PostgreSQL Connection
jdbc_url = "jdbc:postgresql://localhost:5432/ev_fleet_db"

properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

# Read Tables
vehicles = spark.read.jdbc(
    url=jdbc_url,
    table="vehicles",
    properties=properties
)

telemetry = spark.read.jdbc(
    url=jdbc_url,
    table="processed_telemetry",
    properties=properties
)

# Create aliases
v = vehicles.alias("v")
t = telemetry.alias("t")

print("\n========== INNER JOIN ==========")

inner_df = v.join(
    t,
    v.vehicle_id == t.vehicle_id,
    "inner"
)

inner_df.select(
    t.vehicle_id.alias("vehicle_id"),
    t.battery,
    t.speed,
    t.battery_status
).show(20)

print("\n========== LEFT JOIN ==========")

left_df = v.join(
    t,
    v.vehicle_id == t.vehicle_id,
    "left"
)

left_df.select(
    t.vehicle_id.alias("vehicle_id"),
    t.battery,
    t.speed,
    t.battery_status
).show(20)

print("\n========== RIGHT JOIN ==========")

right_df = v.join(
    t,
    v.vehicle_id == t.vehicle_id,
    "right"
)

right_df.select(
    t.vehicle_id.alias("vehicle_id"),
    t.battery,
    t.speed,
    t.battery_status
).show(20)

print("\n========== FULL OUTER JOIN ==========")

full_df = v.join(
    t,
    v.vehicle_id == t.vehicle_id,
    "outer"
)

full_df.select(
    t.vehicle_id.alias("vehicle_id"),
    t.battery,
    t.speed,
    t.battery_status
).show(20)

spark.stop()