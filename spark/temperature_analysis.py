from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, min, max, count

spark = (
    SparkSession.builder
    .appName("Temperature Analysis")
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

print("\n========== TEMPERATURE ANALYSIS ==========\n")

df.select(
    avg("temperature").alias("Average Temperature"),
    min("temperature").alias("Minimum Temperature"),
    max("temperature").alias("Maximum Temperature")
).show()

print("Vehicles Above 45°C")

high_temp = df.filter(col("temperature") > 45)

high_temp.show()

print("Total Vehicles Above 45°C")

high_temp.select(
    count("*").alias("Count")
).show()

spark.stop()