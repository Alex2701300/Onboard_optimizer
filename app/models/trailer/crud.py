# app/models/trailer/crud.py

import uuid
from datetime import datetime
from typing import List, Optional

from app.db.mongodb import db
from app.models.trailer.schemas import TrailerCreateSchema, TrailerResponseSchema

class TrailerCRUD:
    """
    Ленивая логика для trailers.
    """

    async def create_trailer(self, data: TrailerCreateSchema) -> Optional[TrailerResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB 'vehicles' is None.")

        doc = data.dict()
        doc["_id"] = str(uuid.uuid4())
        doc["type"] = "trailer"
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()

        await coll.insert_one(doc)
        new_doc = await coll.find_one({"_id": doc["_id"]})
        if new_doc:
            return TrailerResponseSchema(**new_doc)
        return None

    async def list_trailers(self) -> List[TrailerResponseSchema]:
        coll = db.vehicles
        if coll is None:
            raise RuntimeError("MongoDB 'vehicles' is None.")

        cursor = coll.find({"type": "trailer"})
        docs = await cursor.to_list(None)
        return [TrailerResponseSchema(**d) for d in docs]

    # Если нужны get/update/delete — аналогично
    # async def get_trailer(...)
    # async def update_trailer(...)
    # async def delete_trailer(...)

trailer_crud = TrailerCRUD()