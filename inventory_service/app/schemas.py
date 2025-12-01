from pydantic import BaseModel

class InventoryItem(BaseModel):
    product_id: int
    quantity: int

class ReserveRequest(BaseModel):
    items: list[InventoryItem]
