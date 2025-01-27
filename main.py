
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.db.mongodb import db
from app.api.endpoints.vehicles import router as vehicles_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CarLogix Loading Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup_event():
    try:
        await db.connect_to_database()
        logger.info("Successfully connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    try:
        await db.close_database_connection()
        logger.info("Successfully closed database connection")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")

@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        with open("app/static/test_interface/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        logger.error("index.html not found")
        return HTMLResponse("Error: interface file not found", status_code=500)
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return HTMLResponse("Internal server error", status_code=500)

# Подключаем роутер vehicles
app.include_router(vehicles_router, prefix="/api", tags=["Vehicles"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
