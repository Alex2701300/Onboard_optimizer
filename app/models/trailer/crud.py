# app/models/trailer/crud.py

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.mongodb import db  # наш MongoDB singleton
from app.models.trailer.schemas import TrailerCreateSchema, TrailerResponseSchema

class TrailerCRUD:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def create_trailer(self, trailer_data: TrailerCreateSchema) -> Optional[TrailerResponseSchema]:
        """
        Создать новый трейлер, храним _id как строку (UUID), type="trailer".
        """
        trailer_dict = trailer_data.dict()
        trailer_id = str(uuid.uuid4())
        trailer_dict["_id"] = trailer_id
        trailer_dict["type"] = "trailer"

        trailer_dict["created_at"] = datetime.utcnow()
        trailer_dict["updated_at"] = datetime.utcnow()

        try:
            await self.collection.insert_one(trailer_dict)
            return await self.get_trailer(trailer_id)
        except Exception:
            return None

    async def get_trailer(self, trailer_id: str) -> Optional[TrailerResponseSchema]:
        doc = await self.collection.find_one({"_id": trailer_id, "type": "trailer"})
        if not doc:
            return None
        return TrailerResponseSchema(**doc)

    async def update_trailer(self, trailer_id: str, update_data: Dict[str, Any]) -> Optional[TrailerResponseSchema]:
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": trailer_id, "type": "trailer"},
            {"$set": update_data}
        )
        if result.modified_count < 1:
            return None
        return await self.get_trailer(trailer_id)

    async def delete_trailer(self, trailer_id: str) -> bool:
        result = await self.collection.delete_one({"_id": trailer_id, "type": "trailer"})
        return (result.deleted_count > 0)

    async def list_trailers(self) -> List[TrailerResponseSchema]:
        cursor = self.collection.find({"type": "trailer"})
        docs = await cursor.to_list(length=None)
        return [TrailerResponseSchema(**doc) for doc in docs]

# Инициализация CRUD
trailer_crud = TrailerCRUD(db.vehicles)