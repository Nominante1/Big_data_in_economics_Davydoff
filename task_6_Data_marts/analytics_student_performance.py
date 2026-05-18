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

#
# ИЗМЕНЕНИЕ CREATE TABLE
#

# создание таблицы dmr.analytics_student_perfomance для витрины (нужно добавить поля из задания)
def create_table(conn):

    create_table_query = """
    CREATE TABLE IF NOT EXISTS dmr.analytics_student (
        student_id      INTEGER NOT NULL,
        course_id       INTEGER NOT NULL,
        department_id   INTEGER,
        department_name VARCHAR(50),
        education_level VARCHAR(50),
        education_base  VARCHAR(50),
        semester        INTEGER,
        course_year     INTEGER,
        final_grade     INTEGER CHECK (final_grade IN (2,3,4,5)),
        total_events    INTEGER,
        avg_weekly_events   DECIMAL(10,2),
        total_course_views  INTEGER,
        total_quiz_views    INTEGER,
        total_module_views  INTEGER,
        total_submissions   INTEGER,
        peak_activity_week  INTEGER,
        consistency_score   DECIMAL(10,2),
        activity_category   VARCHAR(50),
        last_update    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (student_id, course_id)
    );
    """
    # + выполнение скрипта
    with conn.cursor() as cur:
        cur.execute(create_table_query)
        conn.commit()
        print("Таблица dmr.analytics_student успешно создана.")

#
# НАПИСАНИЕ SQL-запроса ДЛЯ ЗАПОЛНЕНИЯ dmr.analytics_student_perfomance
#

def insert_data(conn):
    select_query = """
        WITH student_final AS (
        SELECT 
            userid,
            courseid,
            department_id,
            department_name,
            education_level,
            education_base,
            semester,
            course_year,
            final_grade,
            

        FROM public.USER_LOGS
            INNER JOIN public.DEPARTMENTS ON USER_LOGS.department_id = DEPARTMENTS.id
        WHERE namer_level IS NOT NULL
        GROUP BY userid, courseid
    )
    """