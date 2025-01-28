import uuid
from datetime import datetime
from typing import List, Optional

from app.db.mongodb import db
from app.models.trailer.schemas import TrailerCreateSchema, TrailerResponseSchema

class TrailerCRUD:
    """
    Логика для trailers, аналогичная cars (через uuid4).
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

        docs = await coll.find({"type": "trailer"}).to_list(None)
        if not docs:
            return []

        results = []
        for d in docs:
            d["id"] = str(d["_id"])
            results.append(TrailerResponseSchema(**d))
        return results

    # При желании, get_trailer, update_trailer, delete_trailer — делайте аналогично

trailer_crud = TrailerCRUD()