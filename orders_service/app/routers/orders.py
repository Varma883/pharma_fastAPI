from fastapi import APIRouter, Depends, HTTPException
from shared.auth_utils import verify_jwt
from app.schemas import OrderCreate, Order
import itertools

router = APIRouter()

# AUTO INCREMENT ORDER IDs
order_counter = itertools.count(1)

# In-memory store (replace with DB later)
ORDERS_DB = []

# Simulated inventory check (no external service required)
def mock_inventory(items):
    # For now just pretend inventory is always available
    return True


@router.post("/", response_model=Order)
def create_order(
    payload: OrderCreate,
    user=Depends(verify_jwt)
):
    # Step 1 — Check inventory
    ok = mock_inventory(payload.items)
    if not ok:
        raise HTTPException(status_code=400, detail="Inventory reservation failed")

    # Step 2 — Create order
    order_id = next(order_counter)

    order_record = {
        "order_id": order_id,
        "status": "CONFIRMED",
        "items": [item.model_dump() for item in payload.items],
    }

    ORDERS_DB.append(order_record)

    return order_record


@router.get("/", response_model=list[Order])
def list_orders(user=Depends(verify_jwt)):
    return ORDERS_DB
