import pandas as pd
import random
from faker import Faker
from datetime import datetime, timedelta
from faker_vehicle import VehicleProvider
from collections import Counter
import os
import sys

fake.add_provider(VehicleProvider)
fake = Faker('ru_RU')
Faker.seed(42)      # фиксируем seed для воспроизводимости
random.seed(42)

N_CAR_OWNERS = 1000
N_CARS = 1200
N_FINES = 5000
N_POLICIES = 1500

DATA_DIR = '/datasets'

# DataFrame с владельцами автомобилей
def generate_car_owners(n):
   
    car_owners = []
    for i in range(1, n + 1):

        used_licenses = set()

        while True:
            dl = f"{fake.random_int(10, 99)} {fake.random_int(10, 99)} {fake.random_int(100000, 999999)}"
            if dl not in used_licenses:
                used_licenses.add(dl)
                break

        car_owners.append({
            'owner_id': i,
            'name': fake.name(),
            'drive_license': dl,
            'address': fake.address().replace('\n', ', '),
            'phone': fake.phone_number()
        })
    return pd.DataFrame(car_owners)

def generate_cars(n):
   
    cars = []
    for i in range(1, n + 1):
        year, make, model = (fake.vehicle_year_make_model().split(' ', 2)) #получение полной информации об авто

        owner_ids = list(range(1, N_CAR_OWNERS + 1)) #первые 1000 машин принадлежат первым 1000 владельцам
        extra = [random.randint(1, N_CAR_OWNERS) for _ in range(N_CARS - N_CAR_OWNERS)] #рандомные владельцы для оставшихся 200 машин
        owner_ids.extend(extra)
        #random.shuffle(owner_ids) # перемешиваем, чтобы не было очевидной связи между id машины и владельца

        cars.append({
            'car_id': i,
            'car_plate': fake.license_plate(),
            'year': year,
            'brand': make,
            'model': model,
            'vin': fake.vin(),
            'color': fake.color_name(),
            'owner_id': owner_ids[i - 1] # каждый владелец должен иметь хотя бы 1 машину
        })
    return pd.DataFrame(cars)

def generate_fines(n):
    violation_articles = [
    "Статья 12.9 ч.2 (Превышение скорости на 20-40 км/ч)",
    "Статья 12.12 ч.1 (Проезд на красный свет)",
    "Статья 12.19 ч.3 (Остановка на пешеходном переходе)",
    "Статья 12.16 ч.4 (Выезд на встречную полосу)",
    "Статья 12.6 (Непристегнутый ремень безопасности)",
    "Статья 12.8 ч.1 (Управление ТС в состоянии опьянения)",
    "Статья 12.18 (Непредоставление преимущества пешеходу)",
    "Статья 12.36.1 (Использование телефона за рулем)"
]
    fines = []
    for i in range(1, n + 1):

        fines.append({
            'fine_id': i,
            'car_id': random.randint(1, N_CARS),
            'date': fake.date_this_year(),
            'article': random.choice(violation_articles),
            'amount': random.randrange(500, 5001, 500),
            'status': random.choice(['Оплачен', 'Не оплачен'])
        })
    return pd.DataFrame(fines)

def generate_insurance_policies(n_policies):
    policies = []


    car_ids = list(range(1, N_CARS + 1))
                                                                # из 1500:
    insured_cars = random.sample(car_ids, k=int(N_CARS * 0.9)) # 1080 машин будут застрахованы, остальные 120 - нет
    extra_policies = random.choices(insured_cars, k= n_policies - len(insured_cars)) # 1500 - 1080 =  420 полисов будут случайно распределены между застрахованными машинами

    companies = ['Росгосстрах', 'Ингосстрах', 'АльфаСтрахование', 'РЕСО-Гарантия', 'ВСК', 'Т-Страхование']

    policy_counts = Counter(insured_cars) # считаем, сколько полисов приходится на каждую застрахованную машину (вид: {car_id: count_policies})
    for car in extra_policies:
        policy_counts[car] += 1

    policy_id = 1

    for car_id, count in policy_counts.items():
    #полис действует 1 год. 
    # Если дата старта > 1 года назад -> последний полис будет просрочен, < 1 года назад -> последний полис будет активен.
        
        latest_start_date = fake.date_time_between(start_date='-400d', end_date='now')#у 33% будет просроченный полис
        base_start_date = latest_start_date - timedelta(days=365 * (count - 1))#отмотали время назад на количество полисов

        for i in range(count):
            # Каждый следующий полис начинается через год после предыдущего
            start_date = base_start_date + timedelta(days=365 * i)
            end_date = start_date + timedelta(days=365)
            
            policies.append({
                'policy_id': policy_id,
                'car_id': car_id,
                'company': random.choice(companies),
                'start_date': start_date,
                'end_date': end_date,
                'cost': random.randint(5000, 25000)
            })
            policy_id += 1
    return pd.DataFrame(policies)


def step_1_generate_data():
    print(f"Начинаем генерацию данных. Инициализировано владельцев: {N_CAR_OWNERS}")
    
    # Создаем папку, если вдруг её нет
    os.makedirs(DATA_DIR, exist_ok=True)

    # Вызываем твои генераторы
    car_owners_df = generate_car_owners(N_CAR_OWNERS)
    cars_df = generate_cars(N_CARS)
    fines_df = generate_fines(N_FINES)
    policies_df = generate_insurance_policies(N_POLICIES)

    # Сохраняем с использованием абсолютных путей!
    car_owners_df.to_csv(os.path.join(DATA_DIR, 'car_owners.csv'), index=False)
    cars_df.to_csv(os.path.join(DATA_DIR, 'cars.csv'), index=False)
    fines_df.to_csv(os.path.join(DATA_DIR, 'fines.csv'), index=False)
    policies_df.to_csv(os.path.join(DATA_DIR, 'policies.csv'), index=False)

    print(f"Данные успешно сгенерированы и сохранены в папку {DATA_DIR}")