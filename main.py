# main.py

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from bson.objectid import ObjectId
from json import JSONEncoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

# Импорт вашего синглтона для MongoDB
from app.db.mongodb import db

# Предположим, ваш основной роутер описан здесь:
from app.api.endpoints.vehicles import router as vehicles_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Новый подход Lifespan Events вместо @app.on_event("startup"/"shutdown").
    """
    # Это будет выполняться при запуске приложения:
    await db.connect_to_database()

    yield  # <-- точка, где приложение «работает»

    # Это будет выполняться при остановке приложения:
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
    default_response_class=HTMLResponse,
    json_encoder=CustomJSONEncoder
)

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


# Подключаем роутер /api/vehicles (или другие)
app.include_router(vehicles_router, prefix="/api", tags=["Vehicles"])


if __name__ == "__main__":
    import uvicorn
    # Важно: если хотите reload/workers, задайте строку "module:app"
    # Здесь для простоты вызываем напрямую, предупреждение можно игнорировать
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)