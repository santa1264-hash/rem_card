from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Transfusion(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    admission_id: int
    type: str # blood or plasma
    volume_ml: int
    datetime: datetime