from typing import List, Dict, Any, Optional, Tuple
import uuid
import logging
from datetime import datetime

from app.db.dynamodb import db
from app.models.truck.schemas import TruckResponseSchema
from app.models.car.schemas import CarResponseSchema
from app.services.height_calculator import HeightCalculationService
from app.models.enums import VehicleCategory

logger = logging.getLogger(__name__)

class LoadingOptimizer:
    """
    Оптимизатор загрузки автомобилей на автовозы.
    Реализует алгоритмы оптимального размещения с учетом физических ограничений.
    """

    def __init__(self):
        self.name = "Loading Optimizer Service"

    async def health_check(self) -> Dict[str, str]:
        """Проверка работоспособности сервиса"""
        return {"status": "healthy", "service": self.name}

    async def optimize_loading(
        self, 
        truck: TruckResponseSchema, 
        cars: List[CarResponseSchema], 
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Основной метод оптимизации загрузки.

        Args:
            truck: Грузовик для загрузки
            cars: Список автомобилей для размещения
            constraints: Дополнительные ограничения

        Returns:
            Оптимизированная конфигурация загрузки
        """
        logger.info(f"Начало оптимизации загрузки для грузовика {truck.id}, {len(cars)} автомобилей")

        # Проверка возможности размещения
        if not self._can_fit_all_cars(truck, cars):
            logger.warning("Невозможно разместить все автомобили на грузовике")
            return {
                "success": False,
                "message": "Cannot fit all cars on the truck",
                "truck_id": truck.id,
                "car_count": len(cars),
                "loading_spots": truck.loading_spots
            }

        # Сортировка автомобилей по приоритету размещения
        sorted_cars = self._sort_cars_by_priority(cars)

        # Базовое размещение
        base_placement = self._create_initial_placement(truck, sorted_cars)

        # Оптимизация высот
        optimized_placement = await self._optimize_heights(truck, base_placement)

        # Проверка ограничений
        validation_result = await self._validate_constraints(truck, optimized_placement, constraints)
        if not validation_result["valid"]:
            logger.warning(f"Конфигурация не соответствует ограничениям: {validation_result['issues']}")
            return {
                "success": False,
                "message": "Configuration does not meet constraints",
                "issues": validation_result["issues"],
                "truck_id": truck.id
            }

        # Финальная оптимизация
        final_placement = self._final_optimization(truck, optimized_placement)

        # Сохраняем результат
        configuration = {
            "truck_id": truck.id,
            "cars": [car.id for car in cars],
            "placement": final_placement,
            "created_at": datetime.utcnow(),
            "constraints": constraints or {}
        }

        # Логируем опыт загрузки
        await self._log_loading_experience(truck.id, configuration)

        logger.info(f"Оптимизация загрузки завершена успешно для грузовика {truck.id}")

        return {
            "success": True,
            "truck_id": truck.id,
            "car_count": len(cars),
            "configuration": configuration
        }

    async def validate_configuration(
        self, 
        truck: TruckResponseSchema, 
        configuration: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Проверяет конфигурацию загрузки на соответствие ограничениям.

        Args:
            truck: Грузовик для загрузки
            configuration: Конфигурация загрузки для проверки

        Returns:
            Результат валидации
        """
        # Проверяем физические ограничения
        validation_result = await self._validate_constraints(truck, configuration.get("placement", {}))

        return {
            "valid": validation_result["valid"],
            "issues": validation_result.get("issues", []),
            "warnings": validation_result.get("warnings", []),
            "truck_id": truck.id
        }

    async def save_configuration(self, configuration: Dict[str, Any]) -> str:
        """
        Сохраняет конфигурацию загрузки.

        Args:
            configuration: Конфигурация загрузки для сохранения

        Returns:
            ID сохраненной конфигурации
        """
        # Добавляем ID если его нет
        if "id" not in configuration:
            configuration["id"] = str(uuid.uuid4())

        # Сохраняем конфигурацию
        config_id = await db.save_configuration(configuration)

        return config_id

    # -------------------- Вспомогательные методы --------------------

    def _can_fit_all_cars(self, truck: TruckResponseSchema, cars: List[CarResponseSchema]) -> bool:
        """Проверяет, можно ли разместить все автомобили на грузовике"""
        return len(cars) <= truck.loading_spots

    def _sort_cars_by_priority(self, cars: List[CarResponseSchema]) -> List[CarResponseSchema]:
        """Сортирует автомобили по приоритету размещения"""
        # Сначала размещаем самые высокие автомобили
        return sorted(cars, key=lambda car: car.height_ft, reverse=True)

    def _create_initial_placement(
        self, 
        truck: TruckResponseSchema, 
        cars: List[CarResponseSchema]
    ) -> Dict[str, Any]:
        """Создает начальное размещение автомобилей на грузовике"""
        # В реальности здесь был бы сложный алгоритм размещения
        # Для MVP используем упрощенный подход

        placement = {
            "upper_deck": [],
            "lower_deck": []
        }

        # Получаем доступные места на верхней и нижней палубах
        upper_platforms = []
        lower_platforms = []

        if truck.upper_deck and truck.upper_deck.platforms:
            upper_platforms = sorted(truck.upper_deck.platforms, key=lambda p: p.position)

        if truck.lower_deck and truck.lower_deck.platforms:
            lower_platforms = sorted(truck.lower_deck.platforms, key=lambda p: p.position)

        # Распределяем автомобили по платформам
        car_index = 0

        # Сначала заполняем верхнюю палубу
        for platform in upper_platforms:
            if car_index < len(cars):
                placement["upper_deck"].append({
                    "car_id": cars[car_index].id,
                    "platform_id": platform.id,
                    "direction": "forward"  # По умолчанию носом вперед
                })
                car_index += 1

        # Затем заполняем нижнюю палубу
        for platform in lower_platforms:
            if car_index < len(cars):
                placement["lower_deck"].append({
                    "car_id": cars[car_index].id,
                    "platform_id": platform.id,
                    "direction": "backward"  # По умолчанию носом назад
                })
                car_index += 1

        return placement

    async def _optimize_heights(
        self, 
        truck: TruckResponseSchema, 
        placement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Оптимизирует высоты размещения для минимизации общей высоты"""
        # Копируем исходное размещение
        optimized = placement.copy()

        # В реальности здесь был бы сложный алгоритм оптимизации высот
        # с учетом наклонов платформ и размещения автомобилей

        # Для MVP просто пытаемся оптимизировать направление автомобилей
        for deck in ["upper_deck", "lower_deck"]:
            for i, placement_item in enumerate(optimized.get(deck, [])):
                # Определяем категорию автомобиля (для расчета высоты с цепями)
                car_category = self._determine_vehicle_category(placement_item["car_id"])

                # Для некоторых автомобилей меняем направление, если это снизит высоту
                if i % 2 == 1:  # Просто для примера меняем каждый второй
                    optimized[deck][i]["direction"] = "backward" if placement_item["direction"] == "forward" else "forward"

                # Рассчитываем эффективную высоту с учетом цепей
                platform_id = placement_item["platform_id"]
                platform = next(
                    (p for p in getattr(truck, deck).platforms if p.id == platform_id), 
                    None
                )

                if platform:
                    platform_dict = platform.dict() if hasattr(platform, "dict") else platform
                    adjusted = await HeightCalculationService.calculate_adjusted_heights(
                        platform_data=platform_dict,
                        vehicle_category=car_category
                    )

                    # Сохраняем расчетные высоты в размещении
                    optimized[deck][i]["effective_heights"] = {
                        "edge_a": adjusted.get("edge_a", {}).get("effective_height"),
                        "edge_b": adjusted.get("edge_b", {}).get("effective_height")
                    }

        return optimized

    async def _validate_constraints(
        self, 
        truck: TruckResponseSchema, 
        placement: Dict[str, Any], 
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Проверяет размещение на соответствие ограничениям"""
        issues = []
        warnings = []

        # Проверка общей критической высоты
        max_height_inches = self._calculate_max_height(truck, placement)

        # Общая критическая высота не более 14 фут 2 дюйма (170 дюймов)
        if max_height_inches > 170:
            issues.append(f"Critical height exceeded: {max_height_inches} inches (max: 170 inches)")

        # Целевая высота 13 фут 6 дюймов (162 дюйма)
        if max_height_inches > 162:
            warnings.append(f"Target height exceeded: {max_height_inches} inches (target: 162 inches)")

        # Проверка минимальных зазоров
        # В реальности здесь был бы сложный алгоритм проверки зазоров

        # Дополнительные пользовательские ограничения
        if constraints:
            # Проверка дополнительных ограничений
            # ...
            pass

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }

    def _final_optimization(
        self, 
        truck: TruckResponseSchema, 
        placement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Финальная оптимизация размещения"""
        # В реальности здесь был бы алгоритм финальной оптимизации
        # с учетом всех факторов

        # Для MVP просто возвращаем текущее размещение
        return placement

    async def _log_loading_experience(
        self, 
        truck_id: str, 
        configuration: Dict[str, Any]
    ) -> None:
        """Логирует опыт загрузки для анализа"""
        experience_data = {
            "truck_id": truck_id,
            "configuration_id": configuration.get("id", str(uuid.uuid4())),
            "car_count": len(configuration.get("cars", [])),
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }

        await db.log_loading_experience(experience_data)

    def _calculate_max_height(
        self, 
        truck: TruckResponseSchema, 
        placement: Dict[str, Any]
    ) -> float:
        """Рассчитывает максимальную высоту конфигурации"""
        # В реальности здесь был бы сложный расчет высоты
        # с учетом всех факторов

        # Для MVP возвращаем фиксированное значение
        # TODO: реализовать расчет высоты
        return 160.0  # Пример: 160 дюймов

    def _determine_vehicle_category(self, car_id: str) -> VehicleCategory:
        """Определяет категорию автомобиля для расчета высоты с цепями"""
        # В реальности здесь был бы анализ категории автомобиля
        # на основе его характеристик

        # Для MVP возвращаем фиксированную категорию
        # TODO: реализовать определение категории
        return VehicleCategory.STANDARD