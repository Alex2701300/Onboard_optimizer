# app/models/truck/crud.py

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.truck.schemas import TruckCreateSchema, TruckResponseSchema
from app.db.mongodb import db  # Это ваш MongoDB singleton

class TruckCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_truck(self, truck_data: TruckCreateSchema) -> Optional[TruckResponseSchema]:
        """
        Создать новый грузовик, храним _id как строку (UUID).
        """
        # Преобразуем Pydantic-схему в словарь
        truck_dict = truck_data.dict()
        # Генерируем строковый _id
        truck_id = str(uuid.uuid4())
        truck_dict["_id"] = truck_id

        # Укажем type="truck", чтобы отличать
        truck_dict["type"] = "truck"

        # Добавим служебные поля
        truck_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_verified": False,
            "ai_loader_ready": False
        })

        try:
            await self.collection.insert_one(truck_dict)
            # Теперь получаем обратно в формате TruckResponseSchema
            return await self.get_truck(truck_id)
        except Exception:
            return None

    async def get_truck(self, truck_id: str) -> Optional[TruckResponseSchema]:
        """
        Найти грузовик по _id=truck_id (строка).
        """
        doc = await self.collection.find_one({"_id": truck_id, "type": "truck"})
        if not doc:
            return None
        return TruckResponseSchema(**doc)

    async def update_truck_configuration(self, truck_id: str, update_data: Dict[str, Any]) -> Optional[TruckResponseSchema]:
        """
        Обновить поля в документе. Возвращает TruckResponseSchema или None.
        """
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": truck_id, "type": "truck"},
            {"$set": update_data}
        )
        if result.modified_count < 1:
            return None
        # Снова считываем
        return await self.get_truck(truck_id)

    async def delete_truck(self, truck_id: str) -> bool:
        """
        Удалить грузовик. Возвращает True, если что-то удалилось.
        """
        result = await self.collection.delete_one({"_id": truck_id, "type": "truck"})
        return (result.deleted_count > 0)

    async def list_trucks(self) -> List[TruckResponseSchema]:
        """
        Вернуть список всех документов, у которых type="truck"
        """
        cursor = self.collection.find({"type": "truck"})
        docs = await cursor.to_list(length=None)
        # Преобразуем в список TruckResponseSchema
        return [TruckResponseSchema(**d) for d in docs]

# Инициализируем экземпляр CRUD
truck_crud = TruckCRUD(db.vehicles)