from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, min, max, count

spark = (
    SparkSession.builder
    .appName("Speed Analysis")
    .getOrCreate()
)

jdbc_url = "jdbc:postgresql://localhost:5432/ev_fleet_db"

properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

df = spark.read.jdbc(
    url=jdbc_url,
    table="telemetry",
    properties=properties
)

print("\n========== SPEED ANALYSIS ==========\n")

df.select(
    avg("speed").alias("Average Speed"),
    min("speed").alias("Minimum Speed"),
    max("speed").alias("Maximum Speed")
).show()

print("Vehicles Above 100 km/h")

overspeed = df.filter(col("speed") > 100)

overspeed.show()

print("Total Overspeed Vehicles")

overspeed.select(
    count("*").alias("Count")
).show()

spark.stop()