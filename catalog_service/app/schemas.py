from pydantic import BaseModel
from datetime import datetime


class DrugBase(BaseModel):
    name: str
    manufacturer: str
    ndc: str
    form: str | None = None
    strength: str | None = None


class DrugCreate(DrugBase):
    pass


class DrugResponse(DrugBase):
    id: int
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True   # replaces orm_mode=True
