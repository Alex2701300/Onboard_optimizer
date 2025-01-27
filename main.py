
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.db.mongodb import db
from app.api.endpoints.vehicles import router as vehicles_router

app = FastAPI(title="CarLogix Loading Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем статические файлы (если нужно)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    # Подключение к MongoDB
    await db.connect_to_database()

@app.on_event("shutdown")
async def shutdown_event():
    # Отключение от MongoDB
    await db.close_database_connection()

@app.get("/", response_class=HTMLResponse)
async def root():
    # Отдаём index.html
    with open("app/static/test_interface/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

# Подключаем универсальный роутер /api/vehicles
app.include_router(vehicles_router, prefix="/api", tags=["Vehicles"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
