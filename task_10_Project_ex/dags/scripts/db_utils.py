import os
import sys
from dotenv import load_dotenv
import psycopg2

# ОПРЕДЕЛЯЕМ ПУТИ
# Если переменная окружения AIRFLOW_HOME существует, значит мы внутри Docker.
# Иначе - мы на локальном компе (для тестов)
if os.getenv('AIRFLOW_HOME'):
    DATA_DIR = '/opt/airflow/datasets' #зависит от твоего docker-compose.yml
else:
    # Локальные пути для тестирования на Windows
    load_dotenv('.env') # Питон сам найдет .env файл, если он лежит рядом
    DATA_DIR = os.path.join(os.getcwd(), 'datasets')


# получение параметров подключения
def get_db_config():
    """
    Формирует словарь с параметрами подключения к БД.    
    """

    load_dotenv()
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv("DB_PORT"),
        'database': os.getenv("DB_NAME"),
        'user': os.getenv("DB_USER"),
        'password': os.getenv("DB_PASSWORD")
    }  
    print (config)
    return config

def get_connection():
    """Устанавливает и возвращает соединение с БД."""
    try:
        config = get_db_config()
        conn = psycopg2.connect(**config)
        conn.autocommit = False
        return conn
    except Exception as e:
        print(f"Ошибка подключения к БД: {e}")
        sys.exit(1)