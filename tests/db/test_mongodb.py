import pytest
from app.db.mongodb import db
from datetime import datetime

@pytest.fixture
async def mongodb():
    """Фикстура для подключения к тестовой базе данных"""
    await db.connect_to_database()
    yield db
    await db.close_database_connection()

@pytest.mark.asyncio
async def test_mongodb_connection(mongodb):
    """Тест подключения к MongoDB"""
    assert mongodb.client is not None
    assert mongodb.db is not None

    # Проверяем что все коллекции доступны
    assert mongodb.vehicles is not None
    assert mongodb.setups is not None
    assert mongodb.loading_experience is not None

@pytest.mark.asyncio
async def test_vehicles_operations(mongodb):
    """Тест операций с транспортными средствами"""
    # Тестируем создание car
    test_car = {
        "vehicle_type": "car",
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "dimensions": {
            "length": 192.1,
            "width": 72.4,
            "height": 56.9,
            "curb_weight": 3500.0
        },
        "body_type": "sedan",
        "status": "run&drive",
        "created_at": datetime.utcnow()
    }

    car_result = await mongodb.create_vehicle(test_car)
    assert car_result.inserted_id is not None

    # Тестируем создание truck
    test_truck = {
        "vehicle_type": "truck",
        "make": "Peterbilt",
        "model": "389",
        "year": 2021,
        "created_at": datetime.utcnow()
    }

    truck_result = await mongodb.create_vehicle(test_truck)
    assert truck_result.inserted_id is not None

    # Получение по ID
    car = await mongodb.get_vehicle(car_result.inserted_id)
    assert car is not None
    assert car["vehicle_type"] == "car"
    assert car["make"] == "Toyota"

    # Поиск по типу
    cars = await mongodb.get_vehicles_by_type("car")
    assert len(cars) >= 1
    trucks = await mongodb.get_vehicles_by_type("truck")
    assert len(trucks) >= 1

    # Поиск по критериям
    toyota_cars = await mongodb.get_vehicles_by_criteria(
        {"vehicle_type": "car", "make": "Toyota"}
    )
    assert len(toyota_cars) >= 1

    # Обновление
    update_result = await mongodb.update_vehicle(
        car_result.inserted_id,
        {"status": "inoperable-rolling"}
    )
    assert update_result.modified_count == 1

    updated_car = await mongodb.get_vehicle(car_result.inserted_id)
    assert updated_car["status"] == "inoperable-rolling"

    # Очистка
    await mongodb.vehicles.delete_one({"_id": car_result.inserted_id})
    await mongodb.vehicles.delete_one({"_id": truck_result.inserted_id})

@pytest.mark.asyncio
async def test_setups_operations(mongodb):
    """Тест операций с setups"""
    test_setup = {
        "type": "stinger",
        "capacity": 9,
        "weight_limit": 80000,
        "truck_id": "test_truck_id",
        "trailer_id": "test_trailer_id",
        "created_at": datetime.utcnow()
    }

    # Создание
    result = await mongodb.create_setup(test_setup)
    assert result.inserted_id is not None

    # Получение
    setup = await mongodb.get_setup(result.inserted_id)
    assert setup is not None
    assert setup["type"] == "stinger"

    # Поиск по критериям
    stinger_setups = await mongodb.get_setups_by_criteria({"type": "stinger"})
    assert len(stinger_setups) >= 1

    # Обновление
    update_result = await mongodb.update_setup(
        result.inserted_id,
        {"weight_limit": 85000}
    )
    assert update_result.modified_count == 1

    updated_setup = await mongodb.get_setup(result.inserted_id)
    assert updated_setup["weight_limit"] == 85000

    # Очистка
    await mongodb.setups.delete_one({"_id": result.inserted_id})

@pytest.mark.asyncio
async def test_loading_experience_operations(mongodb):
    """Тест операций с loading_experience"""
    test_experience = {
        "vehicle_id": "test_vehicle",
        "setup_id": "test_setup",
        "success": True,
        "loading_time": 15.5,
        "created_at": datetime.utcnow()
    }

    # Создание
    result = await mongodb.create_loading_experience(test_experience)
    assert result.inserted_id is not None

    # Получение с фильтром
    experiences = await mongodb.get_loading_experiences({"success": True})
    assert len(experiences) >= 1

    # Обновление
    update_result = await mongodb.update_loading_experience(
        result.inserted_id,
        {"loading_time": 16.0}
    )
    assert update_result.modified_count == 1

    # Очистка
    await mongodb.loading_experience.delete_one({"_id": result.inserted_id})