# app/services/height_calculator.py

from typing import Dict, Any
from app.models.enums import VehicleCategory
from app.models.truck.schemas import PlatformHeightAdjustment, ChainConfiguration

class HeightCalculationService:
    @staticmethod
    async def calculate_adjusted_heights(
        platform_data: Dict[str, Any],
        vehicle_category: VehicleCategory
    ) -> Dict[str, Any]:
        """
        Рассчитывает итоговые (effective) высоты краёв платформы
        с учётом использования цепей. Возвращает копию данных 
        платформы с полем edge_a['effective_height'] и edge_b['effective_height'].
        """
        adjusted_data = dict(platform_data)  # скопируем начальные данные

        for edge_key in ['edge_a', 'edge_b']:
            if edge_key in adjusted_data:
                base_height = adjusted_data[edge_key].get('height')
                chains_cfg = adjusted_data[edge_key].get('chains')

                # Если высота не задана, игнорируем (возможно, mobile edge)
                if base_height is not None and chains_cfg:
                    # Вызываем расчет
                    new_height = PlatformHeightAdjustment.calculate_effective_height(
                        base_height=base_height,
                        chains_config=ChainConfiguration(**chains_cfg),
                        vehicle_category=vehicle_category
                    )
                    adjusted_data[edge_key]['effective_height'] = new_height

        return adjusted_data