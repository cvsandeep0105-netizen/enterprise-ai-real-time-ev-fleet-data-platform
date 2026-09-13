from pyspark.sql import SparkSession
import os

# Create Spark Session
spark = (
    SparkSession.builder
    .appName("Spark Parquet Analysis")
    .getOrCreate()
)

# PostgreSQL Connection
jdbc_url = "jdbc:postgresql://localhost:5432/ev_fleet_db"

properties = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

# Read data from PostgreSQL
df = spark.read.jdbc(
    url=jdbc_url,
    table="processed_telemetry",
    properties=properties
)

print("\n========== ORIGINAL DATA ==========")
df.show(10)

# Create output folder
output_path = "output/parquet"

if os.path.exists(output_path):
    import shutil
    shutil.rmtree(output_path)

# Write Parquet
df.write.mode("overwrite").parquet(output_path)

print("\nParquet file written successfully!")

# Read Parquet
parquet_df = spark.read.parquet(output_path)

print("\n========== READ PARQUET ==========")
parquet_df.show(10)

print("\n========== TOTAL RECORDS ==========")
print(parquet_df.count())

print("\n========== SCHEMA ==========")
parquet_df.printSchema()

spark.stop()