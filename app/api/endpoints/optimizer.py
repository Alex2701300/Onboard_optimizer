from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional

from app.services.optimizer import LoadingOptimizer
from app.services.height_calculator import HeightCalculationService
from app.models.enums import VehicleCategory
from app.models.truck.crud import truck_crud
from app.models.car.crud import car_crud

# Создаем экземпляр оптимизатора
optimizer = LoadingOptimizer()

# Определяем роутер для API оптимизатора
router = APIRouter(prefix="/optimizer", tags=["optimizer"])

@router.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса оптимизации загрузки.
    """
    return await optimizer.health_check()

@router.post("/optimize/{truck_id}")
async def optimize_loading(
    truck_id: str, 
    car_ids: List[str],
    constraints: Optional[Dict[str, Any]] = None
):
    """
    Оптимизирует загрузку автомобилей на грузовик.

    - **truck_id**: ID грузовика
    - **car_ids**: Список ID автомобилей для загрузки
    - **constraints**: Дополнительные ограничения (опционально)
    """
    # Проверяем существование грузовика
    truck = await truck_crud.get_truck(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail=f"Truck with ID {truck_id} not found")

    # Проверяем существование всех автомобилей
    cars = []
    for car_id in car_ids:
        car = await car_crud.get_car(car_id)
        if not car:
            raise HTTPException(
                status_code=404, 
                detail=f"Car with ID {car_id} not found"
            )
        cars.append(car)

    # Вызываем метод оптимизации загрузки
    try:
        result = await optimizer.optimize_loading(truck, cars, constraints)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{truck_id}/calculate-height")
async def calculate_effective_height(
    truck_id: str, 
    vehicle_category: VehicleCategory
):
    """
    Рассчитывает эффективную высоту краёв платформ для заданной категории ТС.
    Для электромобилей (ELECTRIC) нет снижения, для pickup/SUV - 4 дюйма, 
    для стандартных - 2 дюйма (если цепи is_used=True).

    - **truck_id**: ID грузовика
    - **vehicle_category**: Категория транспортного средства
    """
    truck = await truck_crud.get_truck(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail=f"Truck with ID {truck_id} not found")

    # Применяем расчет высот с учетом цепей для всех платформ
    adjusted_results = []

    # Обрабатываем верхнюю и нижнюю палубы
    for deck_name in ["upper_deck", "lower_deck"]:
        deck_data = getattr(truck, deck_name, None)
        if deck_data and deck_data.platforms:
            for platform in deck_data.platforms:
                # Преобразуем платформу в словарь
                platform_dict = platform.dict() if hasattr(platform, "dict") else platform

                # Вызываем сервис расчета высот
                adjusted = await HeightCalculationService.calculate_adjusted_heights(
                    platform_data=platform_dict,
                    vehicle_category=vehicle_category
                )
                adjusted_results.append(adjusted)

    return {"adjusted_heights": adjusted_results}

@router.post("/{truck_id}/validate-configuration")
async def validate_configuration(
    truck_id: str,
    configuration: Dict[str, Any]
):
    """
    Проверяет конфигурацию загрузки на соответствие ограничениям.

    - **truck_id**: ID грузовика
    - **configuration**: Конфигурация загрузки для проверки
    """
    truck = await truck_crud.get_truck(truck_id)
    if not truck:
        raise HTTPException(status_code=404, detail=f"Truck with ID {truck_id} not found")

    try:
        result = await optimizer.validate_configuration(truck, configuration)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/save-configuration")
async def save_loading_configuration(configuration: Dict[str, Any]):
    """
    Сохраняет оптимизированную конфигурацию загрузки.

    - **configuration**: Конфигурация загрузки для сохранения
    """
    try:
        config_id = await optimizer.save_configuration(configuration)
        return {"config_id": config_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))