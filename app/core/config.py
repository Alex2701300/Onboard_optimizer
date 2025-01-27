
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "AI-Loading Optimizer"
    DEBUG: bool = False
    MONGODB_URL: str
    MONGODB_DB_NAME: str = "Carlogix_loading"

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

@lru_cache()
def get_settings():
    return Settings()
