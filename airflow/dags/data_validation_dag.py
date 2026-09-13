from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psycopg2


def validate_data():
    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow",
        port="5432"
    )

    cursor = conn.cursor()

    # Total records
    cursor.execute("SELECT COUNT(*) FROM ev_data")
    total = cursor.fetchone()[0]

    # Null checks
    cursor.execute("""
        SELECT COUNT(*)
        FROM ev_data
        WHERE battery IS NULL
        OR temp IS NULL
        OR speed IS NULL
    """)
    null_count = cursor.fetchone()[0]

    # Invalid battery values
    cursor.execute("""
        SELECT COUNT(*)
        FROM ev_data
        WHERE battery < 0 OR battery > 100
    """)
    invalid_battery = cursor.fetchone()[0]

    # Invalid temperature values
    cursor.execute("""
        SELECT COUNT(*)
        FROM ev_data
        WHERE temp < -20 OR temp > 100
    """)
    invalid_temp = cursor.fetchone()[0]

    print(f"Total Records: {total}")
    print(f"Null Records: {null_count}")
    print(f"Invalid Battery Records: {invalid_battery}")
    print(f"Invalid Temperature Records: {invalid_temp}")

    conn.close()


with DAG(
    dag_id="data_validation_dag",
    start_date=datetime(2025, 1, 1),
    schedule="@hourly",
    catchup=False
) as dag:

    validation_task = PythonOperator(
        task_id="validate_ev_data",
        python_callable=validate_data
    )

    validation_task
