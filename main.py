import uvicorn
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.middleware import log_request_middleware

from bson import ObjectId
from json import JSONEncoder

# Подключение к БД (синглтон)
from app.db.dynamodb import db

# Импорт ваших роутеров
# Обратите внимание: в files:
#   cars.py -> APIRouter(prefix="/cars")
#   trucks.py -> APIRouter(prefix="/trucks")
#   trailers.py -> APIRouter(prefix="/trailers")
#
# Здесь мы подключим их все через prefix="/api" —
# таким образом итоговые адреса будут:
#   GET /api/cars/
#   GET /api/trucks/
#   GET /api/trailers/
from app.api.endpoints.cars import router as cars_router
from app.api.endpoints.trucks import router as trucks_router
from app.api.endpoints.trailers import router as trailers_router

logger = logging.getLogger(__name__)


class CustomJSONEncoder(JSONEncoder):
    """При необходимости сериализовать ObjectId -> str."""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle приложения:
    подключаемся к DynamoDB при старте, закрываем при остановке.
    """
    try:
        connected = await db.connect_to_database()
        if not connected:
            raise Exception("Failed to connect to DynamoDB")
        logger.info("DynamoDB connected.")
        yield
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        raise
    finally:
        try:
            await db.close_database_connection()
            logger.info("DynamoDB disconnected.")
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")


app = FastAPI(
    title="CarLogix Loading Optimizer",
    lifespan=lifespan,
    # При желании можно указать:
    #   default_response_class=HTMLResponse,
    #   json_encoder=CustomJSONEncoder
)

# Разрешаем CORS:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Подключаем статику (чтобы раздавать index.html, JS, CSS и т.д.):
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# Упрощённый middleware без try/except,
# чтобы избежать внутренних конфликтов Starlette/AnyIO:
@app.middleware("http")
async def middleware(request: Request, call_next):
    return await log_request_middleware(request, call_next)

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Возвращаем ваш test_interface/index.html при GET /
    """
    with open("app/static/test_interface/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


# Подключаем роутеры:
# В самих routers у вас prefix="/cars" / "/trucks" / "/trailers"
# Здесь задаём общий prefix="/api", итого в итоге получим:
#   /api/cars
#   /api/trucks
#   /api/trailers
app.include_router(cars_router,     prefix="/api", tags=["cars"])
app.include_router(trucks_router,   prefix="/api", tags=["trucks"])
app.include_router(trailers_router, prefix="/api", tags=["trailers"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        workers=1
    )