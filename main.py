from fastapi import FastAPI
from app.core.config import get_settings

app = FastAPI(title="CarLogix Loading Optimizer")

@app.get("/")
async def root():
    return {"message": "CarLogix Loading Optimizer API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)