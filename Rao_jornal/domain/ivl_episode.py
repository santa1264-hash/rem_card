from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class IVLEpisode(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    admission_id: int
    episode_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    type: str # delivery or transfer