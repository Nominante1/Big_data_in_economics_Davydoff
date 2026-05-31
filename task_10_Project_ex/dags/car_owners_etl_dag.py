from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Добавляем путь к папке scripts в PYTHONPATH, чтобы импорт работал
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from generate import step_1_generate_data
from load_row import step_2_load_raw
from transform_owner import step_3_transform_owner
from transform_fines import step_4_transform_fines
load_csv, run_transform, save_mart

def step_1_generate_data():
    print("Генерация синтетических данных через Faker...")
    # Здесь код генерации CSV файлов (car_owners.csv, cars.csv и т.д.)

def step_2_load_raw():
    print("Загрузка CSV файлов в сырые таблицы PostgreSQL...")
    # Здесь код: подключение к БД и выполнение команд \copy или INSERT

def step_3_transform():
    print("Трансформация данных: расчет агрегатов (штрафы, полисы)...")
    # Здесь код выполнения сложных SQL-запросов (твои CTE с JOIN и COUNT)
    # и сохранение результата во временные таблицы или dataframe

def step_4_create_mart():
    print("Создание итоговой витрины данных...")
    # Здесь код: берем результаты шага 3 и заливаем в финальную таблицу витрины

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# --- Определение самого DAG ---
with DAG(
    'car_owners_etl_pipeline', # Уникальное имя твоего DAG
    default_args=default_args,
    description='ETL пайплайн для ИДЗ: Владельцы, Авто, Штрафы',
    schedule_interval='0 2 * * *', # Запуск каждый день в 3:00 ночи
    catchup=False,
    tags=['idz', 'etl', 'cars'],
) as dag:

    #Генерация
    task_generate = PythonOperator(
        task_id='generate_data',
        python_callable=step_1_generate_data
    )

    #Загрузка сырых данных
    task_load = PythonOperator(
        task_id='load_raw',
        python_callable=step_2_load_raw
    )

    #Трансформация (SQL)
    task_transform = PythonOperator(
        task_id='transform_data',
        python_callable=step_3_transform
    )

    #Формирование витрины
    task_mart = PythonOperator(
        task_id='create_data_mart',
        python_callable=step_4_create_mart
    )

    #оператор >> указывает, что задача справа начнется только после УСПЕШНОГО завершения задачи слева
    task_generate >> task_load >> task_transform >> task_mart