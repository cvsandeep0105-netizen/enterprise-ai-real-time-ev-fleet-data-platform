from pyspark.sql import SparkSession
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

spark = (
    SparkSession.builder
    .appName("Spark UDF Analysis")
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
    table="processed_telemetry",
    properties=properties
)

# Python Function
def health(battery):
    if battery >= 80:
        return "Excellent"
    elif battery >= 50:
        return "Good"
    elif battery >= 20:
        return "Average"
    else:
        return "Charge Now"

# Convert to Spark UDF
health_udf = udf(health, StringType())

result = df.withColumn(
    "health_status",
    health_udf(df.battery)
)

print("\n========== BATTERY HEALTH ==========")

result.select(
    "vehicle_id",
    "battery",
    "health_status"
).show(30)

spark.stop()