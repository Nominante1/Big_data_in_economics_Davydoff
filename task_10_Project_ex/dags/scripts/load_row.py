import os
import sys

# Добавляем родительскую папку в пути поиска Питона (чтобы работал локальный запуск)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем функцию подключения из нашего модуля-утилиты!
from scripts.db_utils import get_connection

# ОПРЕДЕЛЯЕМ ПУТИ К ДАННЫМ
if os.getenv('AIRFLOW_HOME'):
    DATA_DIR = '/opt/airflow/datasets'  # Путь внутри контейнера Docker
else:
    # Локальный путь на Windows (папка datasets находится на уровень выше скрипта)
    # Использование __file__ надежнее, чем os.getcwd()
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'datasets')


def step_2_load_raw():
    """Загружает CSV файлы в сырые таблицы PostgreSQL."""
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
            print("Очистка старых сырых данных (TRUNCATE)...")
            cur.execute("TRUNCATE TABLE car_owners CASCADE;")
            
            for table, filename in tables_and_files.items():
                filepath = os.path.join(DATA_DIR, filename)
                print(f"Загрузка данных из {filepath} в таблицу {table}...")
                
                # Проверка, существует ли файл
                if not os.path.exists(filepath):
                    raise FileNotFoundError(f"Файл не найден: {filepath}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    copy_sql = f"COPY {table} FROM STDIN WITH CSV HEADER DELIMITER as ','"
                    cur.copy_expert(sql=copy_sql, file=f)
                    
        conn.commit()
        print("Все сырые данные успешно загружены в базу!")
        
    except Exception as e:
        if conn: conn.rollback()
        print(f"Ошибка при загрузке данных: {e}")
        raise e
    finally:
        if conn: # Защита: закрываем только если соединение реально создалось
            conn.close()

# Блок для ручного тестирования (запустится только если нажать Play в редакторе)
if __name__ == "__main__":
    step_2_load_raw()