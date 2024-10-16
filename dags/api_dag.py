import json 
from datetime import datetime
from airflow.models import DAG
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator

def save_posts(ti) -> None:
    # Kiểm tra xem posts có dữ liệu không
    posts = ti.xcom_pull(task_ids=['get_post'])
        # Ghi dữ liệu từ API vào file JSON
    with open('dags/data/api_data.json', 'w') as f:
        json.dump(posts[0], f)  # Ghi toàn bộ dữ liệu từ API vào file JSON

dag =  DAG(
    dag_id= 'api_dag', 
    schedule='@daily',
    start_date=datetime(2024, 10, 5),
    catchup= False
)  
task_is_api_active = HttpSensor(
    task_id = 'is_api_active',
    http_conn_id='http_default',
    endpoint='posts/',
    dag = dag
)
task_get_post = SimpleHttpOperator(
    task_id = 'get_post',
    http_conn_id='http_default',
    endpoint='posts/',
    method='GET',
    response_filter= lambda response: json.loads(response.text),
    log_response= True,
    dag = dag
        
    )

task_save = PythonOperator(
    task_id = 'save_post',
    python_callable= save_posts,
    dag = dag
)

task_is_api_active >> task_get_post >> task_save
