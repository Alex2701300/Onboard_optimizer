import pytest
from decimal import Decimal
from app.models.car import (
    Car, Dimensions, Modification, BodyType, 
    CarStatus, RoofType, VanType, DataSource
)

def test_create_basic_car():
    """Тест создания базового автомобиля"""
    dimensions = Dimensions(
        length=Decimal("180.0"),
        width=Decimal("72.0"),
        height=Decimal("58.0"),
        curb_weight=Decimal("3500.0")
    )

    car = Car(
        year=2020,
        make="Toyota",
        model="Camry",
        body_type=BodyType.SEDAN,
        dimensions=dimensions
    )

    assert car.year == 2020
    assert car.make == "Toyota"
    assert car.body_type == BodyType.SEDAN
    assert car.status == CarStatus.RUN_AND_DRIVE
    assert not car.is_modified
    assert car.source == DataSource.MANUAL

def test_create_van():
    """Тест создания van с обязательной спецификацией"""
    dimensions = Dimensions(
        length=Decimal("250.0"),
        width=Decimal("80.0"),
        height=Decimal("108.0"),
        curb_weight=Decimal("5500.0")
    )

    car = Car(
        year=2020,
        make="Mercedes",
        model="Sprinter",
        body_type=BodyType.VAN,
        dimensions=dimensions,
        van_specification={
            "roof_type": RoofType.HIGH_ROOF,
            "van_type": VanType.UTILITY
        }
    )

    assert car.van_specification.roof_type == RoofType.HIGH_ROOF
    assert car.van_specification.van_type == VanType.UTILITY

def test_van_validation():
    """Тест валидации спецификации van"""
    dimensions = Dimensions(
        length=Decimal("250.0"),
        width=Decimal("80.0"),
        height=Decimal("108.0"),
        curb_weight=Decimal("5500.0")
    )

    # Должно вызвать ошибку - van без спецификации
    with pytest.raises(ValueError):
        Car(
            year=2020,
            make="Mercedes",
            model="Sprinter",
            body_type=BodyType.VAN,
            dimensions=dimensions
        )

def test_dimensions_validation():
    """Тест валидации размеров"""
    # Должно вызвать ошибку - длина меньше ширины
    with pytest.raises(ValueError):
        Dimensions(
            length=Decimal("50.0"),
            width=Decimal("72.0"),
            height=Decimal("58.0"),
            curb_weight=Decimal("3500.0")
        )

def test_car_with_modifications():
    """Тест автомобиля с модификациями"""
    dimensions = Dimensions(
        length=Decimal("180.0"),
        width=Decimal("72.0"),
        height=Decimal("58.0"),
        curb_weight=Decimal("3500.0")
    )

    modification = Modification(
        type="lift_kit",
        description="3 inch suspension lift kit with heavy duty springs and extended shocks",
        height_change=Decimal("3.0"),
        weight_change=Decimal("100.0")
    )

    car = Car(
        year=2020,
        make="Toyota",
        model="4Runner",
        body_type=BodyType.SUV,
        dimensions=dimensions,
        is_modified=True,
        modifications=[modification]
    )

    total_dimensions = car.get_total_dimensions()
    assert total_dimensions.height == Decimal("61.0")  # 58 + 3
    assert total_dimensions.curb_weight == Decimal("3600.0")  # 3500 + 100