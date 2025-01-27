    import pytest

    from app.models.truck.schemas import (
        TruckCreateSchema,
        ChainConfiguration,
        PlatformHeightAdjustment,
        VehicleCategory
    )
    from app.models.truck.crud import truck_crud

    @pytest.mark.asyncio
    async def test_truck_lifecycle():
        """
        Проверяем полный цикл CRUD для грузовика:
          1. Создание (create_truck)
          2. Чтение (get_truck)
          3. Обновление (update_truck_configuration)
          4. Удаление (delete_truck)
        """
        test_truck = TruckCreateSchema(
            nickname="Test Truck",
            year=2023,
            model="Test Model",
            truck_type="semi",
            coupling_type="5th_wheel",
            gvwr=80000.0
        )

        # Создание
        created_truck = await truck_crud.create_truck(test_truck)
        assert created_truck.id is not None, "Truck creation failed: no ID returned"

        # Чтение
        fetched_truck = await truck_crud.get_truck(created_truck.id)
        assert fetched_truck is not None, "Truck not found after creation"
        assert fetched_truck.nickname == "Test Truck", "Nickname mismatch after fetch"

        # Обновление
        updated_data = {"nickname": "Updated Name"}
        updated_truck = await truck_crud.update_truck_configuration(created_truck.id, updated_data)
        assert updated_truck is not None, "Update returned None"
        assert updated_truck.nickname == "Updated Name", "Nickname not updated"

        # Удаление
        delete_result = await truck_crud.delete_truck(created_truck.id)
        assert delete_result is True, "Truck deletion failed"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "base_height,is_used,categories,vehicle_cat,expected",
        [
            # Цепи включены, электромобиль → высота не меняется
            (100.0, True, [VehicleCategory.ELECTRIC], VehicleCategory.ELECTRIC, 100.0),

            # Цепи включены, пикап → минус 4 дюйма
            (100.0, True, [VehicleCategory.PICKUP], VehicleCategory.PICKUP, 96.0),

            # Цепи включены, полноразмерный SUV → минус 4 дюйма
            (100.0, True, [VehicleCategory.FULL_SIZE_SUV], VehicleCategory.FULL_SIZE_SUV, 96.0),

            # Цепи включены, стандарт → минус 2 дюйма
            (100.0, True, [VehicleCategory.STANDARD], VehicleCategory.STANDARD, 98.0),

            # Цепи выключены → высота без изменений
            (100.0, False, [], VehicleCategory.STANDARD, 100.0),
        ]
    )
    async def test_chain_height_calculation(base_height, is_used, categories, vehicle_cat, expected):
        """
        Проверяем логику снижения высоты при использовании цепей:
          - STANDARD: -2 дюйма
          - PICKUP / FULL_SIZE_SUV: -4 дюйма
          - ELECTRIC: без снижения
          - Если is_used=False, высота не меняется
        """
        chains = ChainConfiguration(is_used=is_used, vehicle_categories=categories)
        result = PlatformHeightAdjustment.calculate_effective_height(base_height, chains, vehicle_cat)
        assert abs(result - expected) < 1e-6, f"Calculated={result}, Expected={expected}"