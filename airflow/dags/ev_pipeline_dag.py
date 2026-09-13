from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psycopg2

def check_pipeline():

    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow",
        port="5432"
    )

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM vehicle_data")

    count = cursor.fetchone()[0]

    print(f"Current records in ev_data: {count}")

    conn.close()

with DAG(
    dag_id="ev_pipeline_monitor",
    start_date=datetime(2025,1,1),
    schedule="*/5 * * * *",
    catchup=False
) as dag:

    monitor_task = PythonOperator(
        task_id="check_pipeline",
        python_callable=check_pipeline
    )
