from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import psycopg2


def check_pipeline():

    try:
        conn = psycopg2.connect(
            host="postgres",
            database="airflow",
            user="airflow",
            password="airflow"
        )

        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM vehicle_data")
        count = cursor.fetchone()[0]

        print("=" * 50)
        print("EV PIPELINE STATUS")
        print("=" * 50)
        print("PostgreSQL : Connected")
        print(f"Total Records : {count}")

        if count > 0:
            print("Pipeline Status : HEALTHY")
        else:
            print("Pipeline Status : NO DATA")

        print("=" * 50)

        cursor.close()
        conn.close()

    except Exception as e:
        print("Pipeline Failed")
        print(e)
        raise


with DAG(
    dag_id="monitoring_dag",
    start_date=datetime(2025, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
    tags=["monitoring"],
) as dag:

    monitor = PythonOperator(
        task_id="check_pipeline",
        python_callable=check_pipeline,
    )
