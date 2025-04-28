from typing import List, Optional
from datetime import datetime
import uuid

from app.db.dynamodb import db  # Заменяем MongoDB на DynamoDB
from app.models.car.schemas import CarCreateSchema, CarResponseSchema

class CarCRUD:
    """
    CRUD для Cars с использованием DynamoDB.
    При каждом вызове мы используем методы db.vehicles из dynamodb.py
    """

    async def create_car(self, data: CarCreateSchema) -> Optional[CarResponseSchema]:
        """Создает новый автомобиль в DynamoDB."""
        # Преобразуем входные данные в словарь
        doc = data.dict()

        # Генерируем id для DynamoDB
        doc["id"] = f"car{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        doc["type"] = "car"
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()

        # Добавляем документ в DynamoDB
        await db.create_vehicle(doc)

        # Считываем обратно из базы, чтобы вернуть полные данные
        new_doc = await db.get_vehicle(doc["id"])
        if new_doc:
            # Обеспечиваем совместимость с CarResponseSchema
            if "id" in new_doc and "_id" not in new_doc:
                new_doc["_id"] = new_doc["id"]

            # При необходимости можно дополнить недостающие поля:
            if "model" not in new_doc:
                new_doc["model"] = ""

            return CarResponseSchema(**new_doc)
        return None

    async def list_cars(self) -> List[CarResponseSchema]:
        """Возвращает список всех автомобилей из DynamoDB."""
        # Получаем все транспортные средства
        vehicles = await db.list_vehicles()

        # Фильтруем только автомобили (type="car")
        cars = [v for v in vehicles if v.get("type") == "car"]

        # Если в БД нет ни одной машины, вернём пустой список
        if not cars:
            return []

        # Преобразуем каждый doc -> CarResponseSchema
        results = []
        for d in cars:
            # Переносим DynamoDB id -> поле "_id" для совместимости
            if "id" in d and "_id" not in d:
                d["_id"] = d["id"]

            results.append(CarResponseSchema(**d))

        return results

    async def get_car(self, car_id: str) -> Optional[CarResponseSchema]:
        """Получает автомобиль по ID из DynamoDB."""
        doc = await db.get_vehicle(car_id)
        if doc and doc.get("type") == "car":
            # Обеспечиваем совместимость с CarResponseSchema
            if "id" in doc and "_id" not in doc:
                doc["_id"] = doc["id"]

            return CarResponseSchema(**doc)
        return None

    async def update_car(self, car_id: str, updates: dict) -> Optional[CarResponseSchema]:
        """Обновляет данные автомобиля в DynamoDB."""
        # Обновляем поле updated_at при каждом изменении
        updates["updated_at"] = datetime.utcnow()

        success = await db.update_vehicle(car_id, updates)
        if not success:
            return None

        doc = await db.get_vehicle(car_id)
        if doc:
            # Обеспечиваем совместимость с CarResponseSchema
            if "id" in doc and "_id" not in doc:
                doc["_id"] = doc["id"]

            return CarResponseSchema(**doc)
        return None

    async def delete_car(self, car_id: str) -> bool:
        """Удаляет автомобиль из DynamoDB."""
        return await db.delete_vehicle(car_id)


# Экземпляр CRUD для использования в API
car_crud = CarCRUD()