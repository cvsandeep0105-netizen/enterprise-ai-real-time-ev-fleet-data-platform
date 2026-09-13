from __future__ import annotations

import os
import sys

from pyspark.sql import SparkSession


def create_spark_session(app_name: str = "EV-Fleet-Data-Platform"):
    python = sys.executable

    os.environ["PYSPARK_PYTHON"] = python
    os.environ["PYSPARK_DRIVER_PYTHON"] = python
    os.environ["PYTHON_EXECUTABLE"] = python

    return (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")
        .config("spark.pyspark.python", python)
        .config("spark.pyspark.driver.python", python)
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")

        # Windows local filesystem configuration.
        .config(
            "spark.hadoop.fs.file.impl",
            "org.apache.hadoop.fs.RawLocalFileSystem",
        )
        .config(
            "spark.hadoop.fs.file.impl.disable.cache",
            "true",
        )

        # Prevent Hadoop from requiring the missing Windows native DLL
        # for local filesystem permission checks.
        .config(
            "spark.hadoop.io.native.lib.available",
            "false",
        )

        # Use the standard Spark output committer.
        .config(
            "spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version",
            "2",
        )

        .getOrCreate()
    )
