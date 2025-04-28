import uuid
from datetime import datetime
from typing import List, Optional

from app.db.dynamodb import db  # Изменение импорта с mongodb на dynamodb
from app.models.truck.schemas import TruckCreateSchema, TruckResponseSchema

class TruckCRUD:
    """
    Логика для trucks, с использованием DynamoDB вместо MongoDB.
    """

    async def create_truck(self, data: TruckCreateSchema) -> Optional[TruckResponseSchema]:
        """Создает новую запись грузовика в DynamoDB."""
        doc = data.dict()
        # Используем id вместо _id для DynamoDB
        doc["id"] = str(uuid.uuid4())
        doc["type"] = "truck"
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()
        doc["is_verified"] = False
        doc["ai_loader_ready"] = False

        await db.create_vehicle(doc)
        new_doc = await db.get_vehicle(doc["id"])
        if new_doc:
            # Обратите внимание, что DynamoDB возвращает документ с id, а не _id
            # Но наш TruckResponseSchema ожидает поле _id
            if "id" in new_doc and "_id" not in new_doc:
                new_doc["_id"] = new_doc["id"]
            return TruckResponseSchema(**new_doc)
        return None

    async def list_trucks(self) -> List[TruckResponseSchema]:
        """Возвращает список всех грузовиков из DynamoDB."""
        vehicles = await db.list_vehicles()
        if not vehicles:
            return []

        # Фильтруем только documents с type="truck"
        trucks = [v for v in vehicles if v.get("type") == "truck"]

        results = []
        for d in trucks:
            # Убедимся, что _id существует для совместимости со схемой
            if "id" in d and "_id" not in d:
                d["_id"] = d["id"]
            results.append(TruckResponseSchema(**d))
        return results

    async def get_truck(self, truck_id: str) -> Optional[TruckResponseSchema]:
        """Получает один грузовик по ID из DynamoDB."""
        doc = await db.get_vehicle(truck_id)
        if doc and doc.get("type") == "truck":
            # Убедимся, что _id существует для совместимости
            if "id" in doc and "_id" not in doc:
                doc["_id"] = doc["id"]
            return TruckResponseSchema(**doc)
        return None

    async def update_truck(self, truck_id: str, updates: dict) -> Optional[TruckResponseSchema]:
        """Обновляет данные грузовика в DynamoDB."""
        updates["updated_at"] = datetime.utcnow()
        success = await db.update_vehicle(truck_id, updates)
        if not success:
            return None

        doc = await db.get_vehicle(truck_id)
        if doc:
            # Убедимся, что _id существует для совместимости
            if "id" in doc and "_id" not in doc:
                doc["_id"] = doc["id"]
            return TruckResponseSchema(**doc)
        return None

    async def delete_truck(self, truck_id: str) -> bool:
        """Удаляет грузовик из DynamoDB."""
        return await db.delete_vehicle(truck_id)


# Экземпляр CRUD для использования в API
truck_crud = TruckCRUD()