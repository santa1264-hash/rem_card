from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

class Admission(BaseModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int
    bed_number: int
    history_number: str
    admission_datetime: datetime
    patient_age: Optional[int] = None
    patient_months: Optional[int] = None
    patient_age_unit: Optional[str] = None
    patient_gender: Optional[str] = None # Мужской, Женский
    diagnosis_code: Optional[str] = None
    diagnosis_text: Optional[str] = None
    department_profile: Optional[str] = None
    source_department: Optional[str] = None
    transfer_datetime: Optional[datetime] = None
    transfer_department: Optional[str] = None
    outcome: Optional[str] = None
    transfer_lpu: Optional[str] = None
    transfer_lpu_other: Optional[str] = None
    death_datetime: Optional[datetime] = None
    clinical_death_datetime: Optional[datetime] = None
    cardiac_arrest_cause: Optional[str] = None
    cardiac_arrest_measures_json: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
