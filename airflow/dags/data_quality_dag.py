from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psycopg2


def quality_check():

    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow",
        port="5432"
    )

    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM ev_data
        WHERE battery IS NULL
           OR temp IS NULL
           OR speed IS NULL
    """)

    null_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM ev_data
        WHERE battery < 0 OR battery > 100
    """)

    invalid_battery = cursor.fetchone()[0]

    print(f"Null Records: {null_count}")
    print(f"Invalid Battery Records: {invalid_battery}")

    conn.close()


with DAG(
    dag_id="data_quality_dag",
    start_date=datetime(2025,1,1),
    schedule="@hourly",
    catchup=False
) as dag:

    quality_task = PythonOperator(
        task_id="quality_check",
        python_callable=quality_check
    )
