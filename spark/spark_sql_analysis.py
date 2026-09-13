from pyspark.sql import SparkSession

# Create Spark Session
spark = (
    SparkSession.builder
    .appName("Spark SQL Analysis")
    
    .getOrCreate()
)

# PostgreSQL Connection
jdbc_url = "jdbc:postgresql://localhost:5432/ev_fleet_db"

properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

# Read processed table
df = spark.read.jdbc(
    url=jdbc_url,
    table="processed_telemetry",
    properties=properties
)

# Register Temp View
df.createOrReplaceTempView("fleet")

print("\n========== TOTAL VEHICLES ==========")
spark.sql("""
SELECT COUNT(*) AS Total_Records
FROM fleet
""").show()

print("\n========== BATTERY STATUS ==========")
spark.sql("""
SELECT battery_status,
COUNT(*) AS Vehicles
FROM fleet
GROUP BY battery_status
ORDER BY Vehicles DESC
""").show()

print("\n========== AVERAGE SPEED ==========")
spark.sql("""
SELECT battery_status,
ROUND(AVG(speed),2) AS Avg_Speed
FROM fleet
GROUP BY battery_status
ORDER BY Avg_Speed DESC
""").show()

print("\n========== AVERAGE TEMPERATURE ==========")
spark.sql("""
SELECT
ROUND(AVG(temperature),2) AS Avg_Temperature
FROM fleet
""").show()

print("\n========== TOP 10 FASTEST VEHICLES ==========")
spark.sql("""
SELECT
vehicle_id,
speed,
battery,
battery_status
FROM fleet
ORDER BY speed DESC
LIMIT 10
""").show()

print("\n========== TOP 10 HOTTEST VEHICLES ==========")
spark.sql("""
SELECT
vehicle_id,
temperature,
battery
FROM fleet
ORDER BY temperature DESC
LIMIT 10
""").show()

spark.stop()