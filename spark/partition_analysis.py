from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("Spark Partition Analysis")
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

print("\n========== CURRENT PARTITIONS ==========")

print(df.rdd.getNumPartitions())

print("\n========== REPARTITION TO 8 ==========")

df2 = df.repartition(8)

print(df2.rdd.getNumPartitions())

print("\n========== COALESCE TO 2 ==========")

df3 = df2.coalesce(2)

print(df3.rdd.getNumPartitions())

print("\n========== SAMPLE DATA ==========")

df3.show(20)

spark.stop()