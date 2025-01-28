from typing import List, Optional
from datetime import datetime

# Нужно импортировать ReturnDocument из pymongo
from pymongo import ReturnDocument

from app.db.mongodb import db  # Ленивое подключение к Mongo
from app.models.car.schemas import CarCreateSchema, CarResponseSchema

async def get_next_car_id() -> str:
    """
    Увеличивает счётчик для 'car_counter' и формирует ID вида: car0000001, car0000002, ...
    Хранит счётчик в коллекции db.counters, документ {'_id': 'car_counter'}.
    """
    counters_coll = db.counters
    if counters_coll is None:
        raise RuntimeError("MongoDB collection 'counters' is not initialized.")

    result = await counters_coll.find_one_and_update(
        {"_id": "car_counter"},
        {"$inc": {"seq": 1}},           # Увеличиваем счётчик на 1
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    seq_value = result["seq"]  # текущее значение счётчика
    # Формируем строку вида 'car0000001' (7 цифр с ведущими нулями)
    return f"car{seq_value:07d}"


class CarCRUD:
    """
    CRUD для Cars.
    При каждом вызове мы берём db.vehicles и проверяем, что не None.
    """

    async def create_car(self, data: CarCreateSchema) -> Optional[CarResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB collection 'vehicles' is not initialized.")

        # Преобразуем входные данные в словарь
        doc = data.dict()
        # Генерируем _id на основе счётчика
        doc["_id"] = await get_next_car_id()

        doc["type"] = "car"
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()

        # Добавляем документ в коллекцию
        await coll.insert_one(doc)

        # Считываем обратно из базы, чтобы вернуть полные данные
        new_doc = await coll.find_one({"_id": doc["_id"]})
        if new_doc:
            # При необходимости можно дополнить недостающие поля:
            if "model" not in new_doc:
                new_doc["model"] = ""
            return CarResponseSchema(**new_doc)
        return None

    async def list_cars(self) -> List[CarResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB collection 'vehicles' is not initialized.")

        cursor = coll.find({"type": "car"})
        docs = await cursor.to_list(length=None)

        # Если в БД нет ни одной машины, вернём пустой список
        if not docs:
            return []

        # Преобразуем каждый doc -> CarResponseSchema
        results = []
        for d in docs:
            # Переносим Mongo _id -> поле "id" (для фронтенда, React/Vue и т.п.)
            d["id"] = str(d["_id"])
            results.append(CarResponseSchema(**d))

        return results

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

        # Обновляем поле updated_at при каждом изменении
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


# Экземпляр CRUD для использования в коде
car_crud = CarCRUD()