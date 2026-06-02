import os
import sys
from db_utils import get_connection

# Добавляем родительскую папку в пути поиска Питона (чтобы работал локальный запуск)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем функцию подключения из нашего модуля-утилиты!
from scripts.db_utils import get_connection

# ОПРЕДЕЛЯЕМ ПУТИ К ДАННЫМ
if os.getenv('AIRFLOW_HOME'):
    DATA_DIR = '/opt/airflow/datasets'  # Путь внутри контейнера Docker
else:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets')


def step_2_load_raw():
    """Создает структуру и загружает CSV файлы в сырые таблицы PostgreSQL."""
    print("--- СТАРТ ШАГА 2: Загрузка сырых данных ---")
    conn = get_connection()
    
    tables_and_files = {
        'car_owners': 'car_owners.csv',
        'cars': 'cars.csv',
        'fines': 'fines.csv',
        'policies': 'policies.csv'
    }
    
    try:
        with conn.cursor() as cur:
            # --- 1. ДОБАВЛЕНО: Создание структуры таблиц, если их нет ---
            print("Создание сырых таблиц в схеме public (если они отсутствуют)...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS car_owners (
                    owner_id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    drive_license VARCHAR(255),
                    address TEXT,
                    phone VARCHAR(50)
                );

                CREATE TABLE IF NOT EXISTS cars (
                    car_id INTEGER PRIMARY KEY,
                    car_plate VARCHAR(50) NOT NULL,
                    year INTEGER,
                    brand VARCHAR(100),
                    model VARCHAR(100),
                    vin VARCHAR(100),
                    color VARCHAR(50),
                    owner_id INTEGER,
                    CONSTRAINT fk_owner FOREIGN KEY (owner_id) REFERENCES car_owners(owner_id)
                );

                CREATE TABLE IF NOT EXISTS fines (
                    fine_id INTEGER PRIMARY KEY,
                    car_id INTEGER,
                    date DATE,
                    article TEXT,
                    amount DECIMAL(10, 2),
                    status VARCHAR(50),
                    CONSTRAINT fk_fines_car FOREIGN KEY (car_id) REFERENCES cars(car_id)
                );

                CREATE TABLE IF NOT EXISTS policies (
                    policy_id INTEGER PRIMARY KEY,
                    car_id INTEGER,
                    company VARCHAR(255),
                    start_date DATE,
                    end_date DATE,
                    cost DECIMAL(10, 2),
                    CONSTRAINT fk_policies_car FOREIGN KEY (car_id) REFERENCES cars(car_id)
                );
            """)
            
            # --- 2. Очистка перед загрузкой свежих данных (Идемпотентность) ---
            print("Очистка старых сырых данных (TRUNCATE)...")
            cur.execute("TRUNCATE TABLE car_owners CASCADE;")
            
            # --- 3. Загрузка из CSV файлов ---
            for table, filename in tables_and_files.items():
                filepath = os.path.join(DATA_DIR, filename)
                print(f"Загрузка данных из {filepath} в таблицу {table}...")
                
                if not os.path.exists(filepath):
                    raise FileNotFoundError(f"Файл не найден: {filepath}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    copy_sql = f"COPY {table} FROM STDIN WITH CSV HEADER DELIMITER as ','"
                    cur.copy_expert(sql=copy_sql, file=f)
                    
        conn.commit()
        print("Все сырые таблицы созданы и заполнены!")
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"Ошибка при загрузке данных: {e}")
        raise e
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    step_2_load_raw()