
from functools import lru_cache
from typing import Dict
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    def __init__(self):
        self.APP_NAME = "AI-Loading Optimizer"
        self.DEBUG = False
        self.MONGODB_URL = os.getenv('MONGODB_URL')
        self.MONGODB_DB_NAME = "Carlogix_loading"

@lru_cache()
def get_settings():
    return Settings()
