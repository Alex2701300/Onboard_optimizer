from motor.motor_asyncio import AsyncIOMotorClient
from ..core.config import get_settings
from typing import Optional, List

settings = get_settings()

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    vehicles = None
    setups = None 
    loading_experience = None

    async def connect_to_database(self):
        """Подключение к базе данных"""
        try:
            self.client = AsyncIOMotorClient(settings.MONGODB_URL)
            self.db = self.client[settings.MONGODB_DB_NAME]

            # Инициализация коллекций
            self.vehicles = self.db.Vehicles
            self.setups = self.db.Setups
            self.loading_experience = self.db.Loading_experience

            # Проверка подключения
            await self.client.admin.command('ping')
            print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")

            # Создание индексов для vehicles
            await self.vehicles.create_index([("vin", 1)], unique=True, sparse=True)
            await self.vehicles.create_index([("vehicle_type", 1)])
            # Составной индекс для поиска по типу и основным характеристикам
            await self.vehicles.create_index([
                ("vehicle_type", 1),
                ("year", 1),
                ("make", 1),
                ("model", 1)
            ])

        except Exception as e:
            print(f"Could not connect to MongoDB: {e}")
            raise e

    async def close_database_connection(self):
        """Закрытие соединения с базой данных"""
        if self.client:
            self.client.close()
            print("Closed MongoDB connection")

    # Методы для работы с коллекцией Vehicles
    async def get_vehicles_collection(self):
        return self.vehicles

    async def create_vehicle(self, vehicle_data: dict):
        return await self.vehicles.insert_one(vehicle_data)

    async def get_vehicle(self, vehicle_id: str):
        return await self.vehicles.find_one({"_id": vehicle_id})

    async def get_vehicles_by_type(self, vehicle_type: str):
        return await self.vehicles.find({"vehicle_type": vehicle_type}).to_list(length=None)

    async def get_vehicles_by_criteria(self, criteria: dict):
        return await self.vehicles.find(criteria).to_list(length=None)

    async def update_vehicle(self, vehicle_id: str, update_data: dict):
        return await self.vehicles.update_one(
            {"_id": vehicle_id},
            {"$set": update_data}
        )

    async def delete_vehicle(self, vehicle_id: str):
        return await self.vehicles.delete_one({"_id": vehicle_id})

    # Методы для работы с коллекцией Setups
    async def get_setups_collection(self):
        return self.setups

    async def create_setup(self, setup_data: dict):
        return await self.setups.insert_one(setup_data)

    async def get_setup(self, setup_id: str):
        return await self.setups.find_one({"_id": setup_id})

    async def get_setups_by_criteria(self, criteria: dict):
        return await self.setups.find(criteria).to_list(length=None)

    async def update_setup(self, setup_id: str, update_data: dict):
        return await self.setups.update_one(
            {"_id": setup_id},
            {"$set": update_data}
        )

    # Методы для работы с коллекцией Loading_experience
    async def get_loading_experience_collection(self):
        return self.loading_experience

    async def create_loading_experience(self, experience_data: dict):
        return await self.loading_experience.insert_one(experience_data)

    async def get_loading_experiences(self, filter_criteria: dict = None):
        if filter_criteria is None:
            filter_criteria = {}
        return await self.loading_experience.find(filter_criteria).to_list(length=None)

    async def update_loading_experience(self, experience_id: str, update_data: dict):
        return await self.loading_experience.update_one(
            {"_id": experience_id},
            {"$set": update_data}
        )

db = MongoDB()