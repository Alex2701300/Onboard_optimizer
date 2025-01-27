# app/api/endpoints/trucks.py

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any

from app.models.truck.schemas import (
    TruckCreateSchema,
    TruckResponseSchema,
    VehicleCategory
)
from app.models.truck.crud import truck_crud
from app.services.height_calculator import HeightCalculationService

router = APIRouter(prefix="/trucks", tags=["trucks"])

@router.get("/", response_model=List[TruckResponseSchema])
async def list_trucks():
    """
    Список всех грузовиков в базе.
    """
    trucks = await truck_crud.list_trucks()  # Предполагается, что есть метод list_trucks()
    return trucks

@router.post("/", response_model=TruckResponseSchema)
async def create_truck(truck_data: TruckCreateSchema):
    """
    Создание нового грузовика в базе.
    """
    try:
        created = await truck_crud.create_truck(truck_data)
        if not created:
            raise HTTPException(status_code=500, detail="Failed to create Truck")
        return created
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{truck_id}", response_model=TruckResponseSchema)
async def get_truck(truck_id: str):
    """
    Получение одного грузовика по ID.
    """
    truck = await truck_crud.get_truck(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@router.put("/{truck_id}", response_model=TruckResponseSchema)
async def update_truck(truck_id: str, update_data: Dict[str, Any]):
    """
    Обновление данных грузовика (например, nickname, year и т.д.)
    """
    try:
        updated = await truck_crud.update_truck_configuration(truck_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Truck not found or not updated")
        return updated
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{truck_id}")
async def delete_truck(truck_id: str):
    """
    Удаление грузовика по ID.
    """
    deleted = await truck_crud.delete_truck(truck_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Truck not found")
    return {"message": "Truck deleted successfully"}

@router.post("/{truck_id}/calculate-height")
async def calculate_effective_height(truck_id: str, vehicle_category: VehicleCategory):
    """
    Рассчитывает эффективную высоту краёв платформ для заданной категории ТС.
    Для электромобилей (ELECTRIC) нет снижения, для pickup/SUV - 4 дюйма, 
    для стандартных - 2 дюйма (если цепи is_used=True).
    """
    truck = await truck_crud.get_truck(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")

    # Предположим, что truck содержит поля upper_deck, lower_deck и т.д.
    adjusted_results = []

    for deck_name in ["upper_deck", "lower_deck"]:
        deck_data = getattr(truck, deck_name, None)
        if deck_data and deck_data.platforms:
            # Перебираем все платформы
            for platform in deck_data.platforms:
                # Преобразуем в словарь, чтобы прокинуть в сервис
                platform_dict = platform.dict()
                adjusted = await HeightCalculationService.calculate_adjusted_heights(
                    platform_data=platform_dict,
                    vehicle_category=vehicle_category
                )
                adjusted_results.append(adjusted)

    return {"adjusted_heights": adjusted_results}