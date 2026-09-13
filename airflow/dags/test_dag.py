from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def hello():
    print("Infrastructure 100 Percent Complete")

with DAG(
    dag_id="test_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False
) as dag:

    task = PythonOperator(
        task_id="hello_task",
        python_callable=hello
    )
