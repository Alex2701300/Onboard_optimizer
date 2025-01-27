# app/api/endpoints/cars.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.models.car.schemas import CarCreateSchema, CarResponseSchema
from app.models.car.crud import car_crud

# Сохраняем prefix="/cars"
router = APIRouter(prefix="/cars", tags=["cars"])

@router.post("/", response_model=CarResponseSchema)
async def create_car(car_data: CarCreateSchema):
    created = await car_crud.create_car(car_data)
    if not created:
        raise HTTPException(status_code=500, detail="Failed to create Car")
    return created

@router.get("/", response_model=List[CarResponseSchema])
async def list_cars():
    return await car_crud.list_cars()

@router.get("/{car_id}", response_model=CarResponseSchema)
async def get_car(car_id: str):
    car = await car_crud.get_car(car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car

@router.put("/{car_id}", response_model=CarResponseSchema)
async def update_car(car_id: str, updates: Dict[str, Any]):
    updated = await car_crud.update_car(car_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Car not found or not updated")
    return updated

@router.delete("/{car_id}")
async def delete_car(car_id: str):
    deleted = await car_crud.delete_car(car_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Car not found")
    return {"message": "Car deleted successfully"}