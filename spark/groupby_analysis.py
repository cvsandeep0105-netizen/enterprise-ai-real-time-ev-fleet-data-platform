from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, min, max, count

spark = (
    SparkSession.builder
    .appName("Spark GroupBy Analysis")
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

print("\n========== BATTERY STATUS COUNT ==========")
df.groupBy("battery_status").count().orderBy("count", ascending=False).show()

print("\n========== AVERAGE BATTERY ==========")
df.groupBy("battery_status").agg(avg("battery").alias("avg_battery")).show()

print("\n========== AVERAGE SPEED ==========")
df.groupBy("battery_status").agg(avg("speed").alias("avg_speed")).show()

print("\n========== MAX SPEED ==========")
df.groupBy("battery_status").agg(max("speed").alias("max_speed")).show()

print("\n========== MIN BATTERY ==========")
df.groupBy("battery_status").agg(min("battery").alias("min_battery")).show()

print("\n========== VEHICLES BY STATUS ==========")
df.groupBy("status").agg(count("*").alias("total")).show()

spark.stop()