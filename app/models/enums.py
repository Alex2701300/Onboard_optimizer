# app/models/enums.py

from enum import Enum

class VehicleType(str, Enum):
    """Тип транспортного средства"""
    CAR = "car"
    TRUCK = "truck"
    TRAILER = "trailer"

class CarBodyType(str, Enum):
    """Тип кузова автомобиля"""
    SEDAN = "sedan"
    SUV = "suv"
    HATCHBACK = "hatchback"
    FULL_SIZE_SUV = "full_size_suv"
    VAN = "van"
    PICKUP = "pickup"
    UTILITY_TRUCK = "utility_truck"

class CarStatus(str, Enum):
    """Статус автомобиля"""
    RUN_AND_DRIVE = "run_and_drive"
    INOPERABLE_ROLLING = "inoperable_rolling"
    INOPERABLE_STUCK = "inoperable_stuck"
    NO_KEYS = "no_keys"

class TruckType(str, Enum):
    """Тип грузовика"""
    SEMI = "semi"
    STINGER_HEAD = "stinger_head"
    STINGER_FIVE = "stinger_five"
    SEMI_PLATFORM = "semi_platform"
    PICKUP = "pickup"
    TOWTRUCK = "towtruck"

class CouplingType(str, Enum):
    """Тип сцепки"""
    NONE = "none"
    FIFTH_WHEEL = "5th_wheel"
    GOOSENECK = "gooseneck"
    BUMPER_POOL = "bumper_pool"

class DeckType(str, Enum):
    """Тип палубы"""
    UPPER = "upper_deck"
    LOWER = "lower_deck"

class EdgeType(str, Enum):
    """Тип края платформы"""
    MOBILE = "mobile"
    STATIC = "static"

class JointType(str, Enum):
    """Тип соединения платформ"""
    STATIC = "static_joint"
    OPEN_FREE = "open_free_joint"
    ARTICULATED_SLIDING = "articulated_sliding_joint"
    SEMI_OPEN_FREE = "semi_open_free_joint"
    SEMI_FIX = "semi_fix_joint"
    TURNING = "turning_joint"

class SlideType(str, Enum):
    """Тип раздвижения"""
    NONE = "none"
    PLATFORM = "platform_slide"
    A_EDGE = "a_slide"
    B_EDGE = "b_slide"

class VanRoofType(str, Enum):
    """Тип крыши для van"""
    LOW_ROOF = "low_roof"
    MIDDLE_ROOF = "middle_roof"
    HIGH_ROOF = "high_roof"

class VanType(str, Enum):
    """Тип van"""
    PASSENGER = "passenger_van"
    UTILITY = "utility_van"

class DataSource(str, Enum):
    """Источник данных"""
    MANUAL = "manual"
    API = "api"
    IMPORT = "import"

# <-- NEW: добавлено перечисление для учета типов ТС при использовании цепей
class VehicleCategory(str, Enum):
    STANDARD = "standard"
    PICKUP = "pickup"
    FULL_SIZE_SUV = "full_size_suv"
    ELECTRIC = "electric"