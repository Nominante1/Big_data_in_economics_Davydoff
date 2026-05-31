#!/bin/bash
set -e

# Выполняем SQL команды, используя psql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

    -- 1. Создаем таблицу автовладельцев (главная таблица, не имеет внешних ключей)
    CREATE TABLE IF NOT EXISTS car_owners (
        owner_id INTEGER PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        drive_license VARCHAR(255),
        address TEXT,
        phone VARCHAR(50)
    );

    -- Копируем данные из CSV файла
    \copy car_owners FROM '/datasets/car_owners.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');


    -- 2. Создаем таблицу автомобилей (ссылается на car_owners)
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

    -- Копируем данные автомобилей
    \copy cars FROM '/datasets/cars.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');


    -- 3. Создаем таблицу штрафов (ссылается на cars)
    CREATE TABLE IF NOT EXISTS fines (
        fine_id INTEGER PRIMARY KEY,
        car_id INTEGER,
        date DATE,
        article TEXT,
        amount DECIMAL(10, 2),
        status VARCHAR(50),
        CONSTRAINT fk_fines_car FOREIGN KEY (car_id) REFERENCES cars(car_id)
    );

    -- Копируем данные штрафов
    \copy fines FROM '/datasets/fines.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');


    -- 4. Создаем таблицу страховых полисов (ссылается на cars)
    CREATE TABLE IF NOT EXISTS policies (
        policy_id INTEGER PRIMARY KEY,
        car_id INTEGER,
        company VARCHAR(255),
        start_date DATE,
        end_date DATE,
        cost DECIMAL(10, 2),
        CONSTRAINT fk_policies_car FOREIGN KEY (car_id) REFERENCES cars(car_id)
    );

    -- Копируем данные полисов
    \copy policies FROM '/datasets/policies.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

EOSQL