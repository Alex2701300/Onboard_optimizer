# app/models/truck/schemas.py

from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator

# Импорт из enums:
from app.models.enums import (
    TruckType,
    CouplingType,
    DeckType,
    EdgeType,
    JointType,
    SlideType,
    VehicleCategory
)


###############################################################################
#          1. КОНФИГУРАЦИЯ ЦЕПЕЙ (ChainConfiguration) + УЧЁТ ВЫСОТ
###############################################################################

class ChainConfiguration(BaseModel):
    """
    Конфигурация цепей крепления для края платформы.
    Если is_used=True — это значит, цепи включены. Optionally можно хранить
    список VehicleCategory, для которых даёт эффект.
    """
    is_used: bool = False

    # Если хотите дополнить логикой, например:
    # vehicle_categories: List[VehicleCategory] = []
    # тогда можно расширить.

class PlatformHeightAdjustment(BaseModel):
    """
    Логика вычисления итоговой высоты при использовании цепей 
    в зависимости от категории (VehicleCategory).
    """

    @classmethod
    def calculate_effective_height(
        cls,
        base_height: float,
        chains_config: ChainConfiguration,
        vehicle_category: VehicleCategory
    ) -> float:
        """
        Пример:
        - если is_used=False -> возвращаем base_height без изменения
        - если vehicle_category=ELECTRIC -> тоже без снижения
        - если STANDARD -> уменьшаем на 2
        - если PICKUP/FULL_SIZE_SUV -> уменьшаем на 4
        """
        if not chains_config.is_used:
            return base_height

        if vehicle_category == VehicleCategory.ELECTRIC:
            return base_height

        # По умолчанию -2 (STANDARD)
        reduction = 2.0

        # Если pickup / full_size_suv -> -4:
        if vehicle_category in [VehicleCategory.PICKUP, VehicleCategory.FULL_SIZE_SUV]:
            reduction = 4.0

        return base_height - reduction


###############################################################################
#          2. ОПИСАНИЕ КРАЯ ПЛАТФОРМЫ (PlatformEdgeSchema)
###############################################################################

class PlatformEdgeSchema(BaseModel):
    position: str = Field(..., regex="^[AB]$")
    type: EdgeType  # EdgeType.MOBILE / EdgeType.STATIC

    height: Optional[float] = None      # Для статичного края
    min_height: Optional[float] = None  # Для мобильного
    max_height: Optional[float] = None

    is_open: bool = False
    load_overhang: Optional[float] = Field(None, ge=0, le=48)
    deeping: Optional[float] = Field(None, ge=0, le=4)  # Углубление под колёса (до 4 дюймов)

    chains: ChainConfiguration = ChainConfiguration()

    @validator('height')
    def validate_static_height(cls, v, values):
        """
        Если край статичен (type=STATIC), у него должна быть height.
        """
        if values.get('type') == EdgeType.STATIC and v is None:
            raise ValueError("Static edge requires 'height'.")
        return v

    @validator('min_height', 'max_height')
    def validate_mobile_heights(cls, v, values):
        """
        Если край мобильный (type=MOBILE), нужны min_height и max_height.
        """
        if values.get('type') == EdgeType.MOBILE:
            # Можно проверить, что min_height < max_height
            # Но нужно аккуратно. 
            pass
        return v


###############################################################################
#          3. РАЗДВИЖЕНИЕ ПЛАТФОРМЫ (PlatformSlideSchema)
###############################################################################

class PlatformSlideSchema(BaseModel):
    type: SlideType  # SlideType.PLATFORM / A_EDGE / B_EDGE / NONE
    min_length: float
    max_length: float
    min_distance: float
    max_distance: float

    @validator('max_length')
    def validate_length_range(cls, v, values):
        if 'min_length' in values and v < values['min_length']:
            raise ValueError("max_length must be >= min_length")
        return v


###############################################################################
#          4. ПЛАТФОРМА (PlatformSchema)
###############################################################################

class PlatformSchema(BaseModel):
    id: str  # уникальный идентификатор платформы (строка)
    deck_type: DeckType  # upper_deck / lower_deck
    position: int        # Номер платформы на палубе
    default_length: float

    edge_a: PlatformEdgeSchema
    edge_b: PlatformEdgeSchema
    slide: Optional[PlatformSlideSchema] = None


###############################################################################
#          5. СОЕДИНЕНИЕ (JointSchema)
###############################################################################

class JointSchema(BaseModel):
    type: JointType
    platform_a_id: str
    platform_b_id: str
    edge_a: str   # "A" или "B"
    edge_b: str   # "A" или "B"

    minimum_loading_distance: Optional[float] = None
    max_overlap: Optional[float] = None
    static_height: Optional[float] = None


###############################################################################
#          6. ПАЛУБА (DeckSchema)
###############################################################################

class DeckSchema(BaseModel):
    type: DeckType  # upper_deck / lower_deck
    platforms: List[PlatformSchema] = []
    joints: List[JointSchema] = []
    total_length: float = 0

    # Пример валидации — 
    # если хотите проверить, что позиции platform'ов идут 1..N без пропусков:
    # @validator('platforms')
    # def validate_platform_positions(cls, v):
    #     ...
    #     return v


###############################################################################
#          7. ВЕРТИКАЛЬНЫЕ СВЯЗИ (VerticalConnectionSchema)
###############################################################################

class VerticalConnectionSchema(BaseModel):
    upper_platform_id: str
    lower_platform_id: str
    clearance_profile: Dict[str, float] = {}
    min_clearance: float = 6


###############################################################################
#          8. TruckCreateSchema
###############################################################################

class TruckCreateSchema(BaseModel):
    nickname: str
    model: str
    year: int
    truck_type: TruckType        # semi, stinger_head, ...
    coupling_type: CouplingType  # none, 5th_wheel, ...
    gvwr: float
    loading_spots: int = 0
    deck_count: int = 1

    upper_deck:  Optional[DeckSchema] = None
    lower_deck:  Optional[DeckSchema] = None
    vertical_connections: Optional[List[VerticalConnectionSchema]] = None


###############################################################################
#          9. TruckResponseSchema
###############################################################################

class TruckResponseSchema(BaseModel):
    id: str = Field(..., alias="_id")  # Для чтения из Mongo (_id -> id)

    nickname: str
    model: str
    year: int
    truck_type: str
    coupling_type: str
    gvwr: float
    loading_spots: int
    deck_count: int

    upper_deck:  Optional[DeckSchema] = None
    lower_deck:  Optional[DeckSchema] = None
    vertical_connections: Optional[List[VerticalConnectionSchema]] = None

    # Дополнительные поля
    type: str
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    ai_loader_ready: bool

    class Config:
        allow_population_by_field_name = True