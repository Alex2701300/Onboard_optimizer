from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator

from app.models.enums import (
    TruckType,
    CouplingType,
    DeckType,
    EdgeType,
    JointType,
    SlideType,
    VehicleCategory
)

class ChainConfiguration(BaseModel):
    is_used: bool = False

class PlatformHeightAdjustment(BaseModel):
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

class PlatformEdgeSchema(BaseModel):
    position: str = Field(..., regex="^[AB]$")
    type: EdgeType
    height: Optional[float] = None
    min_height: Optional[float] = None
    max_height: Optional[float] = None
    is_open: bool = False
    load_overhang: Optional[float] = Field(None, ge=0, le=48)
    deeping: Optional[float] = Field(None, ge=0, le=4)
    chains: ChainConfiguration = ChainConfiguration()

    @validator('height')
    def validate_static_height(cls, v, values):
        if values.get('type') == EdgeType.STATIC and v is None:
            raise ValueError("Static edge requires 'height'.")
        return v

    @validator('min_height', 'max_height')
    def validate_mobile_heights(cls, v, values):
        if values.get('type') == EdgeType.MOBILE:
            pass
        return v

class PlatformSlideSchema(BaseModel):
    type: SlideType
    min_length: float
    max_length: float
    min_distance: float
    max_distance: float

    @validator('max_length')
    def validate_length_range(cls, v, values):
        if 'min_length' in values and v < values['min_length']:
            raise ValueError("max_length must be >= min_length")
        return v

class PlatformSchema(BaseModel):
    id: str
    deck_type: DeckType
    position: int
    default_length: float
    edge_a: PlatformEdgeSchema
    edge_b: PlatformEdgeSchema
    slide: Optional[PlatformSlideSchema] = None

class JointSchema(BaseModel):
    type: JointType
    platform_a_id: str
    platform_b_id: str
    edge_a: str
    edge_b: str
    minimum_loading_distance: Optional[float] = None
    max_overlap: Optional[float] = None
    static_height: Optional[float] = None

class DeckSchema(BaseModel):
    type: DeckType
    platforms: List[PlatformSchema] = []
    joints: List[JointSchema] = []
    total_length: float = 0

class VerticalConnectionSchema(BaseModel):
    upper_platform_id: str
    lower_platform_id: str
    clearance_profile: Dict[str, float] = {}
    min_clearance: float = 6

class TruckCreateSchema(BaseModel):
    vin: Optional[str] = None
    nickname: str
    model: str
    year: int
    truck_type: TruckType
    coupling_type: CouplingType
    gvwr: float
    loading_spots: int = 0
    deck_count: int = 1

    upper_deck:  Optional[DeckSchema] = None
    lower_deck:  Optional[DeckSchema] = None
    vertical_connections: Optional[List[VerticalConnectionSchema]] = None

class TruckResponseSchema(BaseModel):
    id: str = Field(..., alias="_id")
    vin: Optional[str] = None
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

    type: str
    created_at: datetime
    updated_at: datetime
    is_verified: bool
    ai_loader_ready: bool

    class Config:
        allow_population_by_field_name = True