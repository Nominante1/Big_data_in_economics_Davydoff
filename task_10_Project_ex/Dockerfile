# Используем официальный образ PostgreSQL
FROM postgres:13

# Копируем папку с наборами данных внутрь образа
# Она будет доступна для скрипта инициализации
COPY datasets /datasets/

# # Копируем скрипт инициализации, который будет исполнен при старте
# COPY init.sh /docker-entrypoint-initdb.d/

FROM apache/airflow:2.10.4
RUN pip install psycopg2-binary python-dotenv

COPY requirements.txt /
# Устанавливаем их
RUN pip install --no-cache-dir -r /requirements.txt