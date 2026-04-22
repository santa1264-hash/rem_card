from pydantic import BaseModel, Field
from typing import Optional

class Patient(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    admission_uid: Optional[str] = Field(default=None)
