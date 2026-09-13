from pyspark.sql import SparkSession

def get_spark_session(app_name):
    return (
        SparkSession.builder
        .appName(app_name)
        .getOrCreate()
    )

def get_db_properties():
    jdbc_url = "jdbc:postgresql://localhost:5432/ev_fleet_db"

    properties = {
        "user": "postgres",
        "password": "postgres",
        "driver": "org.postgresql.Driver"
    }

    return jdbc_url, properties