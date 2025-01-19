from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class BaseDBModel(BaseModel):
    id: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)