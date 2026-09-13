from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, min, max, count

# Create Spark Session
spark = SparkSession.builder \
    .appName("Battery Analysis") \
    .getOrCreate()
    
    
# PostgreSQL Connection
jdbc_url = "jdbc:postgresql://localhost:5432/ev_fleet_db"

properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

# Read telemetry table
df = spark.read.jdbc(
    url=jdbc_url,
    table="telemetry",
    properties=properties
)

print("\n========== BATTERY ANALYSIS ==========\n")

print("Average, Minimum and Maximum Battery")
df.select(
    avg("battery").alias("Average Battery"),
    min("battery").alias("Minimum Battery"),
    max("battery").alias("Maximum Battery")
).show()

print("Vehicles Below 20% Battery")
low_battery = df.filter(col("battery") < 20)

low_battery.show()

print("Total Vehicles Below 20% Battery")

low_battery.select(
    count("*").alias("Count")
).show()

print("Vehicles Needing Charging")

df.filter(col("status") == "Low Battery").show()

spark.stop()