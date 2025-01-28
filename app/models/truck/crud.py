import uuid
from datetime import datetime
from typing import List, Optional

from app.db.mongodb import db
from app.models.truck.schemas import TruckCreateSchema, TruckResponseSchema

class TruckCRUD:
    """
    Логика для trucks, аналогичная cars (через uuid4, без счётчиков).
    """

    async def create_truck(self, data: TruckCreateSchema) -> Optional[TruckResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB 'vehicles' is not init.")

        doc = data.dict()
        # Вместо счётчика — uuid4 (как в cars)
        doc["_id"] = str(uuid.uuid4())

        doc["type"] = "truck"
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()
        doc["is_verified"] = False
        doc["ai_loader_ready"] = False

        await coll.insert_one(doc)
        new_doc = await coll.find_one({"_id": doc["_id"]})
        if new_doc:
            return TruckResponseSchema(**new_doc)
        return None

    async def list_trucks(self) -> List[TruckResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB 'vehicles' is not init.")

        docs = await coll.find({"type": "truck"}).to_list(None)
        if not docs:
            return []

        results = []
        for d in docs:
            # Переносим _id -> id, как в cars
            d["id"] = str(d["_id"])
            results.append(TruckResponseSchema(**d))
        return results

    async def get_truck(self, truck_id: str) -> Optional[TruckResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB 'vehicles' is not init.")

        doc = await coll.find_one({"_id": truck_id, "type": "truck"})
        if doc:
            return TruckResponseSchema(**doc)
        return None

    async def update_truck(self, truck_id: str, updates: dict) -> Optional[TruckResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB 'vehicles' is not init.")

        updates["updated_at"] = datetime.utcnow()
        result = await coll.update_one(
            {"_id": truck_id, "type": "truck"},
            {"$set": updates}
        )
        if result.modified_count < 1:
            return None

        doc = await coll.find_one({"_id": truck_id, "type": "truck"})
        if doc:
            return TruckResponseSchema(**doc)
        return None

    async def delete_truck(self, truck_id: str) -> bool:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB 'vehicles' is not init.")

        result = await coll.delete_one({"_id": truck_id, "type": "truck"})
        return (result.deleted_count > 0)

truck_crud = TruckCRUD()