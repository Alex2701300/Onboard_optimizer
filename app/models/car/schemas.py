# app/models/car/schemas.py

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

#
# Схема для создания автомобиля (POST /api/cars).
#
class CarCreateSchema(BaseModel):
    vin: str
    make: str
    model: str
    year: int
    length_in: Optional[float] = None
    width_in: Optional[float] = None
    height_ft: Optional[float] = None
    wheelbase_in: Optional[float] = None


#
# Схема для ответа (GET /api/cars, GET /api/cars/{car_id} и т.д.)
# Поля, которые могут отсутствовать в базе, объявлены Optional.
# Если _id — ObjectId, Pydantic сконвертирует в str благодаря alias="_id".
#
class CarResponseSchema(BaseModel):
    # MongoDB _id => id:str
    id: str = Field(..., alias="_id")

    vin: str
    make: str
    model: str
    year: int

    length_in: Optional[float] = None
    width_in: Optional[float] = None
    height_ft: Optional[float] = None
    wheelbase_in: Optional[float] = None

    # Если в документе может не быть 'type' — делаем Optional
    type: Optional[str] = None

    # Если в документе могут отсутствовать created_at/updated_at
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        # Разрешаем Pydantic брать поля по alias, чтобы _id -> id
        allow_population_by_field_name = True