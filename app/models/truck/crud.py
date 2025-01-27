from motor.motor_asyncio import AsyncIOMotorCollection
from app.models.truck.schemas import TruckCreateSchema, TruckResponseSchema
from app.db.mongodb import MongoDB
from datetime import datetime

class TruckCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_truck(self, truck_data: TruckCreateSchema) -> TruckResponseSchema:
        truck_dict = truck_data.dict()
        truck_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_verified": False,
            "ai_loader_ready": False
        })

        result = await self.collection.insert_one(truck_dict)
        return await self.get_truck(str(result.inserted_id))

    async def get_truck(self, truck_id: str) -> TruckResponseSchema:
        truck = await self.collection.find_one({"_id": truck_id})
        return TruckResponseSchema(**truck) if truck else None

    async def update_truck_configuration(self, truck_id: str, update_data: dict) -> TruckResponseSchema:
        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one(
            {"_id": truck_id},
            {"$set": update_data}
        )
        return await self.get_truck(truck_id)

    async def delete_truck(self, truck_id: str) -> bool:
        result = await self.collection.delete_one({"_id": truck_id})
        return result.deleted_count > 0

    async def list_trucks(self, filter_params: dict = None, skip: int = 0, limit: int = 100):
        cursor = self.collection.find(filter_params or {}).skip(skip).limit(limit)
        return [TruckResponseSchema(**truck) async for truck in cursor]

# Инициализация
db = MongoDB()
truck_crud = TruckCRUD(db.vehicles)