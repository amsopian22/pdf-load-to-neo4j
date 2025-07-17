from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

def print_hello():
    return 'Hello World from Airflow!'

def print_goodbye():
    return 'Goodbye from Airflow!'

# Default arguments
default_args = {
    'owner': 'admin',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'hello_world_dag',
    default_args=default_args,
    description='A simple Hello World DAG',
    schedule_interval=timedelta(days=1),
    catchup=False,
)

# Tasks
hello_task = PythonOperator(
    task_id='hello_task',
    python_callable=print_hello,
    dag=dag,
)

goodbye_task = PythonOperator(
    task_id='goodbye_task',
    python_callable=print_goodbye,
    dag=dag,
)

date_task = BashOperator(
    task_id='date_task',
    bash_command='date',
    dag=dag,
)

# Task dependencies
hello_task >> date_task >> goodbye_task