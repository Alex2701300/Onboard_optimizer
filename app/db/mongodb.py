# app/db/mongodb.py

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from ..core.config import get_settings
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None
    vehicles: AsyncIOMotorCollection = None
    setups: AsyncIOMotorCollection = None
    loading_experience: AsyncIOMotorCollection = None

    async def connect_to_database(self):
        """Инициализирует подключение к MongoDB и настраивает коллекции"""
        try:
            logger.info(f"Connecting to MongoDB URL: {settings.MONGODB_URL}")
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000
            )
            # Проверка соединения
            await self.client.admin.command('ping')
            
            self.db = self.client[settings.MONGODB_DB_NAME]
            
            # Инициализация коллекций
            self.vehicles = self.db.vehicles
            self.setups = self.db.setups
            self.loading_experience = self.db.loading_experience

            # Создание индексов
            await self._create_indexes()

            logger.info(f"Successfully connected to MongoDB: {settings.MONGODB_DB_NAME}")
            return True

        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            self.client = None
            self.db = None
            return False

    async def _create_indexes(self):
        """Создает необходимые индексы для оптимизации запросов"""
        indexes = [
            # Для Vehicles
            {
                "collection": self.vehicles,
                "keys": [("vin", 1)],
                "options": {"unique": True, "sparse": True}
            },
            {
                "collection": self.vehicles,
                "keys": [("vehicle_type", 1)],
                "options": {}
            },
            {
                "collection": self.vehicles,
                "keys": [("truck_type", 1), ("deck_count", 1)],
                "options": {"name": "truck_type_deck_count_index"}
            },
            {
                "collection": self.vehicles,
                "keys": [("vertical_connections.upper_platform_id", 1)],
                "options": {"name": "vertical_connections_index"}
            },

            # Для Setups
            {
                "collection": self.setups,
                "keys": [("configuration_hash", 1)],
                "options": {"unique": True}
            },

            # Для Loading Experience
            {
                "collection": self.loading_experience,
                "keys": [("truck_id", 1), ("timestamp", -1)],
                "options": {"name": "truck_loading_history"}
            }
        ]

        for index in indexes:
            try:
                await index["collection"].create_index(
                    index["keys"],
                    **index.get("options", {})
                )
            except Exception as e:
                logger.warning(f"Failed to create index: {str(e)}")

    async def close_database_connection(self):
        """Корректно закрывает соединение с базой данных"""
        if self.client:
            await self.client.close()
            logger.info("MongoDB connection closed")

    # -------------------- Методы для Vehicles (универсальные) --------------------

    async def create_vehicle(self, vehicle_data: Dict[str, Any]) -> str:
        """Создает новую запись транспортного средства"""
        try:
            result = await self.vehicles.insert_one(vehicle_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating vehicle: {str(e)}")
            raise e

    async def list_vehicles(self) -> List[Dict[str, Any]]:
        """
        Возвращает список всех транспортных средств (документы из коллекции vehicles).
        """
        try:
            cursor = self.vehicles.find({})
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error listing vehicles: {str(e)}")
            raise e

    async def get_vehicle(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Получает транспортное средство по ID"""
        try:
            return await self.vehicles.find_one({"_id": vehicle_id})
        except Exception as e:
            logger.error(f"Error getting vehicle {vehicle_id}: {str(e)}")
            return None

    async def update_vehicle(self, vehicle_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновляет данные транспортного средства"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            result = await self.vehicles.update_one(
                {"_id": vehicle_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating vehicle {vehicle_id}: {str(e)}")
            return False

    async def delete_vehicle(self, vehicle_id: str) -> bool:
        """Удаляет транспортное средство"""
        try:
            result = await self.vehicles.delete_one({"_id": vehicle_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting vehicle {vehicle_id}: {str(e)}")
            return False

    # -------------------- Специфичные методы для Truck --------------------

    async def get_truck_configuration(self, truck_id: str) -> Optional[Dict[str, Any]]:
        """Получает полную конфигурацию грузовика"""
        try:
            return await self.vehicles.find_one(
                {"_id": truck_id, "vehicle_type": "truck"},
                projection={
                    "nickname": 1,
                    "configuration": 1,
                    "deck_count": 1,
                    "vertical_connections": 1
                }
            )
        except Exception as e:
            logger.error(f"Error getting truck config {truck_id}: {str(e)}")
            return None

    async def update_truck_platforms(self, truck_id: str, platforms: List[Dict[str, Any]]) -> bool:
        """Обновляет конфигурацию платформ грузовика"""
        try:
            result = await self.vehicles.update_one(
                {"_id": truck_id},
                {"$set": {
                    "configuration.platforms": platforms,
                    "updated_at": datetime.utcnow()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating truck platforms {truck_id}: {str(e)}")
            return False

    async def update_chain_configuration(
        self,
        truck_id: str,
        chain_config: Dict[str, List[str]]
    ) -> bool:
        """
        Обновляет словарь {platform_id: [edge_positions]} — 
        какие платформы/края используют цепи.
        """
        try:
            result = await self.vehicles.update_one(
                {"_id": truck_id},
                {
                    "$set": {
                        "chain_configurations": chain_config,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating chain config for {truck_id}: {str(e)}")
            return False

    # -------------------- Методы для работы с Loading Experience --------------------

    async def log_loading_experience(self, experience_data: Dict[str, Any]) -> str:
        """Логирует опыт загрузки"""
        try:
            experience_data["timestamp"] = datetime.utcnow()
            result = await self.loading_experience.insert_one(experience_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error logging loading experience: {str(e)}")
            raise e

    async def get_loading_history(self, truck_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает историю загрузок для грузовика"""
        try:
            cursor = self.loading_experience.find(
                {"truck_id": truck_id}
            ).sort("timestamp", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting loading history for {truck_id}: {str(e)}")
            return []

    # -------------------- Методы для работы с Setups --------------------

    async def save_configuration(self, config_data: Dict[str, Any]) -> str:
        """Сохраняет конфигурацию загрузки"""
        try:
            result = await self.setups.insert_one(config_data)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            raise e

    async def get_configuration(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Получает сохраненную конфигурацию"""
        try:
            return await self.setups.find_one({"_id": config_id})
        except Exception as e:
            logger.error(f"Error getting configuration {config_id}: {str(e)}")
            return None


# Инициализация синглтона
db = MongoDB()