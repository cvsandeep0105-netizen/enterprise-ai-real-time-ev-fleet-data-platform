from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import psycopg2
import os

default_args = {
    "owner": "Sandeep",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "airflow"),
    "user": os.getenv("POSTGRES_USER", "airflow"),
    "password": os.getenv("POSTGRES_PASSWORD", "airflow"),
}


def database_health():

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    COUNT(*),
                    COUNT(DISTINCT event_id),
                    COUNT(DISTINCT vehicle_id)
                FROM public.ev_data
                WHERE producer = 'ev-telemetry-producer'
            """)

            total, unique_events, vehicles = cur.fetchone()

            print("=" * 60)
            print("DATABASE HEALTH")
            print("=" * 60)
            print(f"Canonical records : {total}")
            print(f"Unique events     : {unique_events}")
            print(f"Vehicles          : {vehicles}")

            if total == 0:
                raise ValueError("No canonical telemetry records found")

            if total != unique_events:
                raise ValueError("Duplicate event IDs detected")

            print("DATABASE HEALTH : PASS")


    finally:
        conn.close()


def data_quality():

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT COUNT(*)
                FROM public.ev_data
                WHERE battery IS NULL
                   OR temp IS NULL
                   OR speed IS NULL
                   OR timestamp IS NULL
                   OR vehicle_id IS NULL
            """)

            null_count = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*)
                FROM public.ev_data
                WHERE battery < 0
                   OR battery > 100
                   OR speed < 0
                   OR temp < -40
                   OR temp > 150
            """)

            invalid_count = cur.fetchone()[0]

            print("=" * 60)
            print("DATA QUALITY")
            print("=" * 60)
            print(f"Null records    : {null_count}")
            print(f"Invalid records : {invalid_count}")

            if null_count > 0:
                raise ValueError(
                    f"Data quality failure: {null_count} null records"
                )

            if invalid_count > 0:
                raise ValueError(
                    f"Data quality failure: {invalid_count} invalid records"
                )

            print("DATA QUALITY : PASS")

    finally:
        conn.close()


def duplicate_check():

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT event_id
                    FROM public.ev_data
                    GROUP BY event_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """)

            duplicate_events = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*)
                FROM (
                    SELECT vehicle_id, timestamp
                    FROM public.ev_data
                    GROUP BY vehicle_id, timestamp
                    HAVING COUNT(*) > 1
                ) duplicates
            """)

            duplicate_vehicle_timestamps = cur.fetchone()[0]

            print("=" * 60)
            print("DUPLICATE CHECK")
            print("=" * 60)
            print(f"Duplicate event IDs           : {duplicate_events}")
            print(
                f"Duplicate vehicle/timestamps : "
                f"{duplicate_vehicle_timestamps}"
            )

            if duplicate_events > 0:
                raise ValueError("Duplicate event IDs detected")

            if duplicate_vehicle_timestamps > 0:
                raise ValueError(
                    "Duplicate vehicle/timestamp records detected"
                )

            print("DUPLICATE CHECK : PASS")

    finally:
        conn.close()


def alert_health():

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT COUNT(*)
                FROM public.alerts
            """)

            total_alerts = cur.fetchone()[0]

            cur.execute("""
                SELECT COUNT(*)
                FROM public.dead_letter_queue
            """)

            dlq_records = cur.fetchone()[0]

            print("=" * 60)
            print("ALERT / DLQ HEALTH")
            print("=" * 60)
            print(f"Total alerts : {total_alerts}")
            print(f"DLQ records  : {dlq_records}")
            print("ALERT / DLQ HEALTH : PASS")

    finally:
        conn.close()


with DAG(
    dag_id="ev_fleet_platform",
    description="Production monitoring and data-quality orchestration for EV Fleet Data Platform",
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=[
        "ev",
        "fleet",
        "kafka",
        "postgres",
        "data-quality",
        "monitoring",
    ],
) as dag:

    db_health = PythonOperator(
        task_id="database_health",
        python_callable=database_health,
    )

    quality = PythonOperator(
        task_id="data_quality",
        python_callable=data_quality,
    )

    duplicates = PythonOperator(
        task_id="duplicate_check",
        python_callable=duplicate_check,
    )

    alerts = PythonOperator(
        task_id="alert_dlq_health",
        python_callable=alert_health,
    )

    db_health >> quality >> duplicates >> alerts
