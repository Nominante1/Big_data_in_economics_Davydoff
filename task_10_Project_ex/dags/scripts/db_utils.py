import os
import sys
import psycopg2
from dotenv import load_dotenv

def get_db_config():
    # Если мы локально на Windows, подгружаем .env
    if not os.getenv('AIRFLOW_HOME'):
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        load_dotenv(env_path)

    # Умный выбор хоста и порта
    if os.getenv('AIRFLOW_HOME'):
        host = 'postgres'  # Внутри Docker база называется postgres
        port = '5432'      # Внутри Docker она слушает стандартный порт
    else:
        host = 'localhost' # С твоего Windows база доступна на localhost
        port = '5433'      # Через проброшенный порт 5433

    config = {
        'host': host,
        'port': port,
        'database': os.getenv("DB_NAME"),
        'user': os.getenv("DB_USER"),
        'password': os.getenv("DB_PASSWORD")
    }  
    return config

def get_connection():
    try:
        config = get_db_config()
        conn = psycopg2.connect(**config)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        sys.exit(1)