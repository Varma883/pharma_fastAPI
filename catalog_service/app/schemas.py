from pydantic import BaseModel

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

    class Config:
        from_attributes = True   # replaces orm_mode=True
