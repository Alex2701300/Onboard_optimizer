# main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from bson import ObjectId
from json import JSONEncoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

# Импорт вашего синглтона для MongoDB
from app.db.mongodb import db

# Импортируем роутеры
from app.api.endpoints.cars import router as cars_router
from app.api.endpoints.trucks import router as trucks_router
from app.api.endpoints.trailers import router as trailers_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Новый подход Lifespan Events вместо @app.on_event("startup"/"shutdown").
    """
    # Это будет выполняться при запуске приложения:
    connected = await db.connect_to_database()
    if not connected:
        logger.error("Failed to connect to MongoDB. Application might not work properly.")

    yield  # <-- точка, где приложение «работает»

    # Это будет выполняться при остановке приложения:
    if connected:
        await db.close_database_connection()


# Custom JSON encoder for ObjectId
class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)


# Инициализируем FastAPI, указывая lifespan:
app = FastAPI(
    title="CarLogix Loading Optimizer",
    lifespan=lifespan,
    default_response_class=HTMLResponse,  # По умолчанию HTMLResponse
    json_encoder=CustomJSONEncoder
)

@app.middleware("http")
async def log_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(f"ERROR TYPE: {type(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        raise e

# Разрешаем CORS:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы (если нужно отдавать CSS, JS, картинки):
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Отдаём ваш React-интерфейс (index.html) при запросе на корень "/".
    """
    with open("app/static/test_interface/index.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


# Подключаем роутеры
# Cars → /api/cars
app.include_router(cars_router, prefix="/api", tags=["Cars"])
# Trucks → /api/trucks
app.include_router(trucks_router, prefix="/api", tags=["Trucks"])
# Trailers → /api/trailers
app.include_router(trailers_router, prefix="/api", tags=["Trailers"])


if __name__ == "__main__":
    import uvicorn
    # Если нужен reload, можно указать uvicorn.run("main:app", reload=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)