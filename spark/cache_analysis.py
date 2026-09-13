from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, max, min
from pyspark import StorageLevel
import time

# Create Spark Session
spark = (
    SparkSession.builder
    .appName("Spark Cache Analysis")
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

print("\n========== WITHOUT CACHE ==========")

start = time.time()

df.count()

df.groupBy("battery_status").count().show()

df.groupBy("battery_status").agg(
    avg("battery").alias("avg_battery")
).show()

print(f"Time Without Cache: {time.time()-start:.2f} seconds")

print("\n========== WITH CACHE ==========")

cached_df = df.cache()

start = time.time()

cached_df.count()

cached_df.groupBy("battery_status").count().show()

cached_df.groupBy("battery_status").agg(
    avg("battery").alias("avg_battery")
).show()

print(f"Time With Cache: {time.time()-start:.2f} seconds")

print("\n========== PERSIST ==========")

persist_df = df.persist(StorageLevel.MEMORY_AND_DISK)

persist_df.groupBy("battery_status").agg(
    max("speed").alias("max_speed"),
    min("battery").alias("min_battery")
).show()

cached_df.unpersist()
persist_df.unpersist()

spark.stop()