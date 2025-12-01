from pydantic import BaseModel
from typing import Optional

class UserRegister(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    role: Optional[str] = "user"
