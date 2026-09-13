from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    when,
    current_timestamp,
    to_timestamp,
    avg,
    max,
    min,
    count,
    round as spark_round,
)

import logging
import os
import sys


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("EV-Spark-Pipeline")


# ============================================================
# CONFIGURATION
# ============================================================

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")
POSTGRES_DB = os.getenv("POSTGRES_DB", "airflow")
POSTGRES_USER = os.getenv("POSTGRES_USER", "airflow")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "airflow")

SOURCE_TABLE = "vehicle_data"

DATA_LAKE_ROOT = os.getenv(
    "EV_DATA_LAKE",
    "./data_lake",
)

BRONZE_PATH = os.path.join(
    DATA_LAKE_ROOT,
    "bronze",
    "vehicle_data",
)

SILVER_PATH = os.path.join(
    DATA_LAKE_ROOT,
    "silver",
    "vehicle_data",
)

GOLD_PATH = os.path.join(
    DATA_LAKE_ROOT,
    "gold",
    "fleet_metrics",
)


# ============================================================
# SPARK SESSION
# ============================================================

logger.info("Starting Spark session...")

spark = (
    SparkSession.builder
    .appName("EV Fleet Data Transformation")
    .config(
        "spark.hadoop.fs.file.impl",
        "org.apache.hadoop.fs.RawLocalFileSystem",
    )
    .config(
        "spark.hadoop.fs.permissions.umask-mode",
        "022",
    )
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

logger.info("Spark session started successfully.")


# ============================================================
# JDBC CONFIGURATION
# ============================================================

jdbc_url = (
    f"jdbc:postgresql://"
    f"{POSTGRES_HOST}:"
    f"{POSTGRES_PORT}/"
    f"{POSTGRES_DB}"
    f"?options=-c%20TimeZone%3DUTC"
)

jdbc_properties = {
    "user": POSTGRES_USER,
    "password": POSTGRES_PASSWORD,
    "driver": "org.postgresql.Driver",
}


# ============================================================
# MAIN PIPELINE
# ============================================================

try:

    # ========================================================
    # 1. EXTRACT
    # ========================================================

    logger.info(
        "Reading EV telemetry from PostgreSQL..."
    )

    raw_df = spark.read.jdbc(
        url=jdbc_url,
        table=SOURCE_TABLE,
        properties=jdbc_properties,
    )

    source_count = raw_df.count()

    logger.info(
        f"Records read from PostgreSQL: {source_count}"
    )

    if source_count == 0:
        logger.warning(
            "No vehicle telemetry found."
        )

        spark.stop()
        sys.exit(0)


    # ========================================================
    # 2. BRONZE
    # ========================================================

    logger.info(
        "Writing Bronze Data Lake layer..."
    )

    bronze_df = (
        raw_df
        .withColumn(
            "ingested_at",
            current_timestamp(),
        )
    )

    (
        bronze_df.write
        .mode("append")
        .partitionBy("vehicle_id")
        .parquet(BRONZE_PATH)
    )

    logger.info(
        f"Bronze layer written: {BRONZE_PATH}"
    )


    # ========================================================
    # 3. STANDARDIZATION
    # ========================================================

    logger.info(
        "Standardizing telemetry..."
    )

    standardized_df = (
        raw_df

        .withColumn(
            "vehicle_id",
            col("vehicle_id").cast("string"),
        )

        .withColumn(
            "battery",
            col("battery").cast("double"),
        )

        .withColumn(
            "temp",
            col("temp").cast("double"),
        )

        .withColumn(
            "speed",
            col("speed").cast("double"),
        )

        .withColumn(
            "timestamp",
            to_timestamp(col("timestamp")),
        )

        .withColumn(
            "location",
            col("location").cast("string"),
        )

        .withColumn(
            "charging_status",
            col("charging_status").cast("string"),
        )
    )


    # ========================================================
    # 4. DATA QUALITY
    # ========================================================

    logger.info(
        "Applying data-quality rules..."
    )

    valid_df = (
        standardized_df

        .filter(
            col("vehicle_id").isNotNull()
        )

        .filter(
            col("timestamp").isNotNull()
        )

        .filter(
            (col("battery") >= 0)
            & (col("battery") <= 100)
        )

        .filter(
            (col("temp") >= -40)
            & (col("temp") <= 150)
        )

        .filter(
            (col("speed") >= 0)
            & (col("speed") <= 250)
        )
    )

    valid_count = valid_df.count()

    rejected_count = source_count - valid_count

    logger.info(
        f"Valid records: {valid_count}"
    )

    logger.info(
        f"Rejected records: {rejected_count}"
    )


    # ========================================================
    # 5. SILVER
    # ========================================================

    logger.info(
        "Creating Silver layer..."
    )

    silver_df = (
        valid_df

        .withColumn(
            "battery_status",
            when(
                col("battery") < 10,
                "CRITICAL",
            )
            .when(
                col("battery") < 20,
                "LOW",
            )
            .when(
                col("battery") < 70,
                "NORMAL",
            )
            .otherwise(
                "GOOD",
            ),
        )

        .withColumn(
            "vehicle_status",
            when(
                col("speed") == 0,
                "STOPPED",
            )
            .otherwise(
                "MOVING",
            ),
        )

        .withColumn(
            "temperature_status",
            when(
                col("temp") > 80,
                "CRITICAL",
            )
            .when(
                col("temp") > 60,
                "HIGH",
            )
            .when(
                col("temp") < 10,
                "COLD",
            )
            .otherwise(
                "NORMAL",
            ),
        )

        .withColumn(
            "is_charging",
            when(
                col("charging_status") == "CHARGING",
                True,
            )
            .otherwise(False),
        )

        .withColumn(
            "processed_at",
            current_timestamp(),
        )
    )


    # ========================================================
    # 6. WRITE SILVER
    # ========================================================

    logger.info(
        "Writing Silver Data Lake layer..."
    )

    (
        silver_df.write
        .mode("overwrite")
        .partitionBy("vehicle_id")
        .parquet(SILVER_PATH)
    )

    logger.info(
        f"Silver layer written: {SILVER_PATH}"
    )


    # ========================================================
    # 7. GOLD
    # ========================================================

    logger.info(
        "Creating Gold fleet metrics..."
    )

    gold_df = (
        silver_df
        .groupBy("vehicle_id")
        .agg(

            count("*").alias(
                "telemetry_records"
            ),

            spark_round(
                avg("battery"),
                2,
            ).alias(
                "avg_battery"
            ),

            spark_round(
                min("battery"),
                2,
            ).alias(
                "min_battery"
            ),

            spark_round(
                max("battery"),
                2,
            ).alias(
                "max_battery"
            ),

            spark_round(
                avg("temp"),
                2,
            ).alias(
                "avg_temperature"
            ),

            spark_round(
                max("temp"),
                2,
            ).alias(
                "max_temperature"
            ),

            spark_round(
                avg("speed"),
                2,
            ).alias(
                "avg_speed"
            ),

            spark_round(
                max("speed"),
                2,
            ).alias(
                "max_speed"
            ),

            count(
                when(
                    col("battery_status") == "CRITICAL",
                    True,
                )
            ).alias(
                "critical_battery_events"
            ),

            count(
                when(
                    col("temperature_status") == "CRITICAL",
                    True,
                )
            ).alias(
                "critical_temperature_events"
            ),

            count(
                when(
                    col("speed") > 120,
                    True,
                )
            ).alias(
                "overspeed_events"
            ),

            count(
                when(
                    col("is_charging") == True,
                    True,
                )
            ).alias(
                "charging_events"
            ),
        )
    )


    # ========================================================
    # 8. WRITE GOLD
    # ========================================================

    logger.info(
        "Writing Gold analytics layer..."
    )

    (
        gold_df.write
        .mode("overwrite")
        .parquet(GOLD_PATH)
    )

    logger.info(
        f"Gold layer written: {GOLD_PATH}"
    )


    # ========================================================
    # 9. DISPLAY RESULTS
    # ========================================================

    print()
    print("=" * 70)
    print("EV FLEET SPARK PIPELINE")
    print("=" * 70)

    print(
        f"Source Records       : {source_count}"
    )

    print(
        f"Valid Records        : {valid_count}"
    )

    print(
        f"Rejected Records     : {rejected_count}"
    )

    print(
        f"Bronze Path          : {BRONZE_PATH}"
    )

    print(
        f"Silver Path          : {SILVER_PATH}"
    )

    print(
        f"Gold Path            : {GOLD_PATH}"
    )

    print("=" * 70)

    print()
    print("GOLD FLEET METRICS:")
    print()

    gold_df.show(
        20,
        truncate=False,
    )

    logger.info(
        "Spark EV pipeline completed successfully."
    )


# ============================================================
# ERROR HANDLING
# ============================================================

except Exception:

    logger.exception(
        "Spark pipeline failed."
    )

    raise


# ============================================================
# SHUTDOWN
# ============================================================

finally:

    logger.info(
        "Stopping Spark session..."
    )

    spark.stop()

    logger.info(
        "Spark session stopped."
    )