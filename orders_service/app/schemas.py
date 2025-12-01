from pydantic import BaseModel
from typing import List

class OrderItem(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItem]

class Order(BaseModel):
    id: int
    username: str
    status: str
    items: list

    class Config:
        orm_mode = True
