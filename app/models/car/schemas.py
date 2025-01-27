from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models.enums import CarBodyType, CarStatus, DataSource
from pymongo.objectid import ObjectId

class CarDimensions(BaseModel):
    length: Decimal
    width: Decimal
    height: Decimal
    curb_weight: Decimal
    wheelbase: Optional[Decimal] = None
    hood_height: Optional[Decimal] = None

class CarModification(BaseModel):
    type: str
    description: str
    height_change: Optional[Decimal] = None
    weight_change: Optional[Decimal] = None

class CarLotData(BaseModel):
    lot_number: str
    buyer_number: Optional[str] = None
    gate_number: Optional[str] = None
    lot_location: Optional[str] = None
    order_number: Optional[str] = None

class CarResponseSchema(BaseModel):
    _id: ObjectId
    year: int
    make: str
    model: str
    body_type: CarBodyType
    dimensions: CarDimensions
    status: CarStatus = CarStatus.RUN_AND_DRIVE
    is_modified: bool = False
    source: DataSource = DataSource.MANUAL
    lot_data: Optional[CarLotData] = None
    modifications: Optional[List[CarModification]] = None
    created_at: datetime
    updated_at: datetime
    last_modified_by: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }

class CarCreateSchema(BaseModel):
    year: int
    make: str
    model: str
    body_type: CarBodyType
    dimensions: CarDimensions
    status: Optional[CarStatus] = CarStatus.RUN_AND_DRIVE
    lot_data: Optional[CarLotData] = None
    modifications: Optional[List[CarModification]] = None