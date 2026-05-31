import os
import sys
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

#  ПОДГОТОВКА К ВЫПОЛНЕНИЮ (ВСЁ, КАК БЫЛО)

# Загружаем переменные из .env файла (если он есть)
current_dir = os.getcwd()
project_root = os.path.dirname(current_dir)
dotenv_path = os.path.join(project_root, 'Big data in economics(for GitHub)/task_2_Docker', '.env')

print(current_dir)
print(project_root)
print(dotenv_path)

load_dotenv(dotenv_path)

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

# подключение к БД
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


# создание нового слоя в БД (схема dmr)
def create_schema(conn):
    """Создаёт схему dmr, если она ещё не существует."""
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS dmr;")
        conn.commit()
        print("Схема dmr успешно создана (или уже существовала).")