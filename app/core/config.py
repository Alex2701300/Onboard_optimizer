from functools import lru_cache
from typing import Dict
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    def __init__(self):
        self.APP_NAME = "AI-Loading Optimizer"
        self.DEBUG = False

        # MongoDB settings (для обратной совместимости)
        self.MONGODB_URL = os.getenv('MONGODB_URL')
        self.MONGODB_DB_NAME = "Carlogix_loading"

        # AWS settings
        self.AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
        self.AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

@lru_cache()
def get_settings():
    return Settings()