import logging
import time
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_request_middleware(request: Request, call_next):
    """
    Middleware для детального логирования HTTP запросов и ответов.
    Поможет выявить проблемы с маршрутизацией и перенаправлениями.
    """
    start_time = time.time()

    # Логируем информацию о запросе
    logger.info(f"Request start: {request.method} {request.url.path}")
    logger.info(f"Query params: {request.query_params}")

    try:
        # Читаем тело запроса, если есть
        body = await request.body()
        if body:
            body_str = body.decode()
            if len(body_str) > 500:
                body_str = body_str[:500] + "... [truncated]"
            logger.info(f"Request body: {body_str}")
    except Exception as e:
        logger.error(f"Error reading request body: {str(e)}")

    # Вызываем следующий middleware или обработчик
    try:
        response = await call_next(request)

        # Логируем информацию о ответе
        process_time = time.time() - start_time
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Process time: {process_time:.3f} seconds")

        # Для ошибочных статусов добавляем больше информации
        if response.status_code >= 400:
            logger.warning(f"Error response: {response.status_code} for {request.method} {request.url.path}")

        # Для перенаправлений логируем заголовок Location
        if 300 <= response.status_code < 400:
            location = response.headers.get("location")
            logger.info(f"Redirect to: {location}")

        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise