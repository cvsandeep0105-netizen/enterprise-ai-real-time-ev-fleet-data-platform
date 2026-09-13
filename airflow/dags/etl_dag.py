from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
# pandas imported inside ETL task
from sqlalchemy import create_engine, Integer, Boolean, Text, TIMESTAMP
import logging
import os

# ==========================
# DEFAULT ARGUMENTS
# ==========================
default_args = {
    "owner": "Sandeep",
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}

# ==========================
# DATABASE CONFIG
# ==========================
POSTGRES_USER = os.getenv("POSTGRES_USER", "airflow")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "airflow")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_DB = os.getenv("POSTGRES_DB", "airflow")

# ==========================
# EXTRACT
# ==========================
def extract():

    logging.info("Extract Task Started")

    df = pd.read_csv("/opt/airflow/data/ev_vehicle_data.csv")

    df.to_csv(
        "/opt/airflow/data/extracted.csv",
        index=False
    )

    logging.info(f"Extracted {len(df)} records")


# ==========================
# TRANSFORM
# ==========================
def transform():
    print("Transforming data")

    df = pd.read_csv("/opt/airflow/data/extracted.csv")

    # Remove duplicate rows
    df = df.drop_duplicates()

    # Remove rows with missing values
    df = df.dropna()

    # Standardize column names
    df.columns = [c.lower().replace(" ", "_") for c in df.columns]

    # Ensure numeric columns are valid
    df["battery"] = pd.to_numeric(df["battery"], errors="coerce")
    df["temp"] = pd.to_numeric(df["temp"], errors="coerce")
    df["speed"] = pd.to_numeric(df["speed"], errors="coerce")

    # Remove invalid records
    df = df.dropna()

    # Battery must be between 0 and 100
    df = df[(df["battery"] >= 0) & (df["battery"] <= 100)]

    # Temperature range
    df = df[(df["temp"] >= -40) & (df["temp"] <= 100)]

    # Speed cannot be negative
    df = df[df["speed"] >= 0]
    # Battery Health
    df["battery_status"] = df["battery"].apply(
    lambda x: "Low" if x < 20
    else "Medium" if x < 80
    else "High"
)

    # Vehicle Status
    df["vehicle_status"] = df["speed"].apply(
    lambda x: "Stopped" if x == 0 else "Running"
)

    # Temperature Status
    df["temperature_status"] = df["temp"].apply(
    lambda x: "Hot" if x > 40
    else "Cold" if x < 10
    else "Normal"
)

   # Charging Flag
    df["is_charging"] = df["charging_status"].apply(
    lambda x: True if x == "Charging" else False
)

    print(f"Valid Records: {len(df)}")
    print("=" * 50)
    print(f"Total Valid Records : {len(df)}")
    print(f"Low Battery Vehicles : {(df['battery'] < 20).sum()}")
    print(f"Charging Vehicles : {df['is_charging'].sum()}")
    print(f"Stopped Vehicles : {(df['speed'] == 0).sum()}")
    print("=" * 50)
    df.to_csv(
        "/opt/airflow/data/transformed.csv",
        index=False
    )
    logging.info(f"Transformed {len(df)} records")


# ==========================
# LOAD
# ==========================
def load():

    import time

    logging.info("Load Task Started")

    start_time = time.time()

    engine = None

    try:

        df = pd.read_csv(
            "/opt/airflow/data/transformed.csv"
        )

        engine = create_engine(
            f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"
        )

        with engine.begin() as connection:

            df.to_sql(
                "ev_data",
                connection,
                if_exists="replace",
                index=False,
                method="multi",
                chunksize=1000
            )

        elapsed = round(time.time() - start_time, 2)

        logging.info("=" * 60)
        logging.info(f"Rows Loaded : {len(df)}")
        logging.info(f"Execution Time : {elapsed} sec")
        logging.info("Load Completed Successfully")
        logging.info("=" * 60)

    except Exception as e:

        logging.error(f"Load Failed : {e}")

        raise

    finally:

        if engine is not None:
            engine.dispose()

        logging.info("Database Connection Closed")


# ==========================
# DAG
# ==========================
with DAG(
    dag_id="etl_pipeline_dag",
    description="Real-Time EV Analytics ETL Pipeline",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["etl", "ev", "production"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_task",
        python_callable=extract,
    )

    transform_task = PythonOperator(
        task_id="transform_task",
        python_callable=transform,
    )

    load_task = PythonOperator(
        task_id="load_task",
        python_callable=load,
    )

    extract_task >> transform_task >> load_task

