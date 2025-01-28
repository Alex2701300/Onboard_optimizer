from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models.enums import CarBodyType, CarStatus, DataSource
from bson import ObjectId


class CarDimensions(BaseModel):
    # СТАРЫЙ вариант с вложенными габаритами.
    # Оставляем класс в коде, если он где-то ещё используется,
    # но в CarCreateSchema ниже уже НЕ используем напрямую.
    length: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    curb_weight: Optional[float] = None
    wheelbase: Optional[float] = None
    hood_height: Optional[float] = None


class CarModification(BaseModel):
    type: str
    description: str
    height_change: Optional[float] = None
    weight_change: Optional[float] = None


class CarLotData(BaseModel):
    lot_number: str
    buyer_number: Optional[str] = None
    gate_number: Optional[str] = None
    lot_location: Optional[str] = None
    order_number: Optional[str] = None


class CarResponseSchema(BaseModel):
    """
    Модель, описывающая структуру данных при выдаче (GET) информации о машине.
    Все потенциально отсутствующие поля сделаны Optional.
    """
    id: Optional[str] = None
    vin: Optional[str] = None
    year: Optional[int] = None
    make: Optional[str] = None
    model: Optional[str] = None

    # Вместо единого "dimensions" — отдельные поля (теперь float):
    length_in: Optional[float] = None
    width_in: Optional[float] = None
    height_ft: Optional[float] = None
    wheelbase_in: Optional[float] = None

    body_type: Optional[CarBodyType] = None
    status: CarStatus = CarStatus.RUN_AND_DRIVE
    is_modified: bool = False
    source: DataSource = DataSource.MANUAL
    lot_data: Optional[CarLotData] = None
    modifications: Optional[List[CarModification]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_modified_by: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }

    @classmethod
    def from_mongo(cls, data: dict):
        if not data:
            return None
        mongo_id = data.pop('_id', None)
        if mongo_id:
            data['id'] = str(mongo_id)
        return cls(**data)


class CarCreateSchema(BaseModel):
    """
    Модель, описывающая данные, необходимые для создания (POST) машины.
    Здесь поля вынесены отдельно, чтобы форма (где length_in, width_in, height_ft, wheelbase_in) 
    не выдавала 422.
    """
    vin: Optional[str] = None
    year: int
    make: str
    model: str

    # Раздельные поля габаритов (теперь float):
    length_in: float
    width_in: float
    height_ft: float
    wheelbase_in: float

    body_type: Optional[CarBodyType] = None
    status: Optional[CarStatus] = CarStatus.RUN_AND_DRIVE
    lot_data: Optional[CarLotData] = None
    modifications: Optional[List[CarModification]] = None