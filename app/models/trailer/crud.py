import uuid
from datetime import datetime
from typing import List, Optional

from app.db.dynamodb import db  # Заменяем MongoDB на DynamoDB
from app.models.trailer.schemas import TrailerCreateSchema, TrailerResponseSchema

class TrailerCRUD:
    """
    Логика для trailers с использованием DynamoDB вместо MongoDB.
    """

    async def create_trailer(self, data: TrailerCreateSchema) -> Optional[TrailerResponseSchema]:
        """Создает новый трейлер в DynamoDB."""
        doc = data.dict()
        # Используем id вместо _id для DynamoDB
        doc["id"] = str(uuid.uuid4())
        doc["type"] = "trailer"
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()

        await db.create_vehicle(doc)
        new_doc = await db.get_vehicle(doc["id"])
        if new_doc:
            # Обеспечиваем совместимость с TrailerResponseSchema
            if "id" in new_doc and "_id" not in new_doc:
                new_doc["_id"] = new_doc["id"]

            return TrailerResponseSchema(**new_doc)
        return None

    async def list_trailers(self) -> List[TrailerResponseSchema]:
        """Возвращает список всех трейлеров из DynamoDB."""
        vehicles = await db.list_vehicles()
        if not vehicles:
            return []

        # Фильтруем только трейлеры (type="trailer")
        trailers = [v for v in vehicles if v.get("type") == "trailer"]

        results = []
        for d in trailers:
            # Обеспечиваем совместимость с TrailerResponseSchema
            if "id" in d and "_id" not in d:
                d["_id"] = d["id"]

            results.append(TrailerResponseSchema(**d))
        return results

    async def get_trailer(self, trailer_id: str) -> Optional[TrailerResponseSchema]:
        """Получает трейлер по ID из DynamoDB."""
        doc = await db.get_vehicle(trailer_id)
        if doc and doc.get("type") == "trailer":
            # Обеспечиваем совместимость с TrailerResponseSchema
            if "id" in doc and "_id" not in doc:
                doc["_id"] = doc["id"]

            return TrailerResponseSchema(**doc)
        return None

    async def update_trailer(self, trailer_id: str, updates: dict) -> Optional[TrailerResponseSchema]:
        """Обновляет данные трейлера в DynamoDB."""
        updates["updated_at"] = datetime.utcnow()
        success = await db.update_vehicle(trailer_id, updates)
        if not success:
            return None

        doc = await db.get_vehicle(trailer_id)
        if doc:
            # Обеспечиваем совместимость с TrailerResponseSchema
            if "id" in doc and "_id" not in doc:
                doc["_id"] = doc["id"]

            return TrailerResponseSchema(**doc)
        return None

    async def delete_trailer(self, trailer_id: str) -> bool:
        """Удаляет трейлер из DynamoDB."""
        return await db.delete_vehicle(trailer_id)


# Экземпляр CRUD для использования в API
trailer_crud = TrailerCRUD()