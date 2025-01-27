from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.db.mongodb import db  # Синглтон MongoDB (db.vehicles и т.д.)


################################################################################
# Вспомогательные перечисления/описания:
################################################################################

# Допустимые типы ТС
VEHICLE_TYPES = ("car", "truck", "trailer")

################################################################################
# Схемы (упрощённые) для Car / Trailer
################################################################################

class CarCreateSchema(BaseModel):
    """
    Минимальные поля для создания Car
    (все длины в INCHES, высоты — если есть — в FEET, но тут высоты нет)
    """
    vin: str = Field(..., min_length=3)
    make: str
    model: str
    year: int = Field(..., ge=1900)
    length_in: float = Field(..., gt=0, description="Length of the car in inches")
    width_in: float = Field(..., gt=0, description="Width in inches")
    height_ft: float = Field(..., gt=0, description="Height in feet")
    wheelbase_in: float = Field(..., gt=0, description="Wheelbase in inches")

class TrailerCreateSchema(BaseModel):
    """
    Упрощённая схема для Trailer
    """
    nickname: str
    year: int = Field(..., ge=1900)
    capacity_in: float = Field(..., description="Trailer capacity in inches? (условно)")
    # Любые другие поля...

################################################################################
# Расширенная схема для Truck (палубы, платформы, края, цепи)
################################################################################

class ChainConfiguration(BaseModel):
    is_used: bool = False
    # Снижение высоты зависит от категорий (pickup => -4", standard => -2", electric => 0"), 
    # но это логика; тут можно и поле vehicle_categories, если нужно.

class PlatformEdge(BaseModel):
    position: str = Field(..., pattern="^[AB]$")
    type: str = Field(..., description="static/mobile и т.п.")
    height_ft: float = Field(..., gt=0, description="Edge height in feet (!!!)")
    # load_overhang, deeping, etc. - опускаем для примера
    chains: ChainConfiguration = ChainConfiguration()

class Platform(BaseModel):
    id: str
    deck_type: str  # "upper_deck" / "lower_deck"
    position: int
    default_length_in: float = Field(..., gt=0, description="Length in inches")
    edge_a: PlatformEdge
    edge_b: PlatformEdge

class Deck(BaseModel):
    type: str  # "upper_deck" / "lower_deck"
    platforms: List[Platform] = []
    # joints, etc., если нужно

class TruckCreateSchema(BaseModel):
    nickname: str
    model: str
    year: int = Field(..., ge=1900)
    truck_type: str = Field(..., description="semi, stinger_head, etc.")
    coupling_type: str = Field(..., description="none, 5th_wheel, gooseneck...")
    gvwr_lbs: float = Field(..., gt=0, description="GVWR in lbs")
    loading_spots: int = 0
    deck_count: int = 1

    # Полное описание палуб:
    upper_deck: Optional[Deck] = None
    lower_deck: Optional[Deck] = None

################################################################################
# Общая модель "VehicleCreate" - в зависимости от "type" разворачиваем поля
################################################################################

class VehicleCreate(BaseModel):
    type: str = Field(..., description="car/truck/trailer")

    # Car fields
    vin: Optional[str] = None
    make: Optional[str] = None
    car_model: Optional[str] = None
    year: Optional[int] = None
    length_in: Optional[float] = None
    width_in: Optional[float] = None
    height_ft: Optional[float] = None
    wheelbase_in: Optional[float] = None

    # Trailer fields
    trailer_nickname: Optional[str] = None
    trailer_year: Optional[int] = None
    capacity_in: Optional[float] = None

    # Truck fields
    nickname: Optional[str] = None
    truck_model: Optional[str] = None
    truck_year: Optional[int] = None
    truck_type: Optional[str] = None
    coupling_type: Optional[str] = None
    gvwr_lbs: Optional[float] = None
    loading_spots: Optional[int] = None
    deck_count: Optional[int] = None
    upper_deck: Optional[Deck] = None
    lower_deck: Optional[Deck] = None

################################################################################
# Ответ при создании
################################################################################

class VehicleResponse(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]  # Сырые данные
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

################################################################################
# Роутер
################################################################################

router = APIRouter()

@router.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles():
    """
    Получить список всех ТС (car/truck/trailer)
    """
    docs = await db.list_vehicles()
    responses = []
    for d in docs:
        responses.append(VehicleResponse(
            id=str(d["_id"]),
            type=d.get("type", "unknown"),
            data=d,
            created_at=d["created_at"],
            updated_at=d["updated_at"]
        ))
    return responses

@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: str):
    """
    Получить одно ТС по ID
    """
    doc = await db.get_vehicle(vehicle_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return VehicleResponse(
        id=str(doc["_id"]),
        type=doc["type"],
        data=doc,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"]
    )

@router.post("/vehicles", response_model=VehicleResponse)
async def create_vehicle(payload: VehicleCreate):
    """
    Универсальный эндпоинт для создания Car/Truck/Trailer
    """
    if payload.type not in VEHICLE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid 'type' of vehicle")

    doc = payload.dict(exclude_unset=True)
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()

    inserted_id = await db.create_vehicle(doc)
    new_doc = await db.get_vehicle(inserted_id)
    return VehicleResponse(
        id=str(new_doc["_id"]),
        type=new_doc["type"],
        data=new_doc,
        created_at=new_doc["created_at"],
        updated_at=new_doc["updated_at"]
    )

@router.put("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(vehicle_id: str, updates: Dict[str, Any]):
    """
    Обновить поля в документе (car/truck/trailer)
    """
    success = await db.update_vehicle(vehicle_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Vehicle not found or not updated")

    new_doc = await db.get_vehicle(vehicle_id)
    return VehicleResponse(
        id=str(new_doc["_id"]),
        type=new_doc["type"],
        data=new_doc,
        created_at=new_doc["created_at"],
        updated_at=new_doc["updated_at"]
    )

@router.delete("/vehicles/{vehicle_id}")
async def delete_vehicle(vehicle_id: str):
    """
    Удалить ТС
    """
    deleted = await db.delete_vehicle(vehicle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"message": "Vehicle deleted"}