import aioboto3
import boto3
import uuid
import json
import logging
from ..core.config import get_settings
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

settings = get_settings()
logger = logging.getLogger(__name__)

class DynamoDB:
    """Класс для работы с Amazon DynamoDB, заменяющий MongoDB."""

    session = None
    resource = None
    tables = {
        'vehicles': None,
        'loading_configurations': None,
        'loading_history': None
    }

    async def connect_to_database(self):
        """Инициализирует подключение к DynamoDB"""
        try:
            # Проверяем наличие учетных данных AWS
            if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
                logger.error("AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY не настроены!")
                return False

            logger.info(f"Попытка подключения к DynamoDB...")

            # Создаем асинхронную сессию для работы с AWS
            self.session = aioboto3.Session(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

            # Для некоторых операций может потребоваться синхронный клиент
            self.client = boto3.client(
                'dynamodb',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

            # Проверяем, существуют ли необходимые таблицы
            existing_tables = self.client.list_tables()['TableNames']

            # Проверяем и создаем таблицы при необходимости
            for table_name in self.tables.keys():
                if table_name not in existing_tables:
                    logger.warning(f"Таблица {table_name} не существует. Создаем...")
                    await self._create_table(table_name)
                else:
                    logger.info(f"Таблица {table_name} существует.")

            logger.info(f"Успешное подключение к DynamoDB")
            return True

        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {str(e)}")
            self.session = None
            self.client = None
            return False

    async def _create_table(self, table_name: str):
        """Создает таблицу в DynamoDB если она не существует"""
        try:
            if table_name == 'vehicles':
                response = self.client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'},
                        {'AttributeName': 'type', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'type-index',
                            'KeySchema': [
                                {'AttributeName': 'type', 'KeyType': 'HASH'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
            elif table_name == 'loading_configurations':
                response = self.client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
            elif table_name == 'loading_history':
                response = self.client.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'id', 'KeyType': 'HASH'},  # Partition key
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}  # Sort key
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'id', 'AttributeType': 'S'},
                        {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                        {'AttributeName': 'truck_id', 'AttributeType': 'S'}
                    ],
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'truck_id-timestamp-index',
                            'KeySchema': [
                                {'AttributeName': 'truck_id', 'KeyType': 'HASH'},
                                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                            ],
                            'Projection': {'ProjectionType': 'ALL'},
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )

            logger.info(f"Таблица {table_name} создана успешно")
            return True
        except Exception as e:
            logger.error(f"Ошибка создания таблицы {table_name}: {str(e)}")
            return False

    async def close_database_connection(self):
        """Закрывает соединение с базой данных"""
        # Для boto3/aioboto3 не требуется явное закрытие соединения
        logger.info("Соединение с DynamoDB закрыто")

    # -------------------- Вспомогательные методы --------------------

    def _serialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Сериализует объект Python в формат DynamoDB"""
        # Преобразование _id -> id для совместимости с MongoDB
        if '_id' in item and 'id' not in item:
            item['id'] = item.pop('_id')

        # Преобразование datetime -> ISO строка
        for key, value in item.items():
            if isinstance(value, datetime):
                item[key] = value.isoformat()
            elif isinstance(value, dict):
                item[key] = self._serialize_item(value)
            elif isinstance(value, list):
                item[key] = [
                    self._serialize_item(i) if isinstance(i, dict) else i 
                    for i in value
                ]

        return item

    def _deserialize_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Десериализует объект DynamoDB в формат Python"""
        # Преобразование id -> _id для совместимости с MongoDB
        if 'id' in item and '_id' not in item:
            item['_id'] = item.pop('id')

        # Попытка преобразования ISO строк -> datetime
        for key, value in item.items():
            if isinstance(value, str) and 'T' in value and value.endswith('Z'):
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass  # Не дата/время, оставляем как есть
            elif isinstance(value, dict):
                item[key] = self._deserialize_item(value)
            elif isinstance(value, list):
                item[key] = [
                    self._deserialize_item(i) if isinstance(i, dict) else i 
                    for i in value
                ]

        return item

    # -------------------- Методы для Vehicles (универсальные) --------------------

    async def create_vehicle(self, vehicle_data: Dict[str, Any]) -> str:
        """Создает новую запись транспортного средства"""
        try:
            # Создаем копию данных и добавляем ID если его нет
            data = vehicle_data.copy()
            vehicle_id = data.get('_id') or data.get('id') or str(uuid.uuid4())

            # Стандартизируем ID
            if '_id' in data:
                data['id'] = data.pop('_id')
            else:
                data['id'] = vehicle_id

            # Добавляем временные метки
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow().isoformat()

            # Сериализуем объект для DynamoDB
            dynamo_item = self._serialize_item(data)

            # Добавляем запись в таблицу
            async with self.session.resource('dynamodb') as resource:
                table = await resource.Table('vehicles')
                await table.put_item(Item=dynamo_item)

            return vehicle_id
        except Exception as e:
            logger.error(f"Ошибка создания vehicle: {str(e)}")
            raise e

    async def list_vehicles(self) -> List[Dict[str, Any]]:
        """Возвращает список всех транспортных средств"""
        try:
            async with self.session.resource('dynamodb') as resource:
                table = await resource.Table('vehicles')
                response = await table.scan()

                items = response.get('Items', [])
                # Десериализуем объекты из DynamoDB
                return [self._deserialize_item(item) for item in items]
        except Exception as e:
            logger.error(f"Ошибка получения списка vehicles: {str(e)}")
            return []

    async def get_vehicle(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Получает транспортное средство по ID"""
        try:
            async with self.session.resource('dynamodb') as resource:
                table = await resource.Table('vehicles')
                response = await table.get_item(Key={'id': vehicle_id})

                if 'Item' not in response:
                    return None

                # Десериализуем объект из DynamoDB
                return self._deserialize_item(response['Item'])
        except Exception as e:
            logger.error(f"Ошибка получения vehicle {vehicle_id}: {str(e)}")
            return None

    async def update_vehicle(self, vehicle_id: str, update_data: Dict[str, Any]) -> bool:
        """Обновляет данные транспортного средства"""
        try:
            # Добавляем метку времени обновления
            data = update_data.copy()
            data["updated_at"] = datetime.utcnow().isoformat()

            # Формируем выражение обновления
            update_expression = "SET "
            expression_attribute_values = {}
            expression_attribute_names = {}

            for i, (key, value) in enumerate(data.items()):
                placeholder = f":val{i}"
                name_placeholder = f"#name{i}"
                update_expression += f"{name_placeholder} = {placeholder}, "
                expression_attribute_values[placeholder] = value
                expression_attribute_names[name_placeholder] = key

            # Удаляем последнюю запятую и пробел
            update_expression = update_expression[:-2]

            async with self.session.resource('dynamodb') as resource:
                table = await resource.Table('vehicles')
                response = await table.update_item(
                    Key={'id': vehicle_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values,
                    ExpressionAttributeNames=expression_attribute_names,
                    ReturnValues="UPDATED_NEW"
                )

            return 'Attributes' in response
        except Exception as e:
            logger.error(f"Ошибка обновления vehicle {vehicle_id}: {str(e)}")
            return False

    async def delete_vehicle(self, vehicle_id: str) -> bool:
        """Удаляет транспортное средство"""
        try:
            async with self.session.resource('dynamodb') as resource:
                table = await resource.Table('vehicles')
                response = await table.delete_item(Key={'id': vehicle_id})

            return response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200
        except Exception as e:
            logger.error(f"Ошибка удаления vehicle {vehicle_id}: {str(e)}")
            return False

    # -------------------- Методы для работы с Loading Configuration --------------------

    async def save_configuration(self, config_data: Dict[str, Any]) -> str:
        """Сохраняет конфигурацию загрузки"""
        try:
            # Создаем копию данных и добавляем ID если его нет
            data = config_data.copy()
            config_id = data.get('_id') or data.get('id') or str(uuid.uuid4())

            # Стандартизируем ID
            if '_id' in data:
                data['id'] = data.pop('_id')
            else:
                data['id'] = config_id

            # Добавляем временные метки
            if 'created_at' not in data:
                data['created_at'] = datetime.utcnow().isoformat()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.utcnow().isoformat()

            # Сериализуем объект для DynamoDB
            dynamo_item = self._serialize_item(data)

            async with self.session.resource('dynamodb') as resource:
                table = await resource.Table('loading_configurations')
                await table.put_item(Item=dynamo_item)

            return config_id
        except Exception as e:
            logger.error(f"Ошибка сохранения configuration: {str(e)}")
            raise e

    async def get_configuration(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Получает сохраненную конфигурацию"""
        try:
            async with self.session.resource('dynamodb') as resource:
                table = await resource.Table('loading_configurations')
                response = await table.get_item(Key={'id': config_id})

                if 'Item' not in response:
                    return None

                # Десериализуем объект из DynamoDB
                return self._deserialize_item(response['Item'])
        except Exception as e:
            logger.error(f"Ошибка получения configuration {config_id}: {str(e)}")
            return None

    # -------------------- Методы для работы с Loading History --------------------

    async def log_loading_experience(self, experience_data: Dict[str, Any]) -> str:
        """Логирует опыт загрузки"""
        try:
            # Создаем копию данных и добавляем ID если его нет
            data = experience_data.copy()
            exp_id = data.get('_id') or data.get('id') or str(uuid.uuid4())

            # Стандартизируем ID
            if '_id' in data:
                data['id'] = data.pop('_id')
            else:
                data['id'] = exp_id

            # Добавляем временную метку
            data['timestamp'] = data.get('timestamp') or datetime.utcnow().isoformat()

            # Сериализуем объект для DynamoDB
            dynamo_item = self._serialize_item(data)

            async with self.session.resource('dynamodb') as resource:
                table = await resource.Table('loading_history')
                await table.put_item(Item=dynamo_item)

            return exp_id
        except Exception as e:
            logger.error(f"Ошибка логирования loading experience: {str(e)}")
            raise e

    async def get_loading_history(self, truck_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Получает историю загрузок для грузовика"""
        try:
            async with self.session.resource('dynamodb') as resource:
                table = await resource.Table('loading_history')

                response = await table.query(
                    IndexName='truck_id-timestamp-index',
                    KeyConditionExpression="truck_id = :tid",
                    ExpressionAttributeValues={
                        ":tid": truck_id
                    },
                    ScanIndexForward=False,  # Сортировка по убыванию (новые записи первыми)
                    Limit=limit
                )

                items = response.get('Items', [])
                # Десериализуем объекты из DynamoDB
                return [self._deserialize_item(item) for item in items]
        except Exception as e:
            logger.error(f"Ошибка получения loading history для {truck_id}: {str(e)}")
            return []

# Инициализация синглтона
db = DynamoDB()