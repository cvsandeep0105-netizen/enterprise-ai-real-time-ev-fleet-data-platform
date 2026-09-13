from pyspark.sql import SparkSession
from pyspark.sql.functions import when

spark = (
    SparkSession.builder
    .appName("Write Processed Data")
    .getOrCreate()
)

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

# Create battery status column
processed_df = df.withColumn(
    "battery_status",
    when(df.battery < 20, "Critical")
    .when(df.battery < 40, "Low")
    .when(df.battery < 70, "Medium")
    .otherwise("Healthy")
)

print("Processed Data")

processed_df.show(10)

# Write back to PostgreSQL
processed_df.write.jdbc(
    url=jdbc_url,
    table="processed_telemetry",
    mode="overwrite",
    properties=properties
)

print("processed_telemetry table created successfully.")

spark.stop()