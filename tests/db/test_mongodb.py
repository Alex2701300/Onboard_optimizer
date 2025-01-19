import pytest
from app.db.mongodb import db

@pytest.fixture
async def mongodb():
    await db.connect_to_database()
    yield db
    await db.close_database_connection()

@pytest.mark.asyncio
async def test_mongodb_connection(mongodb):
    assert mongodb.client is not None
    assert mongodb.db is not None

    # Проверяем что все коллекции доступны
    assert mongodb.vehicles is not None
    assert mongodb.setups is not None
    assert mongodb.loading_experience is not None

@pytest.mark.asyncio
async def test_vehicles_operations(mongodb):
    test_vehicle = {
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "dimensions": {
            "length": 192.1,
            "width": 72.4,
            "height": 56.9
        }
    }

    result = await mongodb.create_vehicle(test_vehicle)
    assert result.inserted_id is not None

    vehicle = await mongodb.get_vehicle(result.inserted_id)
    assert vehicle is not None
    assert vehicle["make"] == "Toyota"

    await mongodb.vehicles.delete_one({"_id": result.inserted_id})

@pytest.mark.asyncio
async def test_setups_operations(mongodb):
    test_setup = {
        "type": "stinger",
        "capacity": 9,
        "weight_limit": 80000
    }

    result = await mongodb.create_setup(test_setup)
    assert result.inserted_id is not None

    setup = await mongodb.get_setup(result.inserted_id)
    assert setup is not None
    assert setup["type"] == "stinger"

    await mongodb.setups.delete_one({"_id": result.inserted_id})one({"_id": result.inserted_id})

@pytest.mark.asyncio
async def test_loading_experience_operations(mongodb):
    test_experience = {
        "vehicle_id": "test_vehicle",
        "setup_id": "test_setup",
        "success": True,
        "loading_time": 15.5
    }

    result = await mongodb.create_loading_experience(test_experience)
    assert result.inserted_id is not None

    experiences = await mongodb.get_loading_experiences({"success": True})
    assert len(experiences) >= 1

    await mongodb.loading_experience.delete_one({"_id": result.inserted_id})