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
dotenv_path = os.path.join(project_root, 'Big data in economics(for GitHub)/task_10_Project_ex', '.env')

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

#создание таблицы в новом слое
def create_owner_violations_table(conn):

    create_table_query = """
    CREATE TABLE IF NOT EXISTS dmr.owner_violations(
        owner_id            INTEGER NOT NULL,
        full_name           VARCHAR(255) NOT NULL,
        total_fines         INTEGER,
        total_amount_unpaid DECIMAL(10,2),
        num_cars            INTEGER,
        expired_insurances  INTEGER,
        last_update    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (owner_id)
    );
    """
    # + выполнение скрипта
    with conn.cursor() as cur:
        cur.execute(create_table_query)
        conn.commit()
        print("Таблица dmr.owner_violations успешно создана.")

def create_fine_stats_table(conn):

    create_table_query = """
    CREATE TABLE IF NOT EXISTS dmr.fine_stats(
        article             TEXT NOT NULL,
        total_fines         INTEGER,
        avg_amount          DECIMAL(10,2),
        payment_rate        DECIMAL(5,2),
        last_update    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (article)
    );
    """
    # + выполнение скрипта
    with conn.cursor() as cur:
        cur.execute(create_table_query)
        conn.commit()
        print("Таблица dmr.fine_stats успешно создана.")

#
# НАПИСАНИЕ SQL-запроса ДЛЯ ЗАПОЛНЕНИЯ dmr.analytics_student_perfomance
#

def insert_data_owner_violations(conn):
    select_query = """
WITH owner_cars AS (
    --считаем только машины
    SELECT 
        owner_id, 
        COUNT(car_id) AS num_cars
    FROM cars
    GROUP BY owner_id
),
owner_fines AS (
    --считаем все штрафы и сумму только неоплаченных в одном месте
    SELECT 
        cars.owner_id,
        COUNT(fines.fine_id) AS total_fines,
        --используем CASE, чтобы суммировать только нужные статусы
        SUM(CASE WHEN fines.status = 'Не оплачен' THEN fines.amount ELSE 0 END) AS total_amount_unpaid
    FROM fines
    JOIN cars ON fines.car_id = cars.car_id
    GROUP BY cars.owner_id
),
owner_expired_insurances AS (
    -- Считаем только просроченные полисы
    SELECT 
        cars.owner_id,
        COUNT(policies.policy_id) AS expired_insurances
    FROM policies
    JOIN cars ON policies.car_id = cars.car_id
    WHERE policies.end_date < CURRENT_DATE
    GROUP BY cars.owner_id
)
--Итоговая витрина
SELECT 
    o.owner_id,
    o.name AS full_name,
    COALESCE(f.total_fines, 0) AS total_fines,
    COALESCE(f.total_amount_unpaid, 0) AS total_amount_unpaid,
    COALESCE(c.num_cars, 0) AS num_cars,
    COALESCE(i.expired_insurances, 0) AS expired_insurances
FROM car_owners o
    LEFT JOIN owner_cars c ON o.owner_id = c.owner_id
    LEFT JOIN owner_fines f ON o.owner_id = f.owner_id
    LEFT JOIN owner_expired_insurances i ON o.owner_id = i.owner_id;
    """


    insert_query = sql.SQL("""
    INSERT INTO dmr.owner_violations (
        owner_id,
        full_name,
        total_fines,
        total_amount_unpaid,
        num_cars,
        expired_insurances
    )
    VALUES %s
    ON CONFLICT (owner_id)
    DO UPDATE SET
        full_name = EXCLUDED.full_name,
        total_fines = EXCLUDED.total_fines,
        total_amount_unpaid = EXCLUDED.total_amount_unpaid,
        num_cars = EXCLUDED.num_cars,
        expired_insurances = EXCLUDED.expired_insurances,
        last_update = CURRENT_TIMESTAMP;
""")
    with conn.cursor() as cur:
        cur.execute(select_query)
        rows = cur.fetchall()
        
        if not rows:
            print("Нет данных для вставки.")
            return
        
        execute_values(cur, insert_query, rows, page_size=1000)
        conn.commit()        
        print(f"Витрина заполнена. Добавлено/обновлено записей: {len(rows)}")

def insert_data_fine_stats(conn):
    select_query = """
SELECT 
    article,
    COUNT(fine_id) AS total_fines,
    ROUND(AVG(amount), 2) AS avg_amount,
    ROUND(
        (COUNT(CASE WHEN status = 'Оплачен' THEN 1 END) * 100.0) 
        / 
        NULLIF(COUNT(fine_id), 0), 
        2
    ) AS payment_rate
FROM fines
GROUP BY article
ORDER BY total_fines DESC;
    """
    insert_query = sql.SQL("""
    INSERT INTO dmr.fine_stats (
        article,
        total_fines,
        avg_amount,
        payment_rate
    )
    VALUES %s
    ON CONFLICT (article)
    DO UPDATE SET
        total_fines = EXCLUDED.total_fines,
        avg_amount = EXCLUDED.avg_amount,
        payment_rate = EXCLUDED.payment_rate,
        last_update = CURRENT_TIMESTAMP;
""")

    with conn.cursor() as cur:
        cur.execute(select_query)
        rows = cur.fetchall()

        if not rows:
            print("Нет данных для вставки.")
            return

        execute_values(cur, insert_query, rows, page_size=1000)
        conn.commit()
        print(f"Витрина заполнена. Добавлено/обновлено записей: {len(rows)}")

def main():
    """Последовательное выполнение шагов."""
    conn = None
    try:
        conn = get_connection()
        create_schema(conn)
        create_owner_violations_table(conn)
        insert_data_owner_violations(conn)
        create_fine_stats_table(conn)
        insert_data_fine_stats(conn)
        print("\nВсе операции выполнены успешно!")
    except Exception as e:
        print(f"Ошибка в процессе выполнения: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Соединение с БД закрыто.")

if __name__ == "__main__":
    main()