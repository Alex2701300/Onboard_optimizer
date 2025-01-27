from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.models.trailer.schemas import TrailerCreateSchema, TrailerResponseSchema
from app.models.trailer.crud import trailer_crud

router = APIRouter(prefix="/trailers", tags=["trailers"])

@router.post("/", response_model=TrailerResponseSchema)
async def create_trailer(trailer_data: TrailerCreateSchema):
    """
    Создать трейлер.
    """
    created = await trailer_crud.create_trailer(trailer_data)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create Trailer")
    return created

@router.get("/", response_model=List[TrailerResponseSchema])
async def list_trailers():
    """
    Список всех трейлеров.
    """
    return await trailer_crud.list_trailers()

@router.get("/{trailer_id}", response_model=TrailerResponseSchema)
async def get_trailer(trailer_id: str):
    """
    Получить трейлер по ID.
    """
    trailer = await trailer_crud.get_trailer(trailer_id)
    if not trailer:
        raise HTTPException(status_code=404, detail="Trailer not found")
    return trailer

@router.put("/{trailer_id}", response_model=TrailerResponseSchema)
async def update_trailer(trailer_id: str, updates: Dict[str, Any]):
    """
    Обновить трейлер.
    """
    updated = await trailer_crud.update_trailer(trailer_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Trailer not found or not updated")
    return updated

@router.delete("/{trailer_id}")
async def delete_trailer(trailer_id: str):
    """
    Удалить трейлер.
    """
    deleted = await trailer_crud.delete_trailer(trailer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Trailer not found")
    return {"message": "Trailer deleted successfully"}