# app/models/car/crud.py

from typing import List, Optional
from datetime import datetime
import uuid

from app.db.mongodb import db  # "ленивый" доступ
from app.models.car.schemas import CarCreateSchema, CarResponseSchema


class CarCRUD:
    """
    CRUD для Cars. 
    При каждом вызове мы берём db.vehicles и проверяем, что не None.
    """

    async def create_car(self, data: CarCreateSchema) -> Optional[CarResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB collection 'vehicles' is not initialized.")

        doc = data.dict()
        # Генерируем _id:
        doc["_id"] = str(uuid.uuid4())
        doc["type"] = "car"
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()

        await coll.insert_one(doc)
        new_doc = await coll.find_one({"_id": doc["_id"]})
        if new_doc:
            # Убедимся что _id это строка и добавим model если отсутствует
            new_doc["_id"] = str(new_doc["_id"])
            if "model" not in new_doc:
                new_doc["model"] = ""  # или другое значение по умолчанию
            # Convert _id to string before passing to schema
            if "_id" in new_doc:
                new_doc["_id"] = str(new_doc["_id"])
            return CarResponseSchema.from_mongo(new_doc)
        return None

    async def list_cars(self) -> List[CarResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB collection 'vehicles' is not initialized.")

        cursor = coll.find({"type": "car"})
        docs = await cursor.to_list(length=None)
        # Преобразуем каждый doc -> CarResponseSchema
        return [CarResponseSchema(**d) for d in docs]

    async def get_car(self, car_id: str) -> Optional[CarResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB collection 'vehicles' is not initialized.")

        doc = await coll.find_one({"_id": car_id, "type": "car"})
        if doc:
            return CarResponseSchema(**doc)
        return None

    async def update_car(self, car_id: str, updates: dict) -> Optional[CarResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB collection 'vehicles' is not initialized.")

        updates["updated_at"] = datetime.utcnow()
        result = await coll.update_one(
            {"_id": car_id, "type": "car"},
            {"$set": updates}
        )
        if result.modified_count < 1:
            return None

        doc = await coll.find_one({"_id": car_id, "type": "car"})
        if doc:
            return CarResponseSchema(**doc)
        return None

    async def delete_car(self, car_id: str) -> bool:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB collection 'vehicles' is not initialized.")

        result = await coll.delete_one({"_id": car_id, "type": "car"})
        return (result.deleted_count > 0)


car_crud = CarCRUD()