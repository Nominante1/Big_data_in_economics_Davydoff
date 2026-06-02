import sys
import os
from psycopg2 import sql
from psycopg2.extras import execute_values
from db_utils import get_connection  # Импортируем подключение из нашего модуля!

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_schema(conn):
    """Создаёт схему dmr, если она ещё не существует."""
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS dmr;")
        conn.commit()
        print("Схема dmr успешно создана (или уже существовала).")

def create_owner_violations_table(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS dmr.owner_violations(
        owner_id            INTEGER NOT NULL,
        full_name           VARCHAR(255) NOT NULL,
        total_fines         INTEGER,
        total_amount_unpaid DECIMAL(10,2),
        num_cars            INTEGER,
        expired_insurances  INTEGER,
        last_update         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (owner_id)
    );
    """
    with conn.cursor() as cur:
        cur.execute(create_table_query)
        conn.commit()
        print("Таблица dmr.owner_violations готова.")

def insert_data_owner_violations(conn):
    select_query = """
    WITH owner_cars AS (
        SELECT owner_id, COUNT(car_id) AS num_cars
        FROM cars
        GROUP BY owner_id
    ),
    owner_fines AS (
        SELECT cars.owner_id,
               COUNT(fines.fine_id) AS total_fines,
               SUM(CASE WHEN fines.status = 'Не оплачен' THEN fines.amount ELSE 0 END) AS total_amount_unpaid
        FROM fines
        JOIN cars ON fines.car_id = cars.car_id
        GROUP BY cars.owner_id
    ),
    owner_expired_insurances AS (
        SELECT cars.owner_id,
               COUNT(policies.policy_id) AS expired_insurances
        FROM policies
        JOIN cars ON policies.car_id = cars.car_id
        WHERE policies.end_date < CURRENT_DATE
        GROUP BY cars.owner_id
    )
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
        owner_id, full_name, total_fines, total_amount_unpaid, num_cars, expired_insurances
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
            print("Нет данных для вставки (owner_violations).")
            return
        
        execute_values(cur, insert_query, rows, page_size=1000)
        conn.commit()        
        print(f"Витрина владельцев обновлена. Обраработано записей: {len(rows)}")


def step_3_transform_owner():
    """Главная функция для 3 шага (запускается из DAG)."""
    print("--- СТАРТ ШАГА 3: Трансформация Владельцев ---")
    conn = get_connection()
    try:
        create_schema(conn)
        create_owner_violations_table(conn)
        insert_data_owner_violations(conn)
    except Exception as e:
        print(f"Ошибка в процессе трансформации: {e}")
        if conn: conn.rollback()
        raise e
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    step_3_transform_owner()