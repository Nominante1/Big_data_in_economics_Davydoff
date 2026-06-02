import os
import sys

from psycopg2 import sql
from psycopg2.extras import execute_values
from db_utils import get_connection 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
    with conn.cursor() as cur:
        cur.execute(create_table_query)
        conn.commit()
        print("Таблица dmr.fine_stats готова.")

def insert_data_fine_stats(conn):
    select_query = """
    SELECT 
        article,
        COUNT(fine_id) AS total_fines,
        ROUND(AVG(amount), 2) AS avg_amount,
        ROUND((COUNT(CASE WHEN status = 'Оплачен' THEN 1 END) * 100.0) / NULLIF(COUNT(fine_id), 0), 2) AS payment_rate
    FROM fines
    GROUP BY article
    ORDER BY total_fines DESC;
    """
    
    insert_query = sql.SQL("""
    INSERT INTO dmr.fine_stats (article, total_fines, avg_amount, payment_rate)
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
            print("Нет данных для вставки (fine_stats).")
            return

        execute_values(cur, insert_query, rows, page_size=1000)
        conn.commit()
        print(f"Витрина штрафов обновлена. Обраработано записей: {len(rows)}")


def step_4_transform_fines():
    """Главная функция для 4 шага (запускается из DAG)."""
    print("--- СТАРТ ШАГА 4: Создание витрины штрафов ---")
    conn = get_connection()
    try:
        create_fine_stats_table(conn)
        insert_data_fine_stats(conn)
    except Exception as e:
        print(f"Ошибка в процессе создания витрины: {e}")
        if conn: conn.rollback()
        raise e
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    step_4_transform_fines()