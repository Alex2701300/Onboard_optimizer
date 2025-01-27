# app/models/car/crud.py

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.mongodb import db  # наш синглтон
from app.models.car.schemas import CarCreateSchema, CarResponseSchema

class CarCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_car(self, car_data: CarCreateSchema) -> Optional[CarResponseSchema]:
        """
        Создать новый автомобиль, храним _id как строку (UUID).
        """
        car_dict = car_data.dict()
        car_id = str(uuid.uuid4())
        car_dict["_id"] = car_id

        # Укажем type="car"
        car_dict["type"] = "car"

        # Служебные поля
        car_dict["created_at"] = datetime.utcnow()
        car_dict["updated_at"] = datetime.utcnow()

        try:
            await self.collection.insert_one(car_dict)
            return await self.get_car(car_id)
        except Exception:
            return None

    async def get_car(self, car_id: str) -> Optional[CarResponseSchema]:
        """
        Найти автомобиль по _id=car_id и type="car"
        """
        doc = await self.collection.find_one({"_id": car_id, "type": "car"})
        if not doc:
            return None
        return CarResponseSchema(**doc)

    async def update_car(self, car_id: str, update_data: Dict[str, Any]) -> Optional[CarResponseSchema]:
        """
        Обновить поля в документе (car). Возвращает CarResponseSchema или None.
        """
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": car_id, "type": "car"},
            {"$set": update_data}
        )
        if result.modified_count < 1:
            return None
        return await self.get_car(car_id)

    async def delete_car(self, car_id: str) -> bool:
        """
        Удалить автомобиль. Возвращает True, если что-то удалилось.
        """
        result = await self.collection.delete_one({"_id": car_id, "type": "car"})
        return (result.deleted_count > 0)

    async def list_cars(self) -> List[CarResponseSchema]:
        """
        Список всех documents, где type="car"
        """
        cursor = self.collection.find({"type": "car"})
        docs = await cursor.to_list(length=None)
        return [CarResponseSchema(**d) for d in docs]

# Инициализируем CRUD, используя db.vehicles
car_crud = CarCRUD(db.vehicles)