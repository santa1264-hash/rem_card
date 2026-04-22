from pydantic import BaseModel
from typing import Optional

class Bed(BaseModel):
    bed_number: int
    status: str  # 'FREE' or 'OCCUPIED'
    current_admission_id: Optional[int] = None