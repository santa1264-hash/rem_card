from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Operation(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    admission_id: int
    operation_number: int
    description: str
    operation_datetime: datetime
