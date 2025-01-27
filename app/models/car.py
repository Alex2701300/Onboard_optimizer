        from enum import Enum
        from typing import Optional, List, Dict
        from datetime import datetime
        from decimal import Decimal
        from dataclasses import dataclass

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

        @dataclass
        class Dimensions:
            """
            Изменили порядок полей: теперь поля без дефолта (length, width, height, curb_weight)
            идут *раньше* тех, у кого есть значение по умолчанию (wheelbase, hood_height).
            """
            length: Decimal
            width: Decimal
            height: Decimal
            curb_weight: Decimal
            wheelbase: Optional[Decimal] = None
            hood_height: Optional[Decimal] = None

            def __post_init__(self):
                if self.length <= self.width:
                    raise ValueError('Length must be greater than width')

        @dataclass
        class Modification:
            type: str
            description: str
            height_change: Optional[Decimal] = None
            weight_change: Optional[Decimal] = None

        @dataclass
        class LotData:
            lot_number: str
            buyer_number: Optional[str] = None
            gate_number: Optional[str] = None
            lot_location: Optional[str] = None
            order_number: Optional[str] = None

        @dataclass
        class VanSpecification:
            roof_type: RoofType
            van_type: VanType

        @dataclass
        class Car:
            year: int
            make: str
            model: str
            body_type: BodyType
            dimensions: Dimensions

            van_specification: Optional[VanSpecification] = None
            status: CarStatus = CarStatus.RUN_AND_DRIVE
            is_modified: bool = False
            source: DataSource = DataSource.MANUAL
            lot_data: Optional[LotData] = None
            modifications: Optional[List[Modification]] = None  #Added modifications field

            id: Optional[str] = None  #Added id field
            created_at: datetime = None  #Added created_at field
            updated_at: datetime = None  #Added updated_at field
            last_modified_by: Optional[str] = None  #Added last_modified_by field
            original_api_data: Optional[Dict] = None  #Added original_api_data field

            def __post_init__(self):
                if self.body_type == BodyType.VAN and not self.van_specification:
                    raise ValueError("Van specification is required for van body type")
                if self.created_at is None:
                    self.created_at = datetime.utcnow()
                if self.updated_at is None:
                    self.updated_at = datetime.utcnow()

            def get_total_dimensions(self) -> Dimensions:
                """Получить итоговые размеры с учетом модификаций."""
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
                    curb_weight=self.dimensions.curb_weight + weight_change,
                    wheelbase=self.dimensions.wheelbase,
                    hood_height=self.dimensions.hood_height
                )

            def update_from_api_data(self, api_data: Dict):
                """Обновление данных из API с сохранением оригинальных данных."""
                self.original_api_data = api_data
                self.source = DataSource.API
                # Здесь будет логика обновления полей из API
                self.updated_at = datetime.utcnow()