# app/models/car/schemas.py

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

##############################################################################
# CarBaseSchema
##############################################################################

class CarBaseSchema(BaseModel):
    vin: str = Field(..., min_length=3, description="VIN автомобиля")
    make: str = Field(..., min_length=2, description="Производитель (марка)")
    model: str = Field(..., min_length=1, description="Модель")
    year: int = Field(..., ge=1900, le=9999)
    length_in: float = Field(..., gt=0, description="Длина (дюймы)")
    width_in: float = Field(..., gt=0, description="Ширина (дюймы)")
    height_ft: float = Field(..., gt=0, description="Высота (футы)")
    wheelbase_in: float = Field(..., gt=0, description="Колёсная база (дюймы)")

##############################################################################
# Создание (CarCreateSchema)
##############################################################################

class CarCreateSchema(CarBaseSchema):
    """
    Поля, которые нужны для создания нового автомобиля.
    Можно добавить что-то ещё при желании.
    """
    pass

##############################################################################
# Ответ (CarResponseSchema)
##############################################################################

class CarResponseSchema(CarBaseSchema):
    """
    Расширяем базовый набор полей, добавляя служебные.
    """
    id: str
    created_at: datetime
    updated_at: datetime

    # В Pydantic 2.x вместо orm_mode
    class Config:
        from_attributes = True