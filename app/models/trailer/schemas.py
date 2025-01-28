from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class TrailerCreateSchema(BaseModel):
    nickname: str
    year: int
    capacity_in: float


class TrailerResponseSchema(BaseModel):
    id: str = Field(..., alias="_id")  # "_id" -> "id"
    nickname: str
    year: int
    capacity_in: float

    type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True