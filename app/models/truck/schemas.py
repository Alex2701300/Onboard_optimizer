# app/models/truck/schemas.py

from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator

# Перечисления (например, в app/models/enums.py)
from app.models.enums import (
    TruckType, 
    CouplingType,
    DeckType,
    EdgeType,
    JointType,
    SlideType,
    VehicleCategory
)

##############################################################################
#                   Базовые и вспомогательные схемы
##############################################################################

class ChainConfiguration(BaseModel):
    """
    Конфигурация цепей крепления для края платформы.
    Если is_used=True, обязательно нужно указать vehicle_categories,
    для которых эти цепи применимы.
    """
    is_used: bool = Field(
        False,
        description="Используются ли цепи для данного края"
    )
    vehicle_categories: List[VehicleCategory] = Field(
        default_factory=list,
        description="Категории ТС, для которых применяются цепи"
    )

    @validator('vehicle_categories', always=True)
    def validate_categories(cls, categories, values):
        if values.get('is_used') and not categories:
            raise ValueError("Must specify vehicle categories when chains are used")
        return categories

class PlatformEdgeSchema(BaseModel):
    position: str = Field(
        ...,
        regex="^[AB]$",
        description="Позиция края на платформе: A или B"
    )
    type: EdgeType
    height: Optional[float] = Field(
        None,
        gt=0,
        description="Высота (для статичного края), в дюймах"
    )
    min_height: Optional[float] = Field(
        None,
        gt=0,
        description="Минимальная высота (для подвижного края), в дюймах"
    )
    max_height: Optional[float] = Field(
        None,
        gt=0,
        description="Максимальная высота (для подвижного края), в дюймах"
    )
    is_open: bool = False
    load_overhang: Optional[float] = Field(
        None,
        ge=0,
        le=48,
        description="Допустимый вылет груза (дюймы)"
    )
    deeping: Optional[float] = Field(
        None,
        ge=0,
        le=4,
        description="Глубина углубления под колеса, макс 4 дюйма"
    )
    chains: ChainConfiguration = Field(
        default_factory=ChainConfiguration,
        description="Конфигурация цепей крепления"
    )

    @validator('height', always=True)
    def validate_static_edge(cls, value, values):
        if values.get('type') == EdgeType.STATIC:
            if value is None:
                raise ValueError("Static edge requires a fixed 'height'.")
        return value

    @validator('min_height', 'max_height', always=True)
    def validate_mobile_edge(cls, value, values):
        if values.get('type') == EdgeType.MOBILE:
            min_h = values.get('min_height')
            max_h = values.get('max_height')
            if min_h is None or max_h is None or (max_h <= min_h):
                raise ValueError("Invalid mobile edge range (min_height < max_height).")
        return value

class PlatformSlideSchema(BaseModel):
    type: SlideType
    min_length: float = Field(..., gt=0, description="Мин. длина платформы (дюймы)")
    max_length: float = Field(..., gt=0, description="Макс. длина платформы (дюймы)")
    min_distance: float = Field(..., description="Мин. расстояние до соседней платформы (дюймы)")
    max_distance: float = Field(..., description="Макс. расстояние до соседней платформы (дюймы)")

    @validator('max_length')
    def validate_lengths(cls, v, values):
        if v < values['min_length']:
            raise ValueError("max_length must be greater than min_length")
        return v

class PlatformSchema(BaseModel):
    id: str = Field(
        ...,
        min_length=3,
        description="Уникальный идентификатор платформы (строка)"
    )
    deck_type: DeckType
    position: int = Field(
        ...,
        gt=0,
        description="Позиция платформы на палубе (1..N)"
    )
    default_length: float = Field(
        ...,
        gt=0,
        description="Базовая длина платформы (дюймы)"
    )
    edge_a: PlatformEdgeSchema
    edge_b: PlatformEdgeSchema
    slide: Optional[PlatformSlideSchema] = None

class JointSchema(BaseModel):
    type: JointType
    platform_a: str = Field(..., description="ID первой платформы")
    platform_b: str = Field(..., description="ID второй платформы")
    edge_a: str = Field(..., regex="^[AB]$")
    edge_b: str = Field(..., regex="^[AB]$")
    min_loading_distance: Optional[float] = Field(None, ge=0)
    max_overlap: Optional[float] = Field(None, ge=0)
    # static_height, etc. при желании

class DeckSchema(BaseModel):
    type: DeckType
    platforms: List[PlatformSchema] = Field(..., min_items=1)
    joints: List[JointSchema] = []

    @validator('platforms')
    def validate_platform_positions(cls, v):
        positions = [p.position for p in v]
        expected = list(range(1, len(v) + 1))
        if sorted(positions) != expected:
            raise ValueError("Platform positions must form a continuous sequence 1..N")
        return v

class VerticalConnectionSchema(BaseModel):
    upper_platform_id: str
    lower_platform_id: str
    clearance_profile: Dict[str, float] = Field(
        ...,
        example={"front": 72.0, "middle": 68.0, "rear": 72.0}
    )
    min_clearance: float = Field(..., gt=0)

##############################################################################
# Логика расчёта высоты с учётом цепей
##############################################################################

class PlatformHeightAdjustment(BaseModel):
    """
    Вспомогательный класс для расчёта итоговой высоты
    при использовании цепей в зависимости от категории ТС.
    """
    @classmethod
    def calculate_effective_height(
        cls,
        base_height: float,
        chains_config: ChainConfiguration,
        vehicle_category: VehicleCategory
    ) -> float:
        if not chains_config.is_used:
            return base_height
        if vehicle_category == VehicleCategory.ELECTRIC:
            return base_height
        reduction = 2.0
        if vehicle_category in [VehicleCategory.PICKUP, VehicleCategory.FULL_SIZE_SUV]:
            reduction = 4.0
        return base_height - reduction

##############################################################################
#                       Основная схема для Truck
##############################################################################

class TruckBaseSchema(BaseModel):
    nickname: str = Field(..., min_length=2, max_length=50)
    year: int = Field(..., ge=1900, le=9999)
    model: str = Field(..., min_length=2, max_length=50)
    truck_type: TruckType
    coupling_type: CouplingType
    gvwr: float = Field(..., gt=0, description="Полная масса (фунты)")

class TruckCreateSchema(TruckBaseSchema):
    loading_spots: int = Field(0, ge=0)
    deck_count: Optional[int] = Field(None, ge=1, le=2)
    upper_deck: Optional[DeckSchema] = None
    lower_deck: Optional[DeckSchema] = None
    vertical_connections: Optional[List[VerticalConnectionSchema]] = None
    # Опционально: словарь цепей
    chain_configurations: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Пример: {platform_id: [A,B]} – какие края используют цепи"
    )

class TruckResponseSchema(TruckBaseSchema):
    id: str
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    ai_loader_ready: bool

    class Config:
        # В Pydantic 2.x вместо orm_mode
        from_attributes = True