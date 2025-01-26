from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, validator
from decimal import Decimal

class BodyType(str, Enum):
    SEDAN = "sedan"
    SUV = "suv"
    HATCHBACK = "hatchback"
    FULL_SIZE_SUV = "full_size_suv"
    VAN = "van"
    PICKUP = "pickup"
    UTILITY_TRUCK = "utility_truck"

class CarStatus(str, Enum):
    RUN_AND_DRIVE = "run&drive"
    INOPERABLE_ROLLING = "inoperable-rolling"
    INOPERABLE_STUCK = "inoperable-stuck"
    NO_KEYS = "no_keys"

class RoofType(str, Enum):
    LOW_ROOF = "low_roof"
    MIDDLE_ROOF = "middle_roof"
    HIGH_ROOF = "high_roof"

class VanType(str, Enum):
    PASSENGER = "passenger_van"
    UTILITY = "utility_van"

class DataSource(str, Enum):
    MANUAL = "manual"
    API = "api"
    IMPORT = "import"

class Dimensions(BaseModel):
    """Размеры автомобиля"""
    length: Decimal = Field(..., description="Length in inches", gt=0)
    width: Decimal = Field(..., description="Width in inches", gt=0)
    height: Decimal = Field(..., description="Height in inches", gt=0)
    wheelbase: Optional[Decimal] = Field(None, description="Wheelbase in inches")
    hood_height: Optional[Decimal] = Field(None, description="Hood height in inches")
    curb_weight: Decimal = Field(..., description="Weight in pounds", gt=0)

    @validator('length')
    def length_must_be_greater_than_width(cls, v, values):
        if 'width' in values and v <= values['width']:
            raise ValueError('Length must be greater than width')
        return v

class Modification(BaseModel):
    """Модификации автомобиля"""
    type: str = Field(..., description="Type of modification")
    description: str = Field(..., min_length=50, description="Detailed description")
    height_change: Optional[Decimal] = Field(None, description="Change in height (inches)")
    weight_change: Optional[Decimal] = Field(None, description="Change in weight (pounds)")

class LotData(BaseModel):
    """Данные лота"""
    lot_number: str
    buyer_number: Optional[str] = None
    gate_number: Optional[str] = None
    lot_location: Optional[str] = None
    order_number: Optional[str] = None

class VanSpecification(BaseModel):
    """Спецификация для типа van"""
    roof_type: RoofType
    van_type: VanType

class Car(BaseModel):
    """Модель автомобиля для перевозки"""
    model_config = ConfigDict(populate_by_name=True)

    # Системные поля
    id: Optional[str] = Field(None, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    source: DataSource = Field(default=DataSource.MANUAL)
    last_modified_by: Optional[str] = None

    # Обязательные базовые поля
    year: int = Field(..., ge=1900, le=datetime.now().year + 1)
    make: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    body_type: BodyType
    status: CarStatus = Field(default=CarStatus.RUN_AND_DRIVE)
    dimensions: Dimensions

    # Опциональные поля
    vin: Optional[str] = None
    lot_data: Optional[LotData] = None
    van_specification: Optional[VanSpecification] = None
    original_api_data: Optional[Dict] = None

    # Модификации
    is_modified: bool = Field(default=False)
    modifications: Optional[List[Modification]] = None

    @validator('van_specification')
    def validate_van_spec(cls, v, values):
        if 'body_type' in values and values['body_type'] == BodyType.VAN and v is None:
            raise ValueError('Van specification is required for van body type')
        if 'body_type' in values and values['body_type'] != BodyType.VAN and v is not None:
            raise ValueError('Van specification is only allowed for van body type')
        return v

    def get_total_dimensions(self) -> Dimensions:
        """Получить итоговые размеры с учетом модификаций"""
        if not self.is_modified or not self.modifications:
            return self.dimensions

        height_change = sum(
            mod.height_change or Decimal('0')
            for mod in self.modifications
            if mod.height_change
        )

        weight_change = sum(
            mod.weight_change or Decimal('0')
            for mod in self.modifications
            if mod.weight_change
        )

        return Dimensions(
            length=self.dimensions.length,
            width=self.dimensions.width,
            height=self.dimensions.height + height_change,
            weight=self.dimensions.curb_weight + weight_change,
            wheelbase=self.dimensions.wheelbase,
            hood_height=self.dimensions.hood_height
        )

    def update_from_api_data(self, api_data: Dict):
        """Обновление данных из API с сохранением оригинальных данных"""
        self.original_api_data = api_data
        self.source = DataSource.API
        # Здесь будет логика обновления полей из API
        self.updated_at = datetime.utcnow()