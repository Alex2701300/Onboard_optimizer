from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Dict

class Settings(BaseSettings):
    APP_NAME: str = "AI-Loading Optimizer"
    DEBUG: bool = False

    # MongoDB settings
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "Carlogix_loading"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

@lru_cache()
def get_settings():
    return Settings()