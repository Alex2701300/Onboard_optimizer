# app/models/trailer/schemas.py

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class TrailerBaseSchema(BaseModel):
    """
    Базовые поля для трейлера. 
    Можно расширять при необходимости (габариты, сцепки и т.д.).
    """
    nickname: str = Field(..., min_length=2, description="Имя трейлера (внутреннее)")
    year: int = Field(..., ge=1900, le=9999)
    capacity_in: float = Field(..., gt=0, description="Вместимость/длина в дюймах?")

class TrailerCreateSchema(TrailerBaseSchema):
    """
    Поля для создания трейлера.
    """
    pass

class TrailerResponseSchema(TrailerBaseSchema):
    """
    Ответ при чтении/обновлении. Добавляем служебные поля.
    """
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True