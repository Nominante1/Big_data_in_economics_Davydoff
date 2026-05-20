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
    CREATE TABLE IF NOT EXISTS dmr.analytics_student_performance (
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
        print("Таблица dmr.analytics_student_performance успешно создана.")

#
# НАПИСАНИЕ SQL-запроса ДЛЯ ЗАПОЛНЕНИЯ dmr.analytics_student_perfomance
#

def insert_data(conn):
    select_query = """
         WITH base_aggr AS 
(
	SELECT
		USER_LOGS.userid AS student_id,
		USER_LOGS.courseid AS course_id,
		USER_LOGS.depart AS department_id,
		DEPARTMENTS.name AS department_name,
		CASE
			WHEN USER_LOGS.leveled = '1' THEN 'Baccalaureate'
			WHEN USER_LOGS.leveled = '2' THEN 'Magisteria'
			ELSE 'other'
		END AS education_level,
		CASE
			WHEN USER_LOGS.name_osno = '1' THEN 'Budget'
			WHEN USER_LOGS.name_osno = '2' THEN 'Contract'
			ELSE 'Other'
		END AS education_base,
		num_sem AS semester,
		kurs - 1 AS course_year,
		MAX(CAST(namer_level AS INTEGER)) AS final_grade,
		SUM(s_all) AS total_events,
		SUM(s_all) * 1.0 / COUNT(num_week) AS avg_weekly_events,
		SUM(s_course_viewed) AS total_course_views,
		SUM(s_q_attempt_viewed) AS total_quiz_views,
		SUM(s_a_course_module_viewed) AS total_module_views,
		SUM(s_a_submission_status_viewed) AS total_submissions,
		--в итоговой: здесь peak_activity_week
		SUM((CASE WHEN s_all > 0 THEN 1 ELSE 0 END) * 1.0) / COUNT(num_week) AS consistency_score
	FROM USER_LOGS
		INNER JOIN DEPARTMENTS ON DEPARTMENTS.id = USER_LOGS.depart
	GROUP BY student_id, course_id, department_id, department_name, education_level, education_base, semester, course_year
),
base_aggr_with_activity_category AS
(
	SELECT 
		*,
		CASE 
    		WHEN NTILE(3) OVER (PARTITION BY course_id ORDER BY avg_weekly_events) = 1 THEN 'Низкая'
    		WHEN NTILE(3) OVER (PARTITION BY course_id ORDER BY avg_weekly_events) = 2 THEN 'Средняя'
    		ELSE 'Высокая' 
		END AS activity_category
	FROM
		base_aggr
),
peak_activity_week_calc AS 
(
	SELECT 
		userid,
		courseid,
		s_all,
		num_week,
		ROW_NUMBER() OVER (
	    	PARTITION BY userid, courseid
	  		ORDER BY s_all DESC, num_week --на случай, если у двоих недель будет одинаковая активность
		) AS rn_activity_weeks
		FROM USER_LOGS
)
SELECT 
	student_id,
	course_id,
	department_id,
	department_name,
	education_level,
	education_base,
	semester,
	course_year,
	final_grade,
	total_events,
	avg_weekly_events,
	total_course_views,
	total_quiz_views,
	total_module_views,
	total_submissions,
	peak_activity.num_week AS peak_activity_week,
	consistency_score,
	activity_category,
	CURRENT_TIMESTAMP AS last_update
FROM base_aggr_with_activity_category AS base_table
	LEFT JOIN peak_activity_week_calc AS peak_activity
		ON base_table.student_id = peak_activity.userid AND base_table.course_id = peak_activity.courseid
WHERE peak_activity.rn_activity_weeks = 1
    """


    insert_query = sql.SQL("""
    INSERT INTO dmr.analytics_student_performance (
        student_id, 
        course_id, 
        department_id, 
        department_name, 
        education_level, 
        education_base, 
        semester, 
        course_year, 
        final_grade, 
        total_events, 
        avg_weekly_events, 
        total_course_views, 
        total_quiz_views, 
        total_module_views, 
        total_submissions, 
        peak_activity_week, 
        consistency_score, 
        activity_category, 
        last_update
    )
    VALUES %s
    ON CONFLICT (student_id, course_id) 
    DO UPDATE SET
        department_id      = EXCLUDED.department_id,
        department_name    = EXCLUDED.department_name,
        education_level    = EXCLUDED.education_level,
        education_base     = EXCLUDED.education_base,
        semester           = EXCLUDED.semester,
        course_year        = EXCLUDED.course_year,
        final_grade        = EXCLUDED.final_grade,
        total_events       = EXCLUDED.total_events,
        avg_weekly_events  = EXCLUDED.avg_weekly_events,
        total_course_views = EXCLUDED.total_course_views,
        total_quiz_views   = EXCLUDED.total_quiz_views,
        total_module_views = EXCLUDED.total_module_views,
        total_submissions  = EXCLUDED.total_submissions,
        peak_activity_week = EXCLUDED.peak_activity_week,
        consistency_score  = EXCLUDED.consistency_score,
        activity_category  = EXCLUDED.activity_category,
        last_update        = CURRENT_TIMESTAMP;
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
        create_table(conn)
        insert_data(conn)
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